"""
Ferzion Discovery — Methodology / Seeds / Ato 1 — Calibração.

Conteúdo declarativo das perguntas do Ato 1.

Princípio: dados puros. Sem lógica. Loader cuida da persistência.
Idempotente por (ato_slug, codigo).

Cobertura de sinais:
    - papel_decisor (1.1)
    - maturidade_temporal (1.2)
    - evento_gatilho (1.3)
    - segmento_operacional (1.4)
    - porte_operacional (1.5)
    - disponibilidade_tempo (1.6)
"""

from __future__ import annotations

from apps.methodology.models import (
    Arquetipo,
    FaixaDevolutiva,
    SlugAto,
    TipoPergunta,
)

from ._loader import SEMPRE
from ._spec import MapeamentoSpec, OpcaoSpec, PerguntaSpec

PERGUNTAS: list[PerguntaSpec] = [
    # =========================================================================
    #  1.1 — papel_decisor (Calibradora)
    # =========================================================================
    PerguntaSpec(
        ato_slug=SlugAto.CALIBRACAO,
        codigo="1.1",
        ordem=0,
        arquetipo=Arquetipo.CALIBRADORA,
        tipo=TipoPergunta.ESCOLHA_UNICA,
        texto_publico="Qual seu papel nessa decisão de procurar um sistema?",
        objetivo_interno=(
            "Captura papel decisor para calibrar tom da devolutiva e nível de "
            "envolvimento esperado. Dono/sócio recebe linguagem direta; diretor "
            "recebe linguagem que ajude a apresentar internamente; pesquisa "
            "recebe abordagem informativa sem pressão."
        ),
        opcoes=[
            OpcaoSpec(
                codigo_interno="dono",
                texto_publico="Sou dono ou sócio — decido sozinho ou com poucos parceiros",
            ),
            OpcaoSpec(
                codigo_interno="socio",
                texto_publico="Sou sócio operacional — decido junto com o time fundador",
            ),
            OpcaoSpec(
                codigo_interno="diretor",
                texto_publico="Sou diretor ou gestor — vou levar a decisão para a empresa",
            ),
            OpcaoSpec(
                codigo_interno="responsavel_tech",
                texto_publico="Sou o responsável por tecnologia — estou avaliando opções",
            ),
            OpcaoSpec(
                codigo_interno="pesquisa",
                texto_publico="Estou pesquisando opções e entendendo melhor o cenário",
            ),
        ],
        mapeamentos=[
            MapeamentoSpec("papel_decisor", "dono", "dono"),
            MapeamentoSpec("papel_decisor", "socio", "socio"),
            MapeamentoSpec("papel_decisor", "diretor", "diretor"),
            MapeamentoSpec("papel_decisor", "responsavel_tech", "responsavel_tech"),
            MapeamentoSpec("papel_decisor", "pesquisa", "pesquisa"),
        ],
        devolutivas={
            FaixaDevolutiva.BAIXO: (
                "Você está fazendo o trabalho mais importante da sua jornada — "
                "entender antes de comprar. Esse diagnóstico vai te dar referência "
                "sólida para qualquer próxima decisão."
            ),
            FaixaDevolutiva.MEDIO: (
                "Você está numa posição estratégica — a decisão passa por você, "
                "mas precisa convencer outros. A devolutiva está estruturada "
                "pensando em como você vai apresentar isso internamente."
            ),
            FaixaDevolutiva.ALTO: (
                "Você está próximo da decisão e da operação. A devolutiva vai "
                "priorizar impacto prático, velocidade de implementação e "
                "clareza de retorno."
            ),
        },
    ),
    # =========================================================================
    #  1.2 — maturidade_temporal (Calibradora)
    # =========================================================================
    PerguntaSpec(
        ato_slug=SlugAto.CALIBRACAO,
        codigo="1.2",
        ordem=1,
        arquetipo=Arquetipo.CALIBRADORA,
        tipo=TipoPergunta.ESCOLHA_UNICA,
        texto_publico="Há quanto tempo essa empresa existe?",
        objetivo_interno=(
            "Captura maturidade temporal para contextualizar dores típicas do "
            "estágio. Empresas novas têm gargalos diferentes de consolidadas — "
            "ajuda a calibrar exemplos e linguagem de oportunidades."
        ),
        opcoes=[
            OpcaoSpec(
                codigo_interno="nova",
                texto_publico="Menos de 1 ano — estamos começando agora",
            ),
            OpcaoSpec(
                codigo_interno="1_a_3_anos",
                texto_publico="De 1 até 3 anos",
            ),
            OpcaoSpec(
                codigo_interno="3_a_10_anos",
                texto_publico="Mais de 3 até 10 anos",
            ),
            OpcaoSpec(
                codigo_interno="consolidada",
                texto_publico="Mais de 10 anos — empresa estabelecida",
            ),
        ],
        mapeamentos=[
            MapeamentoSpec("maturidade_temporal", "nova", "nova"),
            MapeamentoSpec("maturidade_temporal", "1_a_3_anos", "1_a_3_anos"),
            MapeamentoSpec("maturidade_temporal", "3_a_10_anos", "3_a_10_anos"),
            MapeamentoSpec("maturidade_temporal", "consolidada", "consolidada"),
        ],
        devolutivas={
            FaixaDevolutiva.BAIXO: (
                "Vocês estão na fase em que estruturar cedo evita o caos depois — "
                "o trabalho é construir base, não consertar."
            ),
            FaixaDevolutiva.MEDIO: (
                "Vocês estão no momento em que a operação amadureceu, e os "
                "gargalos que apareceram são previsíveis — todos navegáveis "
                "com sistema certo."
            ),
            FaixaDevolutiva.ALTO: (
                "Vocês têm operação testada pelo tempo. O desafio agora não é "
                "estruturar — é orquestrar o que já funciona."
            ),
        },
    ),
    # =========================================================================
    #  1.3 — evento_gatilho (Reveladora)
    # =========================================================================
    PerguntaSpec(
        ato_slug=SlugAto.CALIBRACAO,
        codigo="1.3",
        ordem=2,
        arquetipo=Arquetipo.REVELADORA,
        tipo=TipoPergunta.TEXTO_LONGO,
        texto_publico="O que aconteceu nas últimas semanas que te trouxe até aqui?",
        objetivo_interno=(
            "Captura contexto rico do momento atual. Resposta livre alimenta a "
            "devolutiva como referência consultiva e dispara insights de "
            "urgência. Texto preservado integralmente — categorização por "
            "palavras-chave acontece no motor de sinais (futuro)."
        ),
        helper_text="Pode ser uma frase só. A gente puxa o resto na conversa.",
        mapeamentos=[
            MapeamentoSpec(
                sinal_chave="evento_gatilho",
                opcao_codigo=SEMPRE,
                valor_extraido="__RESPOSTA__",
                notas="Placeholder substituído pela resposta real no motor de sinais.",
            ),
        ],
        devolutivas={
            FaixaDevolutiva.BAIXO: (
                "Mesmo sem um evento específico, vocês buscaram esse "
                "diagnóstico — isso já mostra disposição em evoluir."
            ),
            FaixaDevolutiva.MEDIO: (
                "Você mencionou algo concreto — esse tipo de incômodo costuma "
                "ser o primeiro sinal de que a operação pediu estrutura."
            ),
            FaixaDevolutiva.ALTO: (
                "Isso indica uma dor operacional concreta. A devolutiva vai "
                "priorizar causas estruturais e impacto operacional."
            ),
        },
    ),
    # =========================================================================
    #  1.4 — segmento_operacional (Calibradora)
    # =========================================================================
    PerguntaSpec(
        ato_slug=SlugAto.CALIBRACAO,
        codigo="1.4",
        ordem=3,
        arquetipo=Arquetipo.CALIBRADORA,
        tipo=TipoPergunta.ESCOLHA_UNICA_COM_OUTRO,
        texto_publico="Em que área sua empresa atua hoje?",
        objetivo_interno=(
            "Sinal contextual que adapta linguagem, exemplos, templates de "
            "oportunidade e regras setoriais. Influencia interpretação dos "
            "demais sinais diagnósticos."
        ),
        opcoes=[
            OpcaoSpec(
                codigo_interno="servicos",
                texto_publico=(
                    "Serviços profissionais (consultoria, agência, advocacia, contabilidade)"
                ),
            ),
            OpcaoSpec(
                codigo_interno="comercio",
                texto_publico="Comércio (loja física, e-commerce, distribuição)",
            ),
            OpcaoSpec(
                codigo_interno="industria_producao",
                texto_publico="Indústria, produção ou manufatura",
            ),
            OpcaoSpec(
                codigo_interno="logistica_transporte",
                texto_publico="Logística, transporte ou movimentação",
            ),
            OpcaoSpec(
                codigo_interno="saude",
                texto_publico="Saúde (clínica, consultório, laboratório)",
            ),
            OpcaoSpec(
                codigo_interno="educacao",
                texto_publico="Educação ou treinamento",
            ),
            OpcaoSpec(
                codigo_interno="tecnologia",
                texto_publico="Tecnologia ou software",
            ),
            OpcaoSpec(
                codigo_interno="construcao_imoveis",
                texto_publico="Construção, engenharia ou imobiliário",
            ),
            OpcaoSpec(
                codigo_interno="alimentacao",
                texto_publico="Alimentação ou hospitalidade",
            ),
            OpcaoSpec(
                codigo_interno="outro",
                texto_publico="Outro — descrevo abaixo",
            ),
        ],
        mapeamentos=[
            MapeamentoSpec("segmento_operacional", "servicos", "servicos"),
            MapeamentoSpec("segmento_operacional", "comercio", "comercio"),
            MapeamentoSpec("segmento_operacional", "industria_producao", "industria_producao"),
            MapeamentoSpec("segmento_operacional", "logistica_transporte", "logistica_transporte"),
            MapeamentoSpec("segmento_operacional", "saude", "saude"),
            MapeamentoSpec("segmento_operacional", "educacao", "educacao"),
            MapeamentoSpec("segmento_operacional", "tecnologia", "tecnologia"),
            MapeamentoSpec("segmento_operacional", "construcao_imoveis", "construcao_imoveis"),
            MapeamentoSpec("segmento_operacional", "alimentacao", "alimentacao"),
            MapeamentoSpec("segmento_operacional", "outro", "outro"),
        ],
        devolutivas={
            FaixaDevolutiva.BAIXO: (
                "Vocês operam num contexto que não cabe em rótulo padrão — a "
                "devolutiva está adaptada à realidade que você descreveu."
            ),
            FaixaDevolutiva.MEDIO: (
                "Operações nesse setor têm padrões previsíveis de gargalo — "
                "vamos partir desses padrões e ajustar à sua realidade específica."
            ),
            FaixaDevolutiva.ALTO: (
                "Operações em setores com camadas de exigência regulatória não "
                "toleram improviso — a devolutiva foca em rastreabilidade, "
                "controle e conformidade."
            ),
        },
    ),
    # =========================================================================
    #  1.5 — porte_operacional (Calibradora) — SINAL-ÂNCORA
    # =========================================================================
    PerguntaSpec(
        ato_slug=SlugAto.CALIBRACAO,
        codigo="1.5",
        ordem=4,
        arquetipo=Arquetipo.CALIBRADORA,
        tipo=TipoPergunta.ESCOLHA_UNICA,
        texto_publico="Hoje, qual cenário mais se aproxima da sua operação?",
        objetivo_interno=(
            "Sinal-âncora para calibração silenciosa do perfil de profundidade "
            "do briefing (Light/Standard/Deep/Enterprise). Cliente subestima "
            "porte com mais frequência que superestima — opções com referência "
            "numérica calibram a distorção."
        ),
        opcoes=[
            OpcaoSpec(
                codigo_interno="porte_1",
                texto_publico="Sou eu sozinho ou uma equipe bem pequena (até 2 pessoas)",
            ),
            OpcaoSpec(
                codigo_interno="porte_2",
                texto_publico="Pequena equipe — entre 3 e 15 pessoas",
            ),
            OpcaoSpec(
                codigo_interno="porte_3",
                texto_publico="Operação consolidada — entre 16 e 50 pessoas",
            ),
            OpcaoSpec(
                codigo_interno="porte_4",
                texto_publico="Operação grande — 51 a 200 pessoas",
            ),
            OpcaoSpec(
                codigo_interno="porte_5",
                texto_publico="Empresa estabelecida — mais de 200 pessoas",
            ),
        ],
        mapeamentos=[
            MapeamentoSpec("porte_operacional", "porte_1", 1),
            MapeamentoSpec("porte_operacional", "porte_2", 2),
            MapeamentoSpec("porte_operacional", "porte_3", 3),
            MapeamentoSpec("porte_operacional", "porte_4", 4),
            MapeamentoSpec("porte_operacional", "porte_5", 5),
        ],
        devolutivas={
            FaixaDevolutiva.BAIXO: (
                "Vocês estão no momento mais formativo. Aqui o ganho não é "
                "eficiência — é evitar que a operação cresça torta."
            ),
            FaixaDevolutiva.MEDIO: (
                "Vocês estão no porte onde planilhas começam a doer. O sistema "
                "certo agora libera tempo de gestão para estratégia."
            ),
            FaixaDevolutiva.ALTO: (
                "Vocês são uma operação consolidada. O desafio aqui não é "
                "arrumar uma área — é orquestrar o fluxo entre áreas que já "
                "existem."
            ),
        },
    ),
    # =========================================================================
    #  1.6 — disponibilidade_tempo (Calibradora)
    # =========================================================================
    PerguntaSpec(
        ato_slug=SlugAto.CALIBRACAO,
        codigo="1.6",
        ordem=5,
        arquetipo=Arquetipo.CALIBRADORA,
        tipo=TipoPergunta.ESCOLHA_UNICA,
        texto_publico="Quanto tempo você consegue dedicar agora ao briefing?",
        objetivo_interno=(
            "Calibrador secundário do perfil de profundidade. Junto com "
            "porte_operacional, define densidade do fluxo. Cliente que escolhe "
            "'rápido' recebe Light; 'completo' recebe Deep+."
        ),
        opcoes=[
            OpcaoSpec(
                codigo_interno="rapido",
                texto_publico="Tenho uns 5 minutos — quero o essencial",
            ),
            OpcaoSpec(
                codigo_interno="medio",
                texto_publico="Tenho uns 15 minutos — quero algo consistente",
            ),
            OpcaoSpec(
                codigo_interno="completo",
                texto_publico="Tenho 30 minutos ou mais — quero o diagnóstico completo",
            ),
            OpcaoSpec(
                codigo_interno="salvar_depois",
                texto_publico="Quero começar agora e continuar depois com mais calma",
            ),
        ],
        mapeamentos=[
            MapeamentoSpec("disponibilidade_tempo", "rapido", "rapido"),
            MapeamentoSpec("disponibilidade_tempo", "medio", "medio"),
            MapeamentoSpec("disponibilidade_tempo", "completo", "completo"),
            MapeamentoSpec("disponibilidade_tempo", "salvar_depois", "salvar_depois"),
        ],
        devolutivas={
            FaixaDevolutiva.BAIXO: (
                "Foi rápido, e mesmo assim já dá para ver o essencial. Se quiser "
                "aprofundar depois, o painel está sempre aberto."
            ),
            FaixaDevolutiva.MEDIO: (
                "Você dedicou tempo suficiente para um diagnóstico consistente — "
                "a devolutiva tem profundidade real."
            ),
            FaixaDevolutiva.ALTO: (
                "Você foi a fundo. Isso permite uma devolutiva mais estratégica e precisa."
            ),
        },
    ),
]
