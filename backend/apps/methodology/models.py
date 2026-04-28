"""
Ferzion Discovery — Methodology / Models.

★ Este é o coração do sistema ★

Este módulo modela a metodologia de discovery da Ferzion como conteúdo
versionado, append-only, com identidade estável e versões imutáveis após
publicação.

Padrão arquitetural: Aggregate Root + Snapshots Imutáveis.
Ver docs/architecture/decisions/0003-versionamento-append-only.md

Hierarquia:
    RoteiroIdentidade (alma — UUID estável)
        └── RoteiroVersao (fotografia — draft / published / archived)
                └── Ato
                        └── Pergunta
                                └── OpcaoDePergunta (para escolha_*)
                                └── MapeamentoDeSinal → CatalogoSinal

Estados de RoteiroVersao:
    draft     → editável
    published → imutável, é a versão "ativa" (no máximo 1 por identidade)
    archived  → imutável, foi published mas perdeu o lugar para nova versão
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone
from django.utils.text import slugify

from shared.domain.base_entity import BaseEntity
from shared.exceptions import (
    ImmutableEntityModificationAttempt,
    InvalidStateTransition,
    InvariantViolation,
)

if TYPE_CHECKING:
    pass


# =============================================================================
#  ENUMS
# =============================================================================


class TipoRoteiro(models.TextChoices):
    """
    Tipos de roteiro suportados.

    O MVP usa apenas UNIVERSAL. Os demais existem na enum desde já para
    preparar o modelo para verticalização futura SEM migration estrutural.
    """

    UNIVERSAL = "universal", "Universal"
    LOGISTICA = "logistica", "Logística"
    SAUDE = "saude", "Saúde"
    AGRO = "agro", "Agronegócio"
    JURIDICO = "juridico", "Jurídico"
    INDUSTRIA = "industria", "Indústria"
    RH = "rh", "Recursos Humanos"
    VAREJO = "varejo", "Varejo"
    SAAS = "saas", "SaaS"


class StatusVersao(models.TextChoices):
    """Estados do ciclo de vida de uma RoteiroVersao."""

    DRAFT = "draft", "Rascunho"
    PUBLISHED = "published", "Publicada"
    ARCHIVED = "archived", "Arquivada"


class SlugAto(models.TextChoices):
    """Slugs canônicos dos 7 atos da metodologia Ferzion."""

    ACOLHIMENTO = "acolhimento", "Acolhimento"
    CALIBRACAO = "calibracao", "Calibração"
    COMPREENSAO = "compreensao", "Compreensão do Negócio"
    DIAGNOSTICO = "diagnostico", "Diagnóstico Operacional"
    ASPIRACOES = "aspiracoes", "Aspirações e Visão"
    RESTRICOES = "restricoes", "Restrições e Realidade"
    SINTESE = "sintese", "Síntese e Devolutiva"
    PONTE = "ponte", "Ponte para o Painel"


class TipoPergunta(models.TextChoices):
    """
    Tipos de pergunta suportados no MVP.

    Tipos preparados para futuro (definidos mas não implementados ainda):
        upload, ranking, matriz, condicional, conversacional, audio.

    Cada tipo define um schema próprio para o campo `tipo_config` na
    Pergunta. A modelagem permite adicionar novos tipos no futuro
    SEM migration estrutural — apenas dado novo.
    """

    # --- MVP ---
    TEXTO_CURTO = "texto_curto", "Texto curto (1 linha)"
    TEXTO_LONGO = "texto_longo", "Texto longo (várias linhas)"
    ESCOLHA_UNICA = "escolha_unica", "Escolha única (radio)"
    ESCOLHA_MULTIPLA = "escolha_multipla", "Escolha múltipla (checkboxes)"
    ESCALA = "escala", "Escala (1-N)"
    ESCOLHA_UNICA_COM_OUTRO = "escolha_unica_com_outro", "Escolha única + 'Outro'"

    # --- Reservados para implementação futura ---
    UPLOAD = "upload", "Upload de arquivo (futuro)"
    RANKING = "ranking", "Ranking / ordenação (futuro)"
    MATRIZ = "matriz", "Matriz visual (futuro)"
    CONDICIONAL = "condicional", "Condicional avançada (futuro)"
    CONVERSACIONAL = "conversacional", "Bloco conversacional (futuro)"
    AUDIO = "audio", "Áudio / voz (futuro)"


class PerfilProfundidade(models.TextChoices):
    """Perfis de profundidade da metodologia (PPA — Profundidade Progressiva Adaptativa)."""

    LIGHT = "light", "Light"
    STANDARD = "standard", "Standard"
    DEEP = "deep", "Deep"
    ENTERPRISE = "enterprise", "Enterprise"


class TipoValorSinal(models.TextChoices):
    """Tipos de valor que um sinal pode assumir."""

    CATEGORICO = "categorico", "Categórico (ex: 'alto', 'médio', 'baixo')"
    ESCALA = "escala", "Escala numérica (ex: 1-5)"
    BOOLEANO = "booleano", "Booleano (verdadeiro/falso)"
    NUMERICO = "numerico", "Numérico livre"
    TEXTO = "texto", "Texto preservado"


class CategoriaSinal(models.TextChoices):
    """Categoria taxonômica do sinal — facilita organização no admin."""

    PERFIL = "perfil", "Perfil do cliente"
    NEGOCIO = "negocio", "Modelo de negócio"
    OPERACAO = "operacao", "Operação"
    DOR = "dor", "Dor / risco"
    ASPIRACAO = "aspiracao", "Aspiração / visão"
    RESTRICAO = "restricao", "Restrição"
    META = "meta", "Meta-sinal (calibração interna)"


# =============================================================================
#  ROTEIRO IDENTIDADE — a "alma" estável
# =============================================================================


class RoteiroIdentidade(BaseEntity):
    """A identidade estável de um roteiro de discovery."""

    nome = models.CharField(
        max_length=120,
        verbose_name="Nome do roteiro",
        help_text="Nome humano (ex: 'Roteiro Universal Ferzion').",
    )
    slug = models.SlugField(
        max_length=140,
        unique=True,
        verbose_name="Slug",
        help_text="Identificador URL-friendly. Gerado automaticamente se vazio.",
    )
    tipo = models.CharField(
        max_length=32,
        choices=TipoRoteiro.choices,
        default=TipoRoteiro.UNIVERSAL,
        verbose_name="Tipo",
    )
    descricao_interna = models.TextField(
        blank=True,
        verbose_name="Descrição interna",
        help_text="Notas internas da Ferzion (não aparecem para o cliente).",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Ativa",
        help_text="Identidade inativa não aparece para novos briefings.",
    )

    class Meta:
        verbose_name = "Roteiro (identidade)"
        verbose_name_plural = "Roteiros (identidades)"
        ordering: ClassVar[list[str]] = ["nome"]
        indexes: ClassVar[list[models.Index]] = [
            models.Index(fields=["slug"]),
            models.Index(fields=["tipo", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.nome} ({self.get_tipo_display()})"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)

    @property
    def versao_publicada(self) -> RoteiroVersao | None:
        return self.versoes.filter(status=StatusVersao.PUBLISHED).first()

    @property
    def versao_em_draft(self) -> RoteiroVersao | None:
        return self.versoes.filter(status=StatusVersao.DRAFT).first()

    def proximo_numero_versao(self) -> int:
        ultima = self.versoes.order_by("-version").first()
        return (ultima.version + 1) if ultima else 1


# =============================================================================
#  ROTEIRO VERSÃO — uma "fotografia" imutável após publicação
# =============================================================================


class RoteiroVersao(BaseEntity):
    """Uma versão concreta de uma RoteiroIdentidade."""

    identidade = models.ForeignKey(
        RoteiroIdentidade,
        on_delete=models.PROTECT,
        related_name="versoes",
        verbose_name="Identidade",
    )
    version = models.PositiveIntegerField(
        verbose_name="Número da versão",
        help_text="Sequencial dentro da identidade. Gerado automaticamente.",
    )
    status = models.CharField(
        max_length=16,
        choices=StatusVersao.choices,
        default=StatusVersao.DRAFT,
        db_index=True,
        verbose_name="Status",
    )
    published_at = models.DateTimeField(null=True, blank=True, verbose_name="Publicada em")
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="roteiros_publicados",
        verbose_name="Publicada por",
    )
    archived_at = models.DateTimeField(null=True, blank=True, verbose_name="Arquivada em")
    snapshot_json = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Snapshot",
        help_text="Estrutura completa congelada. Preenchido na publicação.",
    )
    notas_da_versao = models.TextField(
        blank=True,
        verbose_name="Notas desta versão",
        help_text="Changelog / notas internas (ex: 'Refinada pergunta 3.6').",
    )

    class Meta:
        verbose_name = "Versão de roteiro"
        verbose_name_plural = "Versões de roteiro"
        ordering: ClassVar[list[str]] = ["-identidade", "-version"]
        constraints: ClassVar[list[Any]] = [
            models.UniqueConstraint(
                fields=["identidade", "version"],
                name="uniq_identidade_versao",
            ),
            models.UniqueConstraint(
                fields=["identidade"],
                condition=models.Q(status="draft"),
                name="uniq_draft_por_identidade",
            ),
            models.UniqueConstraint(
                fields=["identidade"],
                condition=models.Q(status="published"),
                name="uniq_published_por_identidade",
            ),
        ]
        indexes: ClassVar[list[models.Index]] = [
            models.Index(fields=["identidade", "status"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return f"{self.identidade.nome} v{self.version} ({self.get_status_display()})"

    def save(self, *args: Any, **kwargs: Any) -> None:
        is_new = self._state.adding
        if is_new and not self.version:
            self.version = self.identidade.proximo_numero_versao()

        if not is_new and self.pk:
            try:
                original = type(self).objects.get(pk=self.pk)
            except type(self).DoesNotExist:
                original = None

            if original and original.status in (
                StatusVersao.PUBLISHED,
                StatusVersao.ARCHIVED,
            ):
                campos_protegidos = {"notas_da_versao", "snapshot_json"}
                update_fields = kwargs.get("update_fields") or set()
                if not update_fields:
                    if any(getattr(self, f) != getattr(original, f) for f in campos_protegidos):
                        raise ImmutableEntityModificationAttempt(
                            f"Versão v{self.version} está {original.get_status_display()} "
                            "e não pode ter conteúdo modificado. "
                            "Crie uma nova versão a partir desta."
                        )
        super().save(*args, **kwargs)

    @property
    def is_editable(self) -> bool:
        return self.status == StatusVersao.DRAFT

    @property
    def is_immutable(self) -> bool:
        return self.status in (StatusVersao.PUBLISHED, StatusVersao.ARCHIVED)

    @transaction.atomic
    def publish(self, by_user: Any = None) -> None:
        if self.status != StatusVersao.DRAFT:
            raise InvalidStateTransition(
                f"Apenas versões em rascunho podem ser publicadas. "
                f"Versão atual: {self.get_status_display()}."
            )
        self._validate_publishable()

        publicada_atual = self.identidade.versao_publicada
        if publicada_atual:
            publicada_atual.archive()

        self.snapshot_json = self._build_snapshot()
        self.published_at = timezone.now()
        self.published_by = by_user
        self.status = StatusVersao.PUBLISHED
        self.save(
            update_fields=[
                "status",
                "published_at",
                "published_by",
                "snapshot_json",
                "updated_at",
            ]
        )

    @transaction.atomic
    def archive(self) -> None:
        if self.status == StatusVersao.ARCHIVED:
            return
        if self.status == StatusVersao.DRAFT:
            raise InvalidStateTransition(
                "Versões em rascunho não devem ser arquivadas — apenas excluídas."
            )
        self.archived_at = timezone.now()
        self.status = StatusVersao.ARCHIVED
        self.save(update_fields=["status", "archived_at", "updated_at"])

    @transaction.atomic
    def create_next_draft(self) -> RoteiroVersao:
        if self.identidade.versao_em_draft is not None:
            raise InvariantViolation(
                "Já existe um rascunho pendente nesta identidade. "
                "Publique ou exclua o rascunho atual antes de criar outro."
            )
        nova = RoteiroVersao.objects.create(
            identidade=self.identidade,
            status=StatusVersao.DRAFT,
            notas_da_versao=f"Derivada de v{self.version}",
        )
        for ato in self.atos.all():
            ato.duplicate_to(nova)
        return nova

    def _validate_publishable(self) -> None:
        if self.atos.count() == 0:
            raise InvariantViolation(
                "Esta versão não tem nenhum ato. Adicione pelo menos um ato antes de publicar."
            )
        # Garante que cada ato tem ao menos uma pergunta (para atos não-síntese)
        atos_sem_perguntas = [
            ato
            for ato in self.atos.all()
            if ato.slug not in (SlugAto.ACOLHIMENTO, SlugAto.SINTESE, SlugAto.PONTE)
            and ato.perguntas.count() == 0
        ]
        if atos_sem_perguntas:
            slugs = ", ".join(a.get_slug_display() for a in atos_sem_perguntas)
            raise InvariantViolation(
                f"Os seguintes atos não têm nenhuma pergunta: {slugs}. "
                "Adicione perguntas ou remova os atos antes de publicar."
            )

    def _build_snapshot(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "identidade": {
                "id": str(self.identidade.id),
                "nome": self.identidade.nome,
                "slug": self.identidade.slug,
                "tipo": self.identidade.tipo,
            },
            "version": self.version,
            "atos": [ato.to_snapshot_dict() for ato in self.atos.order_by("ordem")],
            "snapshot_built_at": timezone.now().isoformat(),
        }


# =============================================================================
#  ATO — uma seção narrativa do roteiro
# =============================================================================


class Ato(BaseEntity):
    """Um ato do roteiro — uma "cena" narrativa."""

    versao = models.ForeignKey(
        RoteiroVersao,
        on_delete=models.CASCADE,
        related_name="atos",
        verbose_name="Versão",
    )
    slug = models.CharField(
        max_length=32,
        choices=SlugAto.choices,
        verbose_name="Slug do ato",
        help_text="Identificador canônico do ato (contrato com frontend).",
    )
    ordem = models.PositiveSmallIntegerField(verbose_name="Ordem")
    titulo_publico = models.CharField(
        max_length=200,
        verbose_name="Título público",
        help_text="Aparece para o cliente. Tom Ferzion: humano, claro.",
    )
    subtitulo_publico = models.CharField(
        max_length=400, blank=True, verbose_name="Subtítulo público"
    )
    introducao_publica = models.TextField(
        blank=True,
        verbose_name="Introdução pública",
        help_text="Texto introdutório longo (opcional). Markdown aceito.",
    )
    descricao_interna = models.TextField(
        blank=True,
        verbose_name="Descrição interna",
        help_text="Notas/objetivos internos do ato. Não aparece para o cliente.",
    )
    obrigatorio = models.BooleanField(
        default=True,
        verbose_name="Obrigatório",
        help_text="Se desmarcado, este ato pode ser pulado por certos perfis.",
    )
    configuracao = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Configuração",
        help_text="Configurações comportamentais específicas (JSON).",
    )

    class Meta:
        verbose_name = "Ato"
        verbose_name_plural = "Atos"
        ordering: ClassVar[list[str]] = ["versao", "ordem"]
        constraints: ClassVar[list[Any]] = [
            models.UniqueConstraint(fields=["versao", "slug"], name="uniq_ato_slug_por_versao"),
            models.UniqueConstraint(fields=["versao", "ordem"], name="uniq_ato_ordem_por_versao"),
        ]
        indexes: ClassVar[list[models.Index]] = [
            models.Index(fields=["versao", "ordem"]),
        ]

    def __str__(self) -> str:
        return f"{self.versao.identidade.nome} v{self.versao.version} · {self.get_slug_display()}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk and self.versao.is_immutable:
            raise ImmutableEntityModificationAttempt(
                f"Não é possível modificar atos de uma versão "
                f"{self.versao.get_status_display().lower()}. "
                "Crie uma nova versão a partir desta."
            )
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        if self.versao.is_immutable:
            raise ImmutableEntityModificationAttempt(
                f"Não é possível excluir atos de uma versão "
                f"{self.versao.get_status_display().lower()}."
            )
        return super().delete(*args, **kwargs)

    def duplicate_to(self, nova_versao: RoteiroVersao) -> Ato:
        """Duplica este ato (e perguntas filhas) para uma nova versão."""
        novo = Ato.objects.create(
            versao=nova_versao,
            slug=self.slug,
            ordem=self.ordem,
            titulo_publico=self.titulo_publico,
            subtitulo_publico=self.subtitulo_publico,
            introducao_publica=self.introducao_publica,
            descricao_interna=self.descricao_interna,
            obrigatorio=self.obrigatorio,
            configuracao=self.configuracao,
        )
        # Duplica perguntas filhas (que duplicam suas próprias opções e mapeamentos)
        for pergunta in self.perguntas.order_by("ordem"):
            pergunta.duplicate_to(novo)
        return novo

    def to_snapshot_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "slug": self.slug,
            "ordem": self.ordem,
            "titulo_publico": self.titulo_publico,
            "subtitulo_publico": self.subtitulo_publico,
            "introducao_publica": self.introducao_publica,
            "obrigatorio": self.obrigatorio,
            "configuracao": self.configuracao,
            "perguntas": [p.to_snapshot_dict() for p in self.perguntas.order_by("ordem")],
        }


# =============================================================================
#  PERGUNTA — unidade atômica do conteúdo
# =============================================================================


class Pergunta(BaseEntity):
    """
    Uma pergunta dentro de um ato.

    Estrutura:
        - Campos comuns: texto público, código, ordem, tipo, perfis_minimos.
        - tipo_config: JSON com schema variando por tipo (ver TipoPergunta).
        - precondicoes_json: condições que precisam ser satisfeitas para
          esta pergunta aparecer (baseadas em sinais já capturados).
        - perfis_minimos: lista de perfis a partir dos quais a pergunta aparece.
          Ex: ["deep", "enterprise"] = aparece só para perfis Deep+.
    """

    ato = models.ForeignKey(
        Ato,
        on_delete=models.CASCADE,
        related_name="perguntas",
        verbose_name="Ato",
    )
    codigo = models.CharField(
        max_length=16,
        verbose_name="Código",
        help_text="Identificador legível (ex: '1.7', '3.2', '2A.1').",
    )
    ordem = models.PositiveSmallIntegerField(
        verbose_name="Ordem",
        help_text="Posição da pergunta dentro do ato.",
    )
    tipo = models.CharField(
        max_length=32,
        choices=TipoPergunta.choices,
        verbose_name="Tipo de pergunta",
    )

    # --- Conteúdo público (cliente vê) ---
    texto_publico = models.TextField(
        verbose_name="Texto público",
        help_text="O enunciado que o cliente lê.",
    )
    placeholder = models.CharField(
        max_length=300,
        blank=True,
        verbose_name="Placeholder",
        help_text="Texto-guia dentro do campo (apenas tipos texto_*).",
    )
    helper_text = models.CharField(
        max_length=300,
        blank=True,
        verbose_name="Texto de ajuda",
        help_text="Microcopy abaixo do campo. Tom Ferzion.",
    )

    # --- Conteúdo interno ---
    objetivo_interno = models.TextField(
        blank=True,
        verbose_name="Objetivo interno",
        help_text="O que esta pergunta busca descobrir? (não aparece para o cliente)",
    )

    # --- Comportamento ---
    obrigatoria = models.BooleanField(
        default=True,
        verbose_name="Obrigatória",
        help_text="Se desmarcada, o cliente pode pular.",
    )
    perfis_minimos = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Perfis mínimos",
        help_text=(
            "Lista de perfis nos quais a pergunta aparece. "
            "Ex: ['standard', 'deep', 'enterprise']. "
            "Vazio = aparece em todos os perfis."
        ),
    )
    precondicoes = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Pré-condições",
        help_text=(
            "Condições para a pergunta aparecer (baseadas em sinais "
            "já capturados). JSON estruturado — ver docs."
        ),
    )

    # --- Config específica do tipo ---
    tipo_config = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Configuração do tipo",
        help_text=(
            "JSON com schema dependente do tipo. Exemplos: "
            "texto_curto → {'max_chars': 200}; "
            "escala → {'min': 1, 'max': 5, 'rotulos': {'1': 'Discordo'}}; "
            "escolha_unica_com_outro → {'rotulo_outro': 'Outro: descreva'}."
        ),
    )

    class Meta:
        verbose_name = "Pergunta"
        verbose_name_plural = "Perguntas"
        ordering: ClassVar[list[str]] = ["ato", "ordem"]
        constraints: ClassVar[list[Any]] = [
            models.UniqueConstraint(fields=["ato", "codigo"], name="uniq_pergunta_codigo_por_ato"),
            models.UniqueConstraint(fields=["ato", "ordem"], name="uniq_pergunta_ordem_por_ato"),
        ]
        indexes: ClassVar[list[models.Index]] = [
            models.Index(fields=["ato", "ordem"]),
            models.Index(fields=["tipo"]),
        ]

    def __str__(self) -> str:
        return f"{self.codigo} · {self.texto_publico[:60]}"

    # -------------------------------------------------------------------------
    #  Validação de imutabilidade
    # -------------------------------------------------------------------------
    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk and self.ato.versao.is_immutable:
            raise ImmutableEntityModificationAttempt(
                f"Não é possível modificar perguntas de uma versão "
                f"{self.ato.versao.get_status_display().lower()}."
            )
        self.full_clean()  # dispara clean() abaixo
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        if self.ato.versao.is_immutable:
            raise ImmutableEntityModificationAttempt(
                f"Não é possível excluir perguntas de uma versão "
                f"{self.ato.versao.get_status_display().lower()}."
            )
        return super().delete(*args, **kwargs)

    # -------------------------------------------------------------------------
    #  Validação semântica — clean()
    # -------------------------------------------------------------------------
    def clean(self) -> None:
        """Valida que tipo_config está coerente com o tipo escolhido."""
        super().clean()
        config = self.tipo_config or {}

        # Tipos texto: valida max_chars opcional
        if self.tipo in (TipoPergunta.TEXTO_CURTO, TipoPergunta.TEXTO_LONGO):
            if "max_chars" in config and not isinstance(config["max_chars"], int):
                raise ValidationError({"tipo_config": "max_chars deve ser inteiro."})

        # Tipos com opções precisam ter opções
        elif self.tipo in (
            TipoPergunta.ESCOLHA_UNICA,
            TipoPergunta.ESCOLHA_MULTIPLA,
            TipoPergunta.ESCOLHA_UNICA_COM_OUTRO,
        ):
            # Validamos que existem opções APÓS a pergunta ser salva pela
            # primeira vez (caso contrário não dá pra ter relação).
            # No clean(), apenas validamos a config.
            if self.tipo == TipoPergunta.ESCOLHA_MULTIPLA:
                if "min_selecoes" in config:
                    if not isinstance(config["min_selecoes"], int):
                        raise ValidationError({"tipo_config": "min_selecoes deve ser inteiro."})

        # Escala: precisa min e max
        elif self.tipo == TipoPergunta.ESCALA:
            if "min" not in config or "max" not in config:
                raise ValidationError({"tipo_config": "Escala exige 'min' e 'max' em tipo_config."})
            if not (isinstance(config["min"], int) and isinstance(config["max"], int)):
                raise ValidationError({"tipo_config": "min e max devem ser inteiros."})
            if config["min"] >= config["max"]:
                raise ValidationError({"tipo_config": "min deve ser menor que max."})

    # -------------------------------------------------------------------------
    #  API de domínio
    # -------------------------------------------------------------------------
    @property
    def requer_opcoes(self) -> bool:
        """True se o tipo da pergunta exige OpcaoDePergunta vinculadas."""
        return self.tipo in (
            TipoPergunta.ESCOLHA_UNICA,
            TipoPergunta.ESCOLHA_MULTIPLA,
            TipoPergunta.ESCOLHA_UNICA_COM_OUTRO,
        )

    def duplicate_to(self, novo_ato: Ato) -> Pergunta:
        """Duplica esta pergunta (e suas opções e mapeamentos) para outro ato."""
        nova = Pergunta.objects.create(
            ato=novo_ato,
            codigo=self.codigo,
            ordem=self.ordem,
            tipo=self.tipo,
            texto_publico=self.texto_publico,
            placeholder=self.placeholder,
            helper_text=self.helper_text,
            objetivo_interno=self.objetivo_interno,
            obrigatoria=self.obrigatoria,
            perfis_minimos=self.perfis_minimos,
            precondicoes=self.precondicoes,
            tipo_config=self.tipo_config,
        )
        for opcao in self.opcoes.order_by("ordem"):
            opcao.duplicate_to(nova)
        for mapeamento in self.mapeamentos.all():
            mapeamento.duplicate_to(nova)
        return nova

    def to_snapshot_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "codigo": self.codigo,
            "ordem": self.ordem,
            "tipo": self.tipo,
            "texto_publico": self.texto_publico,
            "placeholder": self.placeholder,
            "helper_text": self.helper_text,
            "obrigatoria": self.obrigatoria,
            "perfis_minimos": self.perfis_minimos,
            "precondicoes": self.precondicoes,
            "tipo_config": self.tipo_config,
            "opcoes": [opcao.to_snapshot_dict() for opcao in self.opcoes.order_by("ordem")],
            "mapeamentos": [m.to_snapshot_dict() for m in self.mapeamentos.all()],
        }


# =============================================================================
#  OPÇÃO DE PERGUNTA — alternativas para escolha_unica/multipla
# =============================================================================


class OpcaoDePergunta(BaseEntity):
    """
    Uma alternativa de resposta para perguntas de escolha.

    Cada opção tem um `codigo_interno` estável — usado em mapeamentos
    de sinal — e um `texto_publico` que pode ser refinado sem quebrar
    a lógica de extração.
    """

    pergunta = models.ForeignKey(
        Pergunta,
        on_delete=models.CASCADE,
        related_name="opcoes",
        verbose_name="Pergunta",
    )
    codigo_interno = models.CharField(
        max_length=64,
        verbose_name="Código interno",
        help_text=(
            "Identificador estável da opção (ex: 'porte_micro', 'modelo_recorrente'). "
            "Usado em mapeamentos de sinal."
        ),
    )
    ordem = models.PositiveSmallIntegerField(verbose_name="Ordem")
    texto_publico = models.CharField(
        max_length=300,
        verbose_name="Texto público",
        help_text="O que o cliente lê.",
    )
    descricao_publica = models.CharField(
        max_length=400,
        blank=True,
        verbose_name="Descrição pública",
        help_text="Descrição secundária opcional (aparece menor).",
    )
    icone = models.CharField(
        max_length=64,
        blank=True,
        verbose_name="Ícone",
        help_text="Nome do ícone (ex: 'building', 'user'). Opcional.",
    )

    class Meta:
        verbose_name = "Opção de pergunta"
        verbose_name_plural = "Opções de pergunta"
        ordering: ClassVar[list[str]] = ["pergunta", "ordem"]
        constraints: ClassVar[list[Any]] = [
            models.UniqueConstraint(
                fields=["pergunta", "codigo_interno"],
                name="uniq_opcao_codigo_por_pergunta",
            ),
            models.UniqueConstraint(
                fields=["pergunta", "ordem"],
                name="uniq_opcao_ordem_por_pergunta",
            ),
        ]
        indexes: ClassVar[list[models.Index]] = [
            models.Index(fields=["pergunta", "ordem"]),
        ]

    def __str__(self) -> str:
        return f"{self.pergunta.codigo} · [{self.codigo_interno}] {self.texto_publico[:40]}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk and self.pergunta.ato.versao.is_immutable:
            raise ImmutableEntityModificationAttempt(
                "Não é possível modificar opções de uma versão imutável."
            )
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        if self.pergunta.ato.versao.is_immutable:
            raise ImmutableEntityModificationAttempt(
                "Não é possível excluir opções de uma versão imutável."
            )
        return super().delete(*args, **kwargs)

    def duplicate_to(self, nova_pergunta: Pergunta) -> OpcaoDePergunta:
        return OpcaoDePergunta.objects.create(
            pergunta=nova_pergunta,
            codigo_interno=self.codigo_interno,
            ordem=self.ordem,
            texto_publico=self.texto_publico,
            descricao_publica=self.descricao_publica,
            icone=self.icone,
        )

    def to_snapshot_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "codigo_interno": self.codigo_interno,
            "ordem": self.ordem,
            "texto_publico": self.texto_publico,
            "descricao_publica": self.descricao_publica,
            "icone": self.icone,
        }


# =============================================================================
#  CATÁLOGO DE SINAIS — definições globais (não versionadas por roteiro)
# =============================================================================


class CatalogoSinal(BaseEntity):
    """
    Definição global de um sinal que existe no sistema Ferzion.

    Esta entidade é INTENCIONALMENTE não-versionada por roteiro. Sinais
    são vocabulário compartilhado entre todos os roteiros e métodos de
    extração. Reescrever a definição de um sinal afeta retroativamente
    a interpretação — por isso edições no catálogo devem ser raras e
    documentadas no campo `notas_internas`.

    Exemplo de sinais:
        - chave="porte_operacional", tipo=ESCALA, valores_validos=[1,2,3,4,5]
        - chave="dispersao_informacao", tipo=CATEGORICO, valores_validos=["alto","medio","baixo"]
        - chave="historico_perda_operacional", tipo=CATEGORICO, valores=["grave","escala_pequena","frequente","nao","nao_disse"]
    """

    chave = models.SlugField(
        max_length=80,
        unique=True,
        verbose_name="Chave",
        help_text="Identificador snake_case do sinal (ex: 'porte_operacional').",
    )
    nome = models.CharField(
        max_length=160,
        verbose_name="Nome",
        help_text="Nome legível (aparece no admin e em relatórios técnicos).",
    )
    descricao = models.TextField(
        verbose_name="Descrição",
        help_text="O que este sinal representa? Quando é capturado?",
    )
    categoria = models.CharField(
        max_length=32,
        choices=CategoriaSinal.choices,
        default=CategoriaSinal.OPERACAO,
        verbose_name="Categoria",
    )
    tipo_valor = models.CharField(
        max_length=16,
        choices=TipoValorSinal.choices,
        verbose_name="Tipo do valor",
    )
    valores_validos = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Valores válidos",
        help_text=(
            "Domínio do sinal. Para CATEGORICO: lista de strings. "
            "Para ESCALA: [min, max]. Para BOOLEANO: ignora. "
            "Para TEXTO/NUMERICO: ignora (validação livre)."
        ),
    )
    notas_internas = models.TextField(
        blank=True,
        verbose_name="Notas internas",
        help_text=(
            "Histórico de mudanças, justificativas, contexto da definição. "
            "Editar com cuidado — afeta interpretação histórica."
        ),
    )

    class Meta:
        verbose_name = "Sinal (catálogo)"
        verbose_name_plural = "Sinais (catálogo)"
        ordering: ClassVar[list[str]] = ["categoria", "chave"]
        indexes: ClassVar[list[models.Index]] = [
            models.Index(fields=["categoria"]),
        ]

    def __str__(self) -> str:
        return f"[{self.categoria}] {self.chave}"

    def valor_eh_valido(self, valor: Any) -> bool:
        """Valida se um valor está dentro do domínio definido."""
        if self.tipo_valor == TipoValorSinal.BOOLEANO:
            return isinstance(valor, bool)
        if self.tipo_valor == TipoValorSinal.NUMERICO:
            return isinstance(valor, int | float)
        if self.tipo_valor == TipoValorSinal.TEXTO:
            return isinstance(valor, str)
        if self.tipo_valor == TipoValorSinal.CATEGORICO:
            return valor in (self.valores_validos or [])
        if self.tipo_valor == TipoValorSinal.ESCALA:
            if not (
                isinstance(valor, int)
                and isinstance(self.valores_validos, list)
                and len(self.valores_validos) == 2
            ):
                return False
            return self.valores_validos[0] <= valor <= self.valores_validos[1]
        return False


# =============================================================================
#  MAPEAMENTO DE SINAL — regra "se respondeu X, extrai sinal Y com valor Z"
# =============================================================================


class MapeamentoDeSinal(BaseEntity):
    """
    Regra de extração: dada uma resposta a uma pergunta, qual sinal é
    capturado e com qual valor.

    Mapeamento é versionado JUNTO com a Pergunta (mesma versão de roteiro).
    Quando uma versão é publicada, os mapeamentos congelam com ela.

    Estrutura da `condicao`:
        {
            "operador": "in" | "equals" | "contains" | "always",
            "valores": [...]  // UUIDs de OpcaoDePergunta para in/equals,
                              // string para contains,
                              // ignorado para always
        }
    """

    pergunta = models.ForeignKey(
        Pergunta,
        on_delete=models.CASCADE,
        related_name="mapeamentos",
        verbose_name="Pergunta",
    )
    sinal = models.ForeignKey(
        CatalogoSinal,
        on_delete=models.PROTECT,
        related_name="mapeamentos",
        verbose_name="Sinal",
    )

    condicao = models.JSONField(
        verbose_name="Condição",
        help_text=(
            'JSON da condição. Ex: {"operador": "in", "valores": ["uuid_opt_a"]}. '
            "Operadores: in, equals, contains, always."
        ),
    )
    valor_extraido = models.JSONField(
        verbose_name="Valor extraído",
        help_text=(
            "Valor a atribuir ao sinal quando a condição é satisfeita. "
            "Deve ser válido para o tipo do sinal."
        ),
    )
    peso = models.FloatField(
        default=1.0,
        verbose_name="Peso",
        help_text=(
            "Peso desta extração quando o sinal é agregado. "
            "1.0 = peso normal. Use < 1.0 para regras secundárias."
        ),
    )
    notas = models.TextField(
        blank=True,
        verbose_name="Notas",
        help_text="Justificativa da regra. Útil para revisão futura.",
    )

    class Meta:
        verbose_name = "Mapeamento de sinal"
        verbose_name_plural = "Mapeamentos de sinal"
        ordering: ClassVar[list[str]] = ["pergunta", "sinal"]
        indexes: ClassVar[list[models.Index]] = [
            models.Index(fields=["pergunta"]),
            models.Index(fields=["sinal"]),
        ]

    def __str__(self) -> str:
        return f"{self.pergunta.codigo} → {self.sinal.chave}={self.valor_extraido}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk and self.pergunta.ato.versao.is_immutable:
            raise ImmutableEntityModificationAttempt(
                "Não é possível modificar mapeamentos de uma versão imutável."
            )
        # Valida que valor_extraido está coerente com o tipo do sinal
        if self.sinal_id and not self.sinal.valor_eh_valido(self.valor_extraido):
            raise ValidationError(
                {
                    "valor_extraido": (
                        f"Valor {self.valor_extraido!r} não é válido para o sinal "
                        f"{self.sinal.chave} (tipo {self.sinal.get_tipo_valor_display()})."
                    )
                }
            )
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        if self.pergunta.ato.versao.is_immutable:
            raise ImmutableEntityModificationAttempt(
                "Não é possível excluir mapeamentos de uma versão imutável."
            )
        return super().delete(*args, **kwargs)

    def duplicate_to(self, nova_pergunta: Pergunta) -> MapeamentoDeSinal:
        return MapeamentoDeSinal.objects.create(
            pergunta=nova_pergunta,
            sinal=self.sinal,
            condicao=self.condicao,
            valor_extraido=self.valor_extraido,
            peso=self.peso,
            notas=self.notas,
        )

    def to_snapshot_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "sinal_chave": self.sinal.chave,
            "sinal_categoria": self.sinal.categoria,
            "sinal_tipo_valor": self.sinal.tipo_valor,
            "condicao": self.condicao,
            "valor_extraido": self.valor_extraido,
            "peso": self.peso,
        }
