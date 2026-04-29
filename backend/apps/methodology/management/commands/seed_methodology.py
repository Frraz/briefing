"""
Ferzion Discovery — Methodology / Comando de seed.

Popula a base com a estrutura inicial do Roteiro Universal Ferzion:
    - 1 RoteiroIdentidade ("Roteiro Universal Ferzion")
    - 1 RoteiroVersao v1 em DRAFT
    - 8 atos canônicos (Acolhimento → Ponte) com títulos prontos
    - Catálogo base de 22 sinais cobrindo as 7 categorias
    - Perguntas declarativas dos atos (a partir de seeds/ato_*.py)

Uso:
    docker compose exec backend uv run python manage.py seed_methodology
    docker compose exec backend uv run python manage.py seed_methodology --force

Comportamento:
    Sem --force (idempotente):
        - Cria identidade se não existir.
        - Cria atos faltantes na versão em draft.
        - Cria sinais faltantes no catálogo.
        - Cria/atualiza perguntas, opções, mapeamentos, frases.

    Com --force (destrutivo):
        - Apaga TODA a metodologia atual.
        - Recria do zero.
"""

from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.methodology.models import (
    Ato,
    CatalogoSinal,
    CategoriaSinal,
    RoteiroIdentidade,
    RoteiroVersao,
    SlugAto,
    StatusVersao,
    TipoRoteiro,
    TipoValorSinal,
)
from apps.methodology.seeds import ato_1_calibracao
from apps.methodology.seeds._loader import LoadResult, load_perguntas_para_ato

# =============================================================================
#  Atos canônicos
# =============================================================================

ATOS_CANONICOS: list[dict[str, Any]] = [
    {
        "slug": SlugAto.ACOLHIMENTO,
        "ordem": 0,
        "titulo_publico": "Antes de qualquer projeto, vamos conversar.",
        "subtitulo_publico": (
            "A Ferzion não começa um sistema escrevendo código. Começamos entendendo seu negócio."
        ),
        "introducao_publica": (
            "Nos próximos minutos, vamos passar juntos por quatro momentos: "
            "entender sua empresa, diagnosticar a operação, descobrir oportunidades, "
            "e desenhar um caminho.\n\n"
            "Ao final, mesmo que você decida não trabalhar com a gente, você "
            "sai daqui com um diagnóstico estratégico do seu negócio."
        ),
        "descricao_interna": (
            "Apresentação inicial + promessa de valor. "
            "Captura também o tempo disponível do cliente para calibrar profundidade."
        ),
        "obrigatorio": True,
    },
    {
        "slug": SlugAto.CALIBRACAO,
        "ordem": 1,
        "titulo_publico": "Antes de tudo, vamos nos conhecer.",
        "subtitulo_publico": (
            "Algumas perguntas rápidas para entendermos quem você é e o momento da sua empresa."
        ),
        "descricao_interna": (
            "Calibração silenciosa do perfil de profundidade (Light/Standard/"
            "Deep/Enterprise) via porte_operacional, papel_decisor, e "
            "evento_gatilho. Captura também o pitch da empresa em uma frase."
        ),
        "obrigatorio": True,
    },
    {
        "slug": SlugAto.COMPREENSAO,
        "ordem": 2,
        "titulo_publico": "O que vocês entregam ao mundo.",
        "subtitulo_publico": ("Vamos entender como sua empresa cria, entrega e captura valor."),
        "descricao_interna": (
            "Mapeamento do modelo de negócio: proposta de valor, diferencial, "
            "ciclo comercial, operação core. Base para sugerir módulos certos."
        ),
        "obrigatorio": True,
    },
    {
        "slug": SlugAto.DIAGNOSTICO,
        "ordem": 3,
        "titulo_publico": "Vamos entender como sua operação realmente acontece.",
        "subtitulo_publico": (
            "Aqui descobrimos os gargalos invisíveis e as dores que talvez "
            "você ainda não tenha verbalizado."
        ),
        "descricao_interna": (
            "Coração da metodologia. Profundidade adaptativa baseada no perfil. "
            "Captura: dispersão de informação, retrabalho, dependência humana, "
            "perdas históricas, fragmentação tecnológica. Dispara insights ao vivo."
        ),
        "obrigatorio": True,
    },
    {
        "slug": SlugAto.ASPIRACOES,
        "ordem": 4,
        "titulo_publico": "Onde você quer chegar.",
        "subtitulo_publico": ("Sem isso, qualquer sistema é solução para o problema errado."),
        "descricao_interna": (
            "Visão de 12 meses, referências inspiracionais, motivação simbólica. "
            "A motivação simbólica costuma ser a chave emocional da venda."
        ),
        "obrigatorio": True,
    },
    {
        "slug": SlugAto.RESTRICOES,
        "ordem": 5,
        "titulo_publico": "Agora, a parte mais honesta da conversa.",
        "subtitulo_publico": (
            "Quanto mais real você for aqui, mais preciso será o que vamos te entregar."
        ),
        "introducao_publica": (
            "A Ferzion não tem proposta única — temos caminhos diferentes "
            "para realidades diferentes. Investimento, prazo e equipe interna "
            "definem o desenho do projeto."
        ),
        "descricao_interna": (
            "Captura faixa de investimento, prazos (desejado vs crítico), "
            "envolvimento interno. Calibra escopo do que será proposto."
        ),
        "obrigatorio": True,
    },
    {
        "slug": SlugAto.SINTESE,
        "ordem": 6,
        "titulo_publico": "Aqui está o que descobrimos sobre o seu negócio.",
        "subtitulo_publico": (
            "Diagnóstico estratégico, oportunidades identificadas, e o caminho que recomendamos."
        ),
        "descricao_interna": (
            "Ato gerado, não respondido. Composição determinística baseada em "
            "regras de síntese aplicadas aos sinais capturados. "
            "Inclui frase-síntese, score de maturidade digital, oportunidades, "
            "módulos sugeridos, próximos passos."
        ),
        "obrigatorio": True,
    },
    {
        "slug": SlugAto.PONTE,
        "ordem": 7,
        "titulo_publico": "Este é o início do nosso relacionamento.",
        "subtitulo_publico": (
            "Você terá acesso ao seu painel pessoal, com diagnóstico expandido e próximos passos."
        ),
        "descricao_interna": (
            "Transição do briefing para o painel do cliente. "
            "Envia link mágico por email + apresenta agenda da sessão estratégica."
        ),
        "obrigatorio": True,
    },
]


# =============================================================================
#  Catálogo de sinais — 22 sinais cobrindo as 7 categorias
# =============================================================================

SINAIS_CANONICOS: list[dict[str, Any]] = [
    # --- PERFIL ---
    {
        "chave": "porte_operacional",
        "nome": "Porte operacional",
        "descricao": (
            "Tamanho da operação medido por faixa de funcionários. "
            "Sinal-âncora para calibração de profundidade do briefing."
        ),
        "categoria": CategoriaSinal.PERFIL,
        "tipo_valor": TipoValorSinal.ESCALA,
        "valores_validos": [1, 5],
    },
    {
        "chave": "papel_decisor",
        "nome": "Papel do decisor",
        "descricao": (
            "Posição na estrutura: dono/sócio (alto), gestor/diretor (médio), "
            "responsável tecnologia (médio), pesquisa (baixo)."
        ),
        "categoria": CategoriaSinal.PERFIL,
        "tipo_valor": TipoValorSinal.CATEGORICO,
        "valores_validos": ["dono", "socio", "diretor", "responsavel_tech", "pesquisa"],
    },
    {
        "chave": "maturidade_temporal",
        "nome": "Maturidade temporal",
        "descricao": (
            "Há quanto tempo a empresa existe. Empresas novas têm dores "
            "diferentes de estabelecidas."
        ),
        "categoria": CategoriaSinal.PERFIL,
        "tipo_valor": TipoValorSinal.CATEGORICO,
        "valores_validos": ["nova", "1_a_3_anos", "3_a_10_anos", "consolidada"],
    },
    {
        "chave": "evento_gatilho",
        "nome": "Evento gatilho",
        "descricao": (
            "Resposta livre à pergunta 'O que aconteceu nas últimas semanas "
            "que te trouxe aqui?'. Captura dor recente, urgência real, "
            "contexto emocional. Texto preservado integral; categorização "
            "por palavras-chave acontece no motor de sinais."
        ),
        "categoria": CategoriaSinal.PERFIL,
        "tipo_valor": TipoValorSinal.TEXTO,
    },
    {
        "chave": "segmento_operacional",
        "nome": "Segmento operacional",
        "descricao": (
            "Área de atuação principal da empresa. Funciona como sinal contextual "
            "para adaptar linguagem, exemplos, templates de oportunidade, regras "
            "setoriais e interpretação dos demais sinais diagnósticos."
        ),
        "categoria": CategoriaSinal.PERFIL,
        "tipo_valor": TipoValorSinal.CATEGORICO,
        "valores_validos": [
            "servicos",
            "comercio",
            "industria_producao",
            "logistica_transporte",
            "saude",
            "educacao",
            "tecnologia",
            "construcao_imoveis",
            "alimentacao",
            "outro",
        ],
    },
    # --- NEGOCIO ---
    {
        "chave": "modelo_comercial",
        "nome": "Modelo comercial",
        "descricao": (
            "Como o cliente captura valor: consultivo, transacional, recorrente, "
            "outbound, ou híbrido."
        ),
        "categoria": CategoriaSinal.NEGOCIO,
        "tipo_valor": TipoValorSinal.CATEGORICO,
        "valores_validos": ["consultivo", "transacional", "recorrente", "outbound", "hibrido"],
    },
    {
        "chave": "volume_comercial",
        "nome": "Volume comercial",
        "descricao": "Faixa de negócios fechados por mês.",
        "categoria": CategoriaSinal.NEGOCIO,
        "tipo_valor": TipoValorSinal.CATEGORICO,
        "valores_validos": ["baixo", "medio", "alto", "muito_alto", "nao_medido"],
    },
    {
        "chave": "proposta_valor",
        "nome": "Proposta de valor declarada",
        "descricao": (
            "Resposta à pergunta 'se eu fosse seu cliente final, o que eu "
            "compraria de vocês?'. Texto preservado — alimenta frase-síntese "
            "do Ato 6 e serve como referência consultiva primária."
        ),
        "categoria": CategoriaSinal.NEGOCIO,
        "tipo_valor": TipoValorSinal.TEXTO,
    },
    # --- OPERACAO ---
    {
        "chave": "complexidade_operacional",
        "nome": "Complexidade operacional",
        "descricao": (
            "Quão complexa é a entrega para um cliente. Inferida do número de "
            "etapas e pessoas envolvidas."
        ),
        "categoria": CategoriaSinal.OPERACAO,
        "tipo_valor": TipoValorSinal.CATEGORICO,
        "valores_validos": ["baixa", "media", "alta", "muito_alta"],
    },
    {
        "chave": "ferramenta_comercial",
        "nome": "Ferramenta comercial usada",
        "descricao": (
            "Onde o cliente acompanha vendas hoje. Combina com volume_comercial "
            "para detectar gargalos."
        ),
        "categoria": CategoriaSinal.OPERACAO,
        "tipo_valor": TipoValorSinal.CATEGORICO,
        "valores_validos": ["planilha", "crm", "sistema_proprio", "whatsapp", "informal"],
    },
    {
        "chave": "fragmentacao_tecnologica",
        "nome": "Fragmentação tecnológica",
        "descricao": (
            "Quantos sistemas/ferramentas digitais a empresa usa. "
            "Quanto mais, maior risco de dispersão."
        ),
        "categoria": CategoriaSinal.OPERACAO,
        "tipo_valor": TipoValorSinal.CATEGORICO,
        "valores_validos": ["baixa", "media", "alta", "perdeu_a_conta"],
    },
    {
        "chave": "nivel_integracao",
        "nome": "Nível de integração entre sistemas",
        "descricao": "Grau de comunicação entre as ferramentas digitais usadas.",
        "categoria": CategoriaSinal.OPERACAO,
        "tipo_valor": TipoValorSinal.CATEGORICO,
        "valores_validos": [
            "integrado",
            "parcial",
            "isolado",
            "manual_via_planilha",
            "desconhecido",
        ],
    },
    # --- DOR ---
    {
        "chave": "dispersao_informacao",
        "nome": "Dispersão da informação",
        "descricao": (
            "Quão espalhada está a informação operacional da empresa. "
            "Alto = informação em múltiplos lugares (planilha, papel, WhatsApp, cabeça)."
        ),
        "categoria": CategoriaSinal.DOR,
        "tipo_valor": TipoValorSinal.CATEGORICO,
        "valores_validos": ["alto", "medio", "baixo"],
    },
    {
        "chave": "dependencia_humana_critica",
        "nome": "Dependência humana crítica",
        "descricao": (
            "Existência de pessoas-chave cuja ausência paralisa partes da operação. "
            "Risco operacional silencioso clássico."
        ),
        "categoria": CategoriaSinal.DOR,
        "tipo_valor": TipoValorSinal.CATEGORICO,
        "valores_validos": ["alta", "media", "baixa"],
    },
    {
        "chave": "tempo_perdido_operacional",
        "nome": "Tempo perdido em transferência de informação",
        "descricao": (
            "Quanto tempo a equipe gasta com tarefas de baixo valor "
            "(transferir info de um lugar para outro)."
        ),
        "categoria": CategoriaSinal.DOR,
        "tipo_valor": TipoValorSinal.CATEGORICO,
        "valores_validos": ["baixo", "razoavel", "muito", "nao_medido"],
    },
    {
        "chave": "historico_perda_operacional",
        "nome": "Histórico de perdas operacionais",
        "descricao": (
            "Já houve perdas de cliente, dinheiro ou prazo por falha operacional? "
            "Captura a 'ferida' do cliente — alto poder consultivo."
        ),
        "categoria": CategoriaSinal.DOR,
        "tipo_valor": TipoValorSinal.CATEGORICO,
        "valores_validos": ["grave", "escala_pequena", "frequente", "nao", "nao_disse"],
    },
    # --- ASPIRACAO ---
    {
        "chave": "referencia_inspiracional",
        "nome": "Referência inspiracional",
        "descricao": (
            "Empresa ou marca que o cliente cita como referência. "
            "Indicador valioso de teto de qualidade esperado."
        ),
        "categoria": CategoriaSinal.ASPIRACAO,
        "tipo_valor": TipoValorSinal.TEXTO,
    },
    {
        "chave": "visao_futura",
        "nome": "Visão de futuro (12 meses)",
        "descricao": (
            "Resposta à pergunta 'imagina que daqui a 12 meses esse sistema "
            "está funcionando do jeito que você sonha — o que mudou na sua "
            "rotina?'. Texto preservado. Componente emocional da devolutiva."
        ),
        "categoria": CategoriaSinal.ASPIRACAO,
        "tipo_valor": TipoValorSinal.TEXTO,
    },
    # --- RESTRICAO ---
    {
        "chave": "faixa_investimento",
        "nome": "Faixa de investimento",
        "descricao": "Faixa orçamentária declarada pelo cliente.",
        "categoria": CategoriaSinal.RESTRICAO,
        "tipo_valor": TipoValorSinal.CATEGORICO,
        "valores_validos": [
            "ate_30k",
            "30k_a_80k",
            "80k_a_200k",
            "acima_200k",
            "nao_definida",
            "discutir_depois",
        ],
    },
    {
        "chave": "urgencia_implicita",
        "nome": "Urgência implícita",
        "descricao": "Diferença entre prazo desejado e prazo crítico.",
        "categoria": CategoriaSinal.RESTRICAO,
        "tipo_valor": TipoValorSinal.CATEGORICO,
        "valores_validos": ["alta", "media", "baixa"],
    },
    # --- META ---
    {
        "chave": "perfil_profundidade_calculado",
        "nome": "Perfil de profundidade (calculado)",
        "descricao": (
            "Resultado do Score Composto de Aprofundamento (SCA). "
            "Determina quais perguntas e atos são mostrados. "
            "Calculado dinamicamente, não respondido."
        ),
        "categoria": CategoriaSinal.META,
        "tipo_valor": TipoValorSinal.CATEGORICO,
        "valores_validos": ["light", "standard", "deep", "enterprise"],
    },
    {
        "chave": "disponibilidade_tempo",
        "nome": "Disponibilidade de tempo declarada",
        "descricao": (
            "Quanto tempo o cliente declara ter para o briefing. "
            "Calibrador secundário do perfil de profundidade — junto com "
            "porte_operacional, define densidade do fluxo."
        ),
        "categoria": CategoriaSinal.META,
        "tipo_valor": TipoValorSinal.CATEGORICO,
        "valores_validos": ["rapido", "medio", "completo", "salvar_depois"],
    },
]


# =============================================================================
#  Registro de módulos de seed por ato
#  Adicionar aqui conforme novos atos forem populados.
# =============================================================================

SEED_MODULES_POR_ATO: dict[SlugAto, Any] = {
    SlugAto.CALIBRACAO: ato_1_calibracao,
    # SlugAto.COMPREENSAO: ato_2_compreensao,   (futuro)
    # SlugAto.DIAGNOSTICO: ato_3_diagnostico,   (futuro)
}


# =============================================================================
#  Comando
# =============================================================================


class Command(BaseCommand):
    """Comando de seed do Roteiro Universal Ferzion."""

    help = (
        "Popula a base com a estrutura inicial do Roteiro Universal Ferzion: "
        "identidade, v1 em draft, atos canônicos, catálogo de sinais e "
        "perguntas declarativas dos atos."
    )

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--force",
            action="store_true",
            help=(
                "Apaga TODA a metodologia atual antes de recriar. "
                "ATENÇÃO: destrói perguntas, opções, mapeamentos, insights "
                "e regras já cadastrados."
            ),
        )

    def handle(self, *args: Any, **options: Any) -> None:
        force = options.get("force", False)

        if force:
            self._confirm_destructive_or_abort()
            self._reset_completo()

        with transaction.atomic():
            identidade = self._garantir_identidade()
            versao = self._garantir_versao_em_draft(identidade)
            atos_criados = self._garantir_atos(versao)
            sinais_criados = self._garantir_sinais()
            load_results = self._carregar_perguntas(versao)

        self._imprimir_resumo(
            identidade=identidade,
            versao=versao,
            atos_criados=atos_criados,
            sinais_criados=sinais_criados,
            load_results=load_results,
        )

    # -------------------------------------------------------------------------
    #  Reset destrutivo
    # -------------------------------------------------------------------------
    def _confirm_destructive_or_abort(self) -> None:
        self.stdout.write(
            self.style.WARNING("\n⚠️  Modo --force ativo. Apagando metodologia existente...\n")
        )

    def _reset_completo(self) -> None:
        deleted_versoes, _ = RoteiroVersao.objects.all().delete()
        deleted_identidades, _ = RoteiroIdentidade.objects.all().delete()
        deleted_sinais, _ = CatalogoSinal.objects.all().delete()

        self.stdout.write(f"  · {deleted_versoes} registros de versões/atos/perguntas/etc apagados")
        self.stdout.write(f"  · {deleted_identidades} identidades apagadas")
        self.stdout.write(f"  · {deleted_sinais} sinais do catálogo apagados\n")

    # -------------------------------------------------------------------------
    #  Garantias idempotentes
    # -------------------------------------------------------------------------
    def _garantir_identidade(self) -> RoteiroIdentidade:
        identidade, criada = RoteiroIdentidade.objects.get_or_create(
            slug="roteiro-universal-ferzion",
            defaults={
                "nome": "Roteiro Universal Ferzion",
                "tipo": TipoRoteiro.UNIVERSAL,
                "descricao_interna": (
                    "Roteiro de discovery universal da Ferzion. "
                    "Atende todo o espectro de clientes — do MEI à empresa "
                    "estabelecida — com profundidade calibrada dinamicamente "
                    "via Score Composto de Aprofundamento (SCA)."
                ),
                "is_active": True,
            },
        )
        marker = "criada" if criada else "já existia"
        self.stdout.write(f"  Identidade «{identidade.nome}» [{marker}]")
        return identidade

    def _garantir_versao_em_draft(self, identidade: RoteiroIdentidade) -> RoteiroVersao:
        em_draft = identidade.versao_em_draft
        if em_draft:
            self.stdout.write(f"  Versão {em_draft} [já existia]")
            return em_draft

        publicada = identidade.versao_publicada
        if publicada:
            nova = publicada.create_next_draft()
            self.stdout.write(f"  Versão {nova} [criada a partir de v{publicada.version}]")
            return nova

        nova = RoteiroVersao.objects.create(
            identidade=identidade,
            status=StatusVersao.DRAFT,
            notas_da_versao="Versão inicial criada pelo seed.",
        )
        self.stdout.write(f"  Versão {nova} [criada]")
        return nova

    def _garantir_atos(self, versao: RoteiroVersao) -> int:
        if versao.is_immutable:
            self.stdout.write(
                self.style.WARNING(
                    f"  ⚠ Versão {versao} está {versao.get_status_display().lower()}. "
                    "Não é possível adicionar atos."
                )
            )
            return 0

        slugs_existentes = set(versao.atos.values_list("slug", flat=True))
        criados = 0

        for ato_data in ATOS_CANONICOS:
            if ato_data["slug"] in slugs_existentes:
                continue
            Ato.objects.create(
                versao=versao,
                slug=ato_data["slug"],
                ordem=ato_data["ordem"],
                titulo_publico=ato_data["titulo_publico"],
                subtitulo_publico=ato_data.get("subtitulo_publico", ""),
                introducao_publica=ato_data.get("introducao_publica", ""),
                descricao_interna=ato_data.get("descricao_interna", ""),
                obrigatorio=ato_data.get("obrigatorio", True),
            )
            criados += 1
            self.stdout.write(f"    + Ato '{ato_data['slug']}' criado")

        if criados == 0:
            self.stdout.write("    (todos os atos canônicos já existem)")
        return criados

    def _garantir_sinais(self) -> int:
        chaves_existentes = set(CatalogoSinal.objects.values_list("chave", flat=True))
        criados = 0

        for sinal_data in SINAIS_CANONICOS:
            if sinal_data["chave"] in chaves_existentes:
                continue
            CatalogoSinal.objects.create(
                chave=sinal_data["chave"],
                nome=sinal_data["nome"],
                descricao=sinal_data["descricao"],
                categoria=sinal_data["categoria"],
                tipo_valor=sinal_data["tipo_valor"],
                valores_validos=sinal_data.get("valores_validos", []),
            )
            criados += 1
            self.stdout.write(f"    + Sinal '{sinal_data['chave']}' criado")

        if criados == 0:
            self.stdout.write("    (todos os sinais canônicos já existem)")
        return criados

    def _carregar_perguntas(self, versao: RoteiroVersao) -> list[LoadResult]:
        """Carrega perguntas declarativas a partir de seeds/ato_*.py."""
        if versao.is_immutable:
            self.stdout.write(
                self.style.WARNING(f"  ⚠ Versão {versao} está imutável — pulando perguntas.")
            )
            return []

        results: list[LoadResult] = []
        for ato_slug, modulo in SEED_MODULES_POR_ATO.items():
            specs = getattr(modulo, "PERGUNTAS", [])
            if not specs:
                continue
            result = load_perguntas_para_ato(versao, ato_slug, specs)
            results.append(result)
            self.stdout.write(f"  {result}")
        return results

    # -------------------------------------------------------------------------
    #  Resumo final
    # -------------------------------------------------------------------------
    def _imprimir_resumo(
        self,
        identidade: RoteiroIdentidade,
        versao: RoteiroVersao,
        atos_criados: int,
        sinais_criados: int,
        load_results: list[LoadResult],
    ) -> None:
        total_atos = versao.atos.count()
        total_sinais = CatalogoSinal.objects.count()
        total_perguntas = sum(a.perguntas.count() for a in versao.atos.all())

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("✓ Seed concluído"))
        self.stdout.write("=" * 60)
        self.stdout.write(f"  Identidade ativa:  {identidade.nome}")
        self.stdout.write(f"  Versão em rascunho: v{versao.version}")
        self.stdout.write(f"  Atos na versão:    {total_atos}")
        self.stdout.write(f"  Catálogo de sinais: {total_sinais}")
        self.stdout.write(f"  Perguntas:         {total_perguntas}")

        if load_results:
            total_p_criadas = sum(r.perguntas_criadas for r in load_results)
            total_p_atualizadas = sum(r.perguntas_atualizadas for r in load_results)
            total_o_criadas = sum(r.opcoes_criadas for r in load_results)
            total_m_criadas = sum(r.mapeamentos_criados for r in load_results)
            total_f_criadas = sum(r.frases_criadas for r in load_results)
            self.stdout.write(
                f"\n  Carga de perguntas: "
                f"+{total_p_criadas} criadas, ~{total_p_atualizadas} atualizadas, "
                f"+{total_o_criadas} opções, +{total_m_criadas} mapeamentos, "
                f"+{total_f_criadas} frases."
            )

        self.stdout.write(
            self.style.HTTP_INFO(
                "\n  → Para revisar: http://localhost:8001/admin/methodology/pergunta/\n"
            )
        )
