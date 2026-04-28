"""
Ferzion Discovery — Methodology / Models (V4).

★ Coração do sistema ★

Modelagem completa da metodologia versionada de discovery da Ferzion.
Padrão: Aggregate Root + Snapshots Imutáveis.
Ver docs/architecture/decisions/0003-versionamento-append-only.md

Hierarquia:
    RoteiroIdentidade (alma — UUID estável)
        └── RoteiroVersao (fotografia — draft / published / archived)
                ├── Ato
                │       └── Pergunta
                │               ├── OpcaoDePergunta
                │               ├── MapeamentoDeSinal → CatalogoSinal
                │               └── FraseDevolutiva
                ├── Insight (insights ao vivo + síntese)
                └── RegraDeSintese (composição da devolutiva)

CatalogoSinal vive global (não versionado por roteiro) — vocabulário
compartilhado entre roteiros e mantido com cuidado.
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
    DRAFT = "draft", "Rascunho"
    PUBLISHED = "published", "Publicada"
    ARCHIVED = "archived", "Arquivada"


class SlugAto(models.TextChoices):
    ACOLHIMENTO = "acolhimento", "Acolhimento"
    CALIBRACAO = "calibracao", "Calibração"
    COMPREENSAO = "compreensao", "Compreensão do Negócio"
    DIAGNOSTICO = "diagnostico", "Diagnóstico Operacional"
    ASPIRACOES = "aspiracoes", "Aspirações e Visão"
    RESTRICOES = "restricoes", "Restrições e Realidade"
    SINTESE = "sintese", "Síntese e Devolutiva"
    PONTE = "ponte", "Ponte para o Painel"


class TipoPergunta(models.TextChoices):
    # MVP
    TEXTO_CURTO = "texto_curto", "Texto curto (1 linha)"
    TEXTO_LONGO = "texto_longo", "Texto longo (várias linhas)"
    ESCOLHA_UNICA = "escolha_unica", "Escolha única (radio)"
    ESCOLHA_MULTIPLA = "escolha_multipla", "Escolha múltipla (checkboxes)"
    ESCALA = "escala", "Escala (1-N)"
    ESCOLHA_UNICA_COM_OUTRO = "escolha_unica_com_outro", "Escolha única + 'Outro'"
    # Reservados para futuro
    UPLOAD = "upload", "Upload de arquivo (futuro)"
    RANKING = "ranking", "Ranking / ordenação (futuro)"
    MATRIZ = "matriz", "Matriz visual (futuro)"
    CONDICIONAL = "condicional", "Condicional avançada (futuro)"
    CONVERSACIONAL = "conversacional", "Bloco conversacional (futuro)"
    AUDIO = "audio", "Áudio / voz (futuro)"


class PerfilProfundidade(models.TextChoices):
    LIGHT = "light", "Light"
    STANDARD = "standard", "Standard"
    DEEP = "deep", "Deep"
    ENTERPRISE = "enterprise", "Enterprise"


class TipoValorSinal(models.TextChoices):
    CATEGORICO = "categorico", "Categórico"
    ESCALA = "escala", "Escala numérica"
    BOOLEANO = "booleano", "Booleano"
    NUMERICO = "numerico", "Numérico livre"
    TEXTO = "texto", "Texto preservado"


class CategoriaSinal(models.TextChoices):
    PERFIL = "perfil", "Perfil do cliente"
    NEGOCIO = "negocio", "Modelo de negócio"
    OPERACAO = "operacao", "Operação"
    DOR = "dor", "Dor / risco"
    ASPIRACAO = "aspiracao", "Aspiração / visão"
    RESTRICAO = "restricao", "Restrição"
    META = "meta", "Meta-sinal (calibração interna)"


class Arquetipo(models.TextChoices):
    CALIBRADORA = "calibradora", "Calibradora"
    REVELADORA = "reveladora", "Reveladora"
    MAPEADORA = "mapeadora", "Mapeadora"
    CONFRONTADORA = "confrontadora", "Confrontadora"


class FaixaDevolutiva(models.TextChoices):
    BAIXO = "baixo", "Baixo"
    MEDIO = "medio", "Médio"
    ALTO = "alto", "Alto"


class SeveridadeInsight(models.TextChoices):
    INFO = "info", "Informativo"
    ATENCAO = "atencao", "Atenção"
    CRITICO = "critico", "Crítico"
    POSITIVO = "positivo", "Positivo"


class CategoriaInsight(models.TextChoices):
    GOVERNANCA = "governanca", "Governança"
    OPERACIONAL = "operacional", "Operacional"
    COMERCIAL = "comercial", "Comercial"
    FINANCEIRO = "financeiro", "Financeiro"
    TECNOLOGICO = "tecnologico", "Tecnológico"
    HUMANO = "humano", "Pessoas / RH"
    ESTRATEGICO = "estrategico", "Estratégico"


class MomentoDisparoInsight(models.TextChoices):
    DURANTE_ATO = "durante_ato", "Durante um ato (ao vivo)"
    SINTESE_FINAL = "sintese_final", "Apenas no Ato 6"
    AMBOS = "ambos", "Durante ato e na síntese"


class TipoRegraDeSintese(models.TextChoices):
    FRASE_SINTESE = "frase_sintese", "Frase-síntese principal"
    SCORE_MATURIDADE = "score_maturidade", "Score de maturidade digital"
    OPORTUNIDADE = "oportunidade", "Oportunidade identificada"
    PROXIMO_PASSO = "proximo_passo", "Próximo passo recomendado"
    MODULO_SUGERIDO = "modulo_sugerido", "Módulo de sistema sugerido"
    RISCO_OPERACIONAL = "risco_operacional", "Risco operacional"


# =============================================================================
#  ROTEIRO IDENTIDADE
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
#  ROTEIRO VERSÃO
# =============================================================================


class RoteiroVersao(BaseEntity):
    """Uma versão concreta de uma RoteiroIdentidade."""

    identidade = models.ForeignKey(
        RoteiroIdentidade,
        on_delete=models.PROTECT,
        related_name="versoes",
        verbose_name="Identidade",
    )
    version = models.PositiveIntegerField(verbose_name="Número da versão")
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
        help_text="Changelog / notas internas.",
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

        # Duplica atos (que duplicam perguntas, opções, mapeamentos, frases)
        ato_map: dict[str, Ato] = {}
        for ato in self.atos.order_by("ordem"):
            novo_ato = ato.duplicate_to(nova)
            ato_map[ato.slug] = novo_ato

        # Duplica insights (com remapeamento de ato_de_disparo)
        for insight in self.insights.all():
            insight.duplicate_to(nova, ato_map=ato_map)

        # Duplica regras de síntese
        for regra in self.regras_de_sintese.all():
            regra.duplicate_to(nova)

        return nova

    def _validate_publishable(self) -> None:
        if self.atos.count() == 0:
            raise InvariantViolation(
                "Esta versão não tem nenhum ato. Adicione pelo menos um ato antes de publicar."
            )
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
            "insights": [
                ins.to_snapshot_dict() for ins in self.insights.order_by("categoria", "-prioridade")
            ],
            "regras_de_sintese": [
                regra.to_snapshot_dict()
                for regra in self.regras_de_sintese.order_by("tipo", "-prioridade")
            ],
            "snapshot_built_at": timezone.now().isoformat(),
        }


# =============================================================================
#  ATO
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
    )
    ordem = models.PositiveSmallIntegerField(verbose_name="Ordem")
    titulo_publico = models.CharField(max_length=200, verbose_name="Título público")
    subtitulo_publico = models.CharField(
        max_length=400, blank=True, verbose_name="Subtítulo público"
    )
    introducao_publica = models.TextField(blank=True, verbose_name="Introdução pública")
    descricao_interna = models.TextField(blank=True, verbose_name="Descrição interna")
    obrigatorio = models.BooleanField(default=True, verbose_name="Obrigatório")
    configuracao = models.JSONField(default=dict, blank=True, verbose_name="Configuração")

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
                f"{self.versao.get_status_display().lower()}."
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
#  PERGUNTA
# =============================================================================


class Pergunta(BaseEntity):
    """Uma pergunta dentro de um ato."""

    ato = models.ForeignKey(
        Ato,
        on_delete=models.CASCADE,
        related_name="perguntas",
        verbose_name="Ato",
    )
    codigo = models.CharField(max_length=16, verbose_name="Código")
    ordem = models.PositiveSmallIntegerField(verbose_name="Ordem")
    tipo = models.CharField(
        max_length=32,
        choices=TipoPergunta.choices,
        verbose_name="Tipo de pergunta",
    )
    arquetipo = models.CharField(
        max_length=24,
        choices=Arquetipo.choices,
        default=Arquetipo.CALIBRADORA,
        verbose_name="Arquétipo",
        help_text=(
            "Função metodológica: Calibradora (classifica), Reveladora (texto livre), "
            "Mapeadora (múltiplas marcações), Confrontadora (gera consciência)."
        ),
    )
    texto_publico = models.TextField(verbose_name="Texto público")
    placeholder = models.CharField(max_length=300, blank=True, verbose_name="Placeholder")
    helper_text = models.CharField(max_length=300, blank=True, verbose_name="Texto de ajuda")
    objetivo_interno = models.TextField(blank=True, verbose_name="Objetivo interno")
    obrigatoria = models.BooleanField(default=True, verbose_name="Obrigatória")
    perfis_minimos = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Perfis mínimos",
        help_text="Lista de perfis nos quais a pergunta aparece. Vazio = todos.",
    )
    precondicoes = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Pré-condições",
    )
    tipo_config = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Configuração do tipo",
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
            models.Index(fields=["arquetipo"]),
        ]

    def __str__(self) -> str:
        return f"{self.codigo} · {self.texto_publico[:60]}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk and self.ato.versao.is_immutable:
            raise ImmutableEntityModificationAttempt(
                f"Não é possível modificar perguntas de uma versão "
                f"{self.ato.versao.get_status_display().lower()}."
            )
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        if self.ato.versao.is_immutable:
            raise ImmutableEntityModificationAttempt(
                f"Não é possível excluir perguntas de uma versão "
                f"{self.ato.versao.get_status_display().lower()}."
            )
        return super().delete(*args, **kwargs)

    def clean(self) -> None:
        super().clean()
        config = self.tipo_config or {}

        if self.tipo in (TipoPergunta.TEXTO_CURTO, TipoPergunta.TEXTO_LONGO):
            if "max_chars" in config and not isinstance(config["max_chars"], int):
                raise ValidationError({"tipo_config": "max_chars deve ser inteiro."})

        elif self.tipo in (
            TipoPergunta.ESCOLHA_UNICA,
            TipoPergunta.ESCOLHA_MULTIPLA,
            TipoPergunta.ESCOLHA_UNICA_COM_OUTRO,
        ):
            if self.tipo == TipoPergunta.ESCOLHA_MULTIPLA:
                if "min_selecoes" in config:
                    if not isinstance(config["min_selecoes"], int):
                        raise ValidationError({"tipo_config": "min_selecoes deve ser inteiro."})

        elif self.tipo == TipoPergunta.ESCALA:
            if "min" not in config or "max" not in config:
                raise ValidationError({"tipo_config": "Escala exige 'min' e 'max' em tipo_config."})
            if not (isinstance(config["min"], int) and isinstance(config["max"], int)):
                raise ValidationError({"tipo_config": "min e max devem ser inteiros."})
            if config["min"] >= config["max"]:
                raise ValidationError({"tipo_config": "min deve ser menor que max."})

    @property
    def requer_opcoes(self) -> bool:
        return self.tipo in (
            TipoPergunta.ESCOLHA_UNICA,
            TipoPergunta.ESCOLHA_MULTIPLA,
            TipoPergunta.ESCOLHA_UNICA_COM_OUTRO,
        )

    def duplicate_to(self, novo_ato: Ato) -> Pergunta:
        nova = Pergunta.objects.create(
            ato=novo_ato,
            codigo=self.codigo,
            ordem=self.ordem,
            tipo=self.tipo,
            arquetipo=self.arquetipo,
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
        for frase in self.frases_devolutiva.all():
            frase.duplicate_to(nova)
        return nova

    def to_snapshot_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "codigo": self.codigo,
            "ordem": self.ordem,
            "tipo": self.tipo,
            "arquetipo": self.arquetipo,
            "texto_publico": self.texto_publico,
            "placeholder": self.placeholder,
            "helper_text": self.helper_text,
            "obrigatoria": self.obrigatoria,
            "perfis_minimos": self.perfis_minimos,
            "precondicoes": self.precondicoes,
            "tipo_config": self.tipo_config,
            "opcoes": [opcao.to_snapshot_dict() for opcao in self.opcoes.order_by("ordem")],
            "mapeamentos": [m.to_snapshot_dict() for m in self.mapeamentos.all()],
            "frases_devolutiva": [f.to_snapshot_dict() for f in self.frases_devolutiva.all()],
        }


# =============================================================================
#  OPÇÃO DE PERGUNTA
# =============================================================================


class OpcaoDePergunta(BaseEntity):
    """Uma alternativa de resposta para perguntas de escolha."""

    pergunta = models.ForeignKey(
        Pergunta,
        on_delete=models.CASCADE,
        related_name="opcoes",
        verbose_name="Pergunta",
    )
    codigo_interno = models.CharField(
        max_length=64,
        verbose_name="Código interno",
        help_text="Identificador estável da opção (ex: 'porte_micro').",
    )
    ordem = models.PositiveSmallIntegerField(verbose_name="Ordem")
    texto_publico = models.CharField(max_length=300, verbose_name="Texto público")
    descricao_publica = models.CharField(
        max_length=400, blank=True, verbose_name="Descrição pública"
    )
    icone = models.CharField(max_length=64, blank=True, verbose_name="Ícone")

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
#  CATÁLOGO DE SINAIS
# =============================================================================


class CatalogoSinal(BaseEntity):
    """Definição global de um sinal. NÃO é versionado por roteiro."""

    chave = models.SlugField(
        max_length=80,
        unique=True,
        verbose_name="Chave",
        help_text="Identificador snake_case do sinal.",
    )
    nome = models.CharField(max_length=160, verbose_name="Nome")
    descricao = models.TextField(verbose_name="Descrição")
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
    )
    notas_internas = models.TextField(blank=True, verbose_name="Notas internas")

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
#  MAPEAMENTO DE SINAL
# =============================================================================


class MapeamentoDeSinal(BaseEntity):
    """Regra de extração: dada uma resposta a uma pergunta, qual sinal é capturado."""

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
    condicao = models.JSONField(verbose_name="Condição")
    valor_extraido = models.JSONField(verbose_name="Valor extraído")
    peso = models.FloatField(default=1.0, verbose_name="Peso")
    notas = models.TextField(blank=True, verbose_name="Notas")

    class Meta:
        verbose_name = "Mapeamento de sinal"
        verbose_name_plural = "Mapeamentos de sinal"
        ordering: ClassVar[list[str]] = ["pergunta", "sinal"]
        constraints: ClassVar[list[Any]] = [
            models.UniqueConstraint(
                fields=["pergunta", "sinal", "valor_extraido"],
                name="uniq_mapeamento_pergunta_sinal_valor",
            ),
        ]
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


# =============================================================================
#  INSIGHT — pedaço de inteligência consultiva
# =============================================================================


class Insight(BaseEntity):
    """
    Um pedaço de inteligência consultiva disparado por sinais.

    Aparece em dois momentos:
        1. Durante um ato (Ato 3 principalmente) — "ao vivo"
        2. Na síntese final (Ato 6) — composição da devolutiva
    """

    versao = models.ForeignKey(
        RoteiroVersao,
        on_delete=models.CASCADE,
        related_name="insights",
        verbose_name="Versão do roteiro",
    )
    codigo = models.SlugField(
        max_length=80,
        verbose_name="Código",
        help_text="Identificador snake_case dentro da versão.",
    )
    titulo_publico = models.CharField(
        max_length=200,
        verbose_name="Título público",
        help_text="Título curto que aparece no card de insight.",
    )
    texto_publico = models.TextField(
        verbose_name="Texto público",
        help_text=(
            "Mensagem do insight. Tom Ferzion. "
            "Pode usar {nome_empresa} ou {valor_sinal:porte_operacional}."
        ),
    )
    severidade = models.CharField(
        max_length=16,
        choices=SeveridadeInsight.choices,
        default=SeveridadeInsight.INFO,
        verbose_name="Severidade",
    )
    categoria = models.CharField(
        max_length=24,
        choices=CategoriaInsight.choices,
        default=CategoriaInsight.OPERACIONAL,
        verbose_name="Categoria",
    )
    momento_disparo = models.CharField(
        max_length=16,
        choices=MomentoDisparoInsight.choices,
        default=MomentoDisparoInsight.AMBOS,
        verbose_name="Momento de disparo",
    )
    ato_de_disparo = models.ForeignKey(
        Ato,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="insights_ao_vivo",
        verbose_name="Ato (para disparo ao vivo)",
        help_text=("Se o momento permite ao vivo, em qual ato disparar?"),
    )
    condicoes = models.JSONField(
        default=dict,
        verbose_name="Condições de disparo",
        help_text='Ex: {"operador": "and", "clausulas": [...]}.',
    )
    prioridade = models.PositiveSmallIntegerField(
        default=50,
        verbose_name="Prioridade",
        help_text="0-100. Maior = aparece primeiro quando vários disparam.",
    )
    limite_simultaneos = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Limite simultâneo",
        help_text="0 = sem limite.",
    )
    objetivo_interno = models.TextField(
        blank=True,
        verbose_name="Objetivo interno",
    )

    class Meta:
        verbose_name = "Insight"
        verbose_name_plural = "Insights"
        ordering: ClassVar[list[str]] = ["versao", "categoria", "-prioridade"]
        constraints: ClassVar[list[Any]] = [
            models.UniqueConstraint(
                fields=["versao", "codigo"],
                name="uniq_insight_codigo_por_versao",
            ),
        ]
        indexes: ClassVar[list[models.Index]] = [
            models.Index(fields=["versao", "categoria"]),
            models.Index(fields=["versao", "momento_disparo"]),
            models.Index(fields=["severidade"]),
        ]

    def __str__(self) -> str:
        return f"[{self.get_severidade_display()}] {self.titulo_publico[:60]}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk and self.versao.is_immutable:
            raise ImmutableEntityModificationAttempt(
                f"Não é possível modificar insights de uma versão "
                f"{self.versao.get_status_display().lower()}."
            )
        if (
            self.momento_disparo
            in (
                MomentoDisparoInsight.DURANTE_ATO,
                MomentoDisparoInsight.AMBOS,
            )
            and not self.ato_de_disparo_id
        ):
            raise ValidationError(
                {"ato_de_disparo": ("Para disparo durante um ato, o ato precisa ser definido.")}
            )
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        if self.versao.is_immutable:
            raise ImmutableEntityModificationAttempt(
                f"Não é possível excluir insights de uma versão "
                f"{self.versao.get_status_display().lower()}."
            )
        return super().delete(*args, **kwargs)

    def duplicate_to(
        self,
        nova_versao: RoteiroVersao,
        ato_map: dict[str, Ato] | None = None,
    ) -> Insight:
        novo_ato = None
        if self.ato_de_disparo_id and ato_map:
            novo_ato = ato_map.get(self.ato_de_disparo.slug)

        return Insight.objects.create(
            versao=nova_versao,
            codigo=self.codigo,
            titulo_publico=self.titulo_publico,
            texto_publico=self.texto_publico,
            severidade=self.severidade,
            categoria=self.categoria,
            momento_disparo=self.momento_disparo,
            ato_de_disparo=novo_ato,
            condicoes=self.condicoes,
            prioridade=self.prioridade,
            limite_simultaneos=self.limite_simultaneos,
            objetivo_interno=self.objetivo_interno,
        )

    def to_snapshot_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "codigo": self.codigo,
            "titulo_publico": self.titulo_publico,
            "texto_publico": self.texto_publico,
            "severidade": self.severidade,
            "categoria": self.categoria,
            "momento_disparo": self.momento_disparo,
            "ato_de_disparo_slug": (self.ato_de_disparo.slug if self.ato_de_disparo else None),
            "condicoes": self.condicoes,
            "prioridade": self.prioridade,
            "limite_simultaneos": self.limite_simultaneos,
        }


# =============================================================================
#  REGRA DE SÍNTESE — composição da devolutiva (Ato 6)
# =============================================================================


class RegraDeSintese(BaseEntity):
    """
    Uma regra que compõe a devolutiva do Ato 6.

    A devolutiva é uma COMPOSIÇÃO de blocos com tipos diferentes
    (frase-síntese, score, oportunidades, próximos passos, módulos, riscos).
    """

    versao = models.ForeignKey(
        RoteiroVersao,
        on_delete=models.CASCADE,
        related_name="regras_de_sintese",
        verbose_name="Versão do roteiro",
    )
    codigo = models.SlugField(max_length=80, verbose_name="Código")
    tipo = models.CharField(
        max_length=24,
        choices=TipoRegraDeSintese.choices,
        verbose_name="Tipo",
    )
    titulo_interno = models.CharField(
        max_length=160,
        verbose_name="Título interno",
        help_text="Como aparece no admin.",
    )
    template = models.TextField(
        verbose_name="Template",
        help_text=(
            "Texto renderizado quando a regra é aplicada. Aceita variáveis no formato {variavel}."
        ),
    )
    condicoes = models.JSONField(
        default=dict,
        verbose_name="Condições de aplicação",
    )
    prioridade = models.PositiveSmallIntegerField(
        default=50,
        verbose_name="Prioridade",
    )
    perfis_aplicaveis = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Perfis aplicáveis",
        help_text="Vazio = todos os perfis.",
    )
    impacto_estimado = models.CharField(
        max_length=32,
        blank=True,
        verbose_name="Impacto estimado",
        help_text="Para regras de oportunidade. Ex: 'alto', 'medio', 'baixo'.",
    )
    modulo_sugerido_codigo = models.SlugField(
        max_length=80,
        blank=True,
        verbose_name="Código de módulo sugerido",
        help_text="Para regras de oportunidade ou módulo. Ex: 'crm_basico'.",
    )
    notas_internas = models.TextField(blank=True, verbose_name="Notas internas")

    class Meta:
        verbose_name = "Regra de síntese"
        verbose_name_plural = "Regras de síntese"
        ordering: ClassVar[list[str]] = ["versao", "tipo", "-prioridade"]
        constraints: ClassVar[list[Any]] = [
            models.UniqueConstraint(
                fields=["versao", "codigo"],
                name="uniq_regra_codigo_por_versao",
            ),
        ]
        indexes: ClassVar[list[models.Index]] = [
            models.Index(fields=["versao", "tipo"]),
        ]

    def __str__(self) -> str:
        return f"[{self.get_tipo_display()}] {self.titulo_interno}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk and self.versao.is_immutable:
            raise ImmutableEntityModificationAttempt(
                f"Não é possível modificar regras de uma versão "
                f"{self.versao.get_status_display().lower()}."
            )
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        if self.versao.is_immutable:
            raise ImmutableEntityModificationAttempt(
                f"Não é possível excluir regras de uma versão "
                f"{self.versao.get_status_display().lower()}."
            )
        return super().delete(*args, **kwargs)

    def duplicate_to(self, nova_versao: RoteiroVersao) -> RegraDeSintese:
        return RegraDeSintese.objects.create(
            versao=nova_versao,
            codigo=self.codigo,
            tipo=self.tipo,
            titulo_interno=self.titulo_interno,
            template=self.template,
            condicoes=self.condicoes,
            prioridade=self.prioridade,
            perfis_aplicaveis=self.perfis_aplicaveis,
            impacto_estimado=self.impacto_estimado,
            modulo_sugerido_codigo=self.modulo_sugerido_codigo,
            notas_internas=self.notas_internas,
        )

    def to_snapshot_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "codigo": self.codigo,
            "tipo": self.tipo,
            "titulo_interno": self.titulo_interno,
            "template": self.template,
            "condicoes": self.condicoes,
            "prioridade": self.prioridade,
            "perfis_aplicaveis": self.perfis_aplicaveis,
            "impacto_estimado": self.impacto_estimado,
            "modulo_sugerido_codigo": self.modulo_sugerido_codigo,
        }


# =============================================================================
#  FRASE DE DEVOLUTIVA — texto da síntese por faixa de sinal
# =============================================================================


class FraseDevolutiva(BaseEntity):
    """
    Texto que aparece na devolutiva (Ato 6) conforme o valor do sinal-alvo
    da pergunta. Uma frase por faixa (baixo/médio/alto).

    Existe vinculada à Pergunta para preservar o "teste das 3 frases" do
    framework metodológico — se uma pergunta não tem as 3, sinal está raso.
    """

    pergunta = models.ForeignKey(
        Pergunta,
        on_delete=models.CASCADE,
        related_name="frases_devolutiva",
        verbose_name="Pergunta",
    )
    faixa = models.CharField(
        max_length=8,
        choices=FaixaDevolutiva.choices,
        verbose_name="Faixa",
    )
    texto = models.TextField(
        verbose_name="Texto",
        help_text="Frase exibida na devolutiva quando o sinal cair nesta faixa.",
    )

    class Meta:
        verbose_name = "Frase de devolutiva"
        verbose_name_plural = "Frases de devolutiva"
        ordering: ClassVar[list[str]] = ["pergunta", "faixa"]
        constraints: ClassVar[list[Any]] = [
            models.UniqueConstraint(
                fields=["pergunta", "faixa"],
                name="uniq_frase_faixa_por_pergunta",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.pergunta.codigo} [{self.get_faixa_display()}]"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk and self.pergunta.ato.versao.is_immutable:
            raise ImmutableEntityModificationAttempt(
                "Não é possível modificar frases de uma versão imutável."
            )
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        if self.pergunta.ato.versao.is_immutable:
            raise ImmutableEntityModificationAttempt(
                "Não é possível excluir frases de uma versão imutável."
            )
        return super().delete(*args, **kwargs)

    def duplicate_to(self, nova_pergunta: Pergunta) -> FraseDevolutiva:
        return FraseDevolutiva.objects.create(
            pergunta=nova_pergunta,
            faixa=self.faixa,
            texto=self.texto,
        )

    def to_snapshot_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "faixa": self.faixa,
            "texto": self.texto,
        }
