"""
Ferzion Discovery — Methodology / Seeds / Loader.

Lógica idempotente para carregar PerguntaSpec → banco.

Garantias:
    - Idempotente por (ato, codigo).
    - Não destrói dados — apenas cria ou atualiza.
    - Não toca em versões imutáveis (published/archived).
    - Atomic por pergunta (transação parcial não corrompe banco).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from django.db import transaction

from apps.methodology.models import (
    Ato,
    CatalogoSinal,
    FraseDevolutiva,
    MapeamentoDeSinal,
    OpcaoDePergunta,
    Pergunta,
    RoteiroVersao,
    SlugAto,
)

from ._spec import MapeamentoSpec, OpcaoSpec, PerguntaSpec

logger = logging.getLogger(__name__)


# Chave especial para mapeamentos de Reveladoras (texto livre)
SEMPRE = "__sempre__"


@dataclass
class LoadResult:
    """Resultado consolidado do carregamento de um ato."""

    ato_slug: str
    perguntas_criadas: int = 0
    perguntas_atualizadas: int = 0
    perguntas_ignoradas: int = 0  # versão imutável
    opcoes_criadas: int = 0
    opcoes_atualizadas: int = 0
    mapeamentos_criados: int = 0
    mapeamentos_atualizados: int = 0
    frases_criadas: int = 0
    frases_atualizadas: int = 0

    def __str__(self) -> str:
        return (
            f"[{self.ato_slug}] "
            f"perguntas: +{self.perguntas_criadas} ~{self.perguntas_atualizadas} "
            f"·{self.perguntas_ignoradas} | "
            f"opções: +{self.opcoes_criadas} ~{self.opcoes_atualizadas} | "
            f"mapeamentos: +{self.mapeamentos_criados} ~{self.mapeamentos_atualizados} | "
            f"frases: +{self.frases_criadas} ~{self.frases_atualizadas}"
        )


def load_perguntas_para_ato(
    versao: RoteiroVersao,
    ato_slug: SlugAto,
    specs: list[PerguntaSpec],
) -> LoadResult:
    """
    Carrega lista de PerguntaSpec em um ato específico de uma versão.

    Idempotente: rodar duas vezes não duplica.
    Seguro: ignora silenciosamente se versão imutável.

    Args:
        versao: RoteiroVersao alvo (deve estar em DRAFT).
        ato_slug: slug do ato alvo (deve existir na versão).
        specs: lista de PerguntaSpec a carregar.

    Returns:
        LoadResult com contagens.

    Raises:
        Ato.DoesNotExist: se o ato não existe na versão.
    """
    result = LoadResult(ato_slug=str(ato_slug))

    if versao.is_immutable:
        logger.warning(
            "Versão %s está imutável — pulando carga de %s perguntas no ato %s",
            versao,
            len(specs),
            ato_slug,
        )
        result.perguntas_ignoradas = len(specs)
        return result

    ato = Ato.objects.get(versao=versao, slug=ato_slug)

    # Cache de sinais — evita N+1 nas queries
    chaves_referenciadas = {m.sinal_chave for spec in specs for m in spec.mapeamentos}
    sinais_por_chave: dict[str, CatalogoSinal] = {
        s.chave: s for s in CatalogoSinal.objects.filter(chave__in=chaves_referenciadas)
    }

    # Validação prévia: todos os sinais referenciados existem
    chaves_faltando = chaves_referenciadas - set(sinais_por_chave)
    if chaves_faltando:
        raise ValueError(
            f"Sinais referenciados não existem no catálogo: "
            f"{sorted(chaves_faltando)}. "
            f"Adicione ao seed_methodology antes de carregar."
        )

    for spec in specs:
        _load_pergunta(ato, spec, sinais_por_chave, result)

    return result


@transaction.atomic
def _load_pergunta(
    ato: Ato,
    spec: PerguntaSpec,
    sinais_por_chave: dict[str, CatalogoSinal],
    result: LoadResult,
) -> None:
    """Carrega uma pergunta individualmente (atomic)."""
    pergunta, criada = Pergunta.objects.get_or_create(
        ato=ato,
        codigo=spec.codigo,
        defaults=_pergunta_defaults(spec),
    )

    if criada:
        result.perguntas_criadas += 1
    else:
        if _atualizar_pergunta_se_necessario(pergunta, spec):
            result.perguntas_atualizadas += 1

    # Subentidades em ordem fixa
    _sync_opcoes(pergunta, spec.opcoes, result)
    _sync_mapeamentos(pergunta, spec.mapeamentos, sinais_por_chave, result)
    _sync_frases(pergunta, spec.devolutivas, result)


def _pergunta_defaults(spec: PerguntaSpec) -> dict:
    return {
        "ordem": spec.ordem,
        "tipo": spec.tipo,
        "arquetipo": spec.arquetipo,
        "texto_publico": spec.texto_publico,
        "objetivo_interno": spec.objetivo_interno,
        "obrigatoria": spec.obrigatoria,
        "perfis_minimos": spec.perfis_minimos_str(),
        "placeholder": spec.placeholder,
        "helper_text": spec.helper_text,
        "tipo_config": spec.tipo_config,
        "precondicoes": spec.precondicoes,
    }


def _atualizar_pergunta_se_necessario(pergunta: Pergunta, spec: PerguntaSpec) -> bool:
    """Atualiza campos editáveis. Retorna True se algo mudou."""
    novos = _pergunta_defaults(spec)
    mudou = False
    for campo, valor in novos.items():
        if getattr(pergunta, campo) != valor:
            setattr(pergunta, campo, valor)
            mudou = True
    if mudou:
        pergunta.save()
    return mudou


def _sync_opcoes(
    pergunta: Pergunta,
    opcoes: list[OpcaoSpec],
    result: LoadResult,
) -> None:
    """Sincroniza opções. Cria/atualiza por codigo_interno. Não remove."""
    for ordem, opcao_spec in enumerate(opcoes):
        opcao, criada = OpcaoDePergunta.objects.get_or_create(
            pergunta=pergunta,
            codigo_interno=opcao_spec.codigo_interno,
            defaults={
                "ordem": ordem,
                "texto_publico": opcao_spec.texto_publico,
                "descricao_publica": opcao_spec.descricao_publica,
                "icone": opcao_spec.icone,
            },
        )
        if criada:
            result.opcoes_criadas += 1
            continue

        # Atualiza se mudou
        mudou = False
        if opcao.ordem != ordem:
            opcao.ordem = ordem
            mudou = True
        if opcao.texto_publico != opcao_spec.texto_publico:
            opcao.texto_publico = opcao_spec.texto_publico
            mudou = True
        if opcao.descricao_publica != opcao_spec.descricao_publica:
            opcao.descricao_publica = opcao_spec.descricao_publica
            mudou = True
        if opcao.icone != opcao_spec.icone:
            opcao.icone = opcao_spec.icone
            mudou = True
        if mudou:
            opcao.save()
            result.opcoes_atualizadas += 1


def _sync_mapeamentos(
    pergunta: Pergunta,
    mapeamentos: list[MapeamentoSpec],
    sinais_por_chave: dict[str, CatalogoSinal],
    result: LoadResult,
) -> None:
    """
    Sincroniza mapeamentos. Chave de unicidade: (pergunta, sinal, valor_extraido).
    Cria/atualiza. Não remove.
    """
    for m_spec in mapeamentos:
        sinal = sinais_por_chave[m_spec.sinal_chave]
        condicao = _construir_condicao(m_spec.opcao_codigo)

        mapeamento, criado = MapeamentoDeSinal.objects.get_or_create(
            pergunta=pergunta,
            sinal=sinal,
            valor_extraido=m_spec.valor_extraido,
            defaults={
                "condicao": condicao,
                "peso": m_spec.peso,
                "notas": m_spec.notas,
            },
        )
        if criado:
            result.mapeamentos_criados += 1
            continue

        # Atualiza condicao/peso/notas se mudou
        mudou = False
        if mapeamento.condicao != condicao:
            mapeamento.condicao = condicao
            mudou = True
        if mapeamento.peso != m_spec.peso:
            mapeamento.peso = m_spec.peso
            mudou = True
        if mapeamento.notas != m_spec.notas:
            mapeamento.notas = m_spec.notas
            mudou = True
        if mudou:
            mapeamento.save()
            result.mapeamentos_atualizados += 1


def _construir_condicao(opcao_codigo: str) -> dict:
    """
    Traduz `opcao_codigo` da spec para o JSON `condicao` do banco.

    Convenção:
        - "__sempre__" → {"operador": "always"} (Reveladoras)
        - qualquer outro → {"operador": "equals", "opcao_codigo": "..."}
    """
    if opcao_codigo == SEMPRE:
        return {"operador": "always"}
    return {"operador": "equals", "opcao_codigo": opcao_codigo}


def _sync_frases(
    pergunta: Pergunta,
    devolutivas: dict,
    result: LoadResult,
) -> None:
    """Sincroniza frases de devolutiva (uma por faixa)."""
    for faixa, texto in devolutivas.items():
        frase, criada = FraseDevolutiva.objects.get_or_create(
            pergunta=pergunta,
            faixa=faixa,
            defaults={"texto": texto},
        )
        if criada:
            result.frases_criadas += 1
        elif frase.texto != texto:
            frase.texto = texto
            frase.save()
            result.frases_atualizadas += 1
