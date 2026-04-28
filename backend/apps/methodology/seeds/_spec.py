"""
Ferzion Discovery — Methodology / Seeds / Spec.

Dataclasses declarativas para descrever perguntas no seed.
Conteúdo é dado puro — sem dependência de Django.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from apps.methodology.models import (
    Arquetipo,
    FaixaDevolutiva,
    PerfilProfundidade,
    SlugAto,
    TipoPergunta,
)


@dataclass(frozen=True)
class OpcaoSpec:
    """Opção de uma pergunta de escolha."""

    codigo_interno: str
    texto_publico: str
    descricao_publica: str = ""
    icone: str = ""


@dataclass(frozen=True)
class MapeamentoSpec:
    """
    Mapeamento de uma resposta para um sinal.

    `opcao_codigo`:
        - Para perguntas de escolha: código interno da opção (chave da
          `condicao` de matching).
        - Para Reveladoras / texto livre: usar string especial "__sempre__"
          que vira `condicao={"operador": "always"}` no banco.
    """

    sinal_chave: str
    opcao_codigo: str
    valor_extraido: Any
    peso: float = 1.0
    notas: str = ""


@dataclass(frozen=True)
class PerguntaSpec:
    """
    Especificação declarativa de uma pergunta.

    Contém tudo necessário para o loader criar/atualizar:
        - Pergunta
        - OpcaoDePergunta (todas)
        - MapeamentoDeSinal (todos)
        - FraseDevolutiva (até 3 — baixo/médio/alto)

    Idempotente por (ato_slug, codigo).
    """

    # --- Identidade ---
    ato_slug: SlugAto
    codigo: str
    ordem: int

    # --- Metodológica ---
    arquetipo: Arquetipo
    tipo: TipoPergunta

    # --- Conteúdo público ---
    texto_publico: str
    objetivo_interno: str

    # --- Configuração ---
    obrigatoria: bool = True
    perfis_minimos: list[PerfilProfundidade] = field(default_factory=list)
    placeholder: str = ""
    helper_text: str = ""
    tipo_config: dict[str, Any] = field(default_factory=dict)
    precondicoes: dict[str, Any] = field(default_factory=dict)

    # --- Estrutura ---
    opcoes: list[OpcaoSpec] = field(default_factory=list)
    mapeamentos: list[MapeamentoSpec] = field(default_factory=list)
    devolutivas: dict[FaixaDevolutiva, str] = field(default_factory=dict)

    def perfis_minimos_str(self) -> list[str]:
        """Converte enums para lista de strings (formato persistido em JSON)."""
        return [p.value for p in self.perfis_minimos]
