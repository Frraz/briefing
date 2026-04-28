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
                └── Ato (acolhimento, calibracao, ...)
                        └── Pergunta (próxima entrega)

Estados de RoteiroVersao:
    draft     → editável
    published → imutável, é a versão "ativa" (no máximo 1 por identidade)
    archived  → imutável, foi published mas perdeu o lugar para nova versão
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any, ClassVar

from django.conf import settings
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
#  ENUMS — usar TextChoices para internacionalização e admin amigável
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
    """
    Slugs canônicos dos 7 atos da metodologia Ferzion.

    Estes slugs são contratos com o frontend — mudar aqui requer deploy
    coordenado. Por isso ficam como enum, não como texto livre.
    """

    ACOLHIMENTO = "acolhimento", "Acolhimento"
    CALIBRACAO = "calibracao", "Calibração"
    COMPREENSAO = "compreensao", "Compreensão do Negócio"
    DIAGNOSTICO = "diagnostico", "Diagnóstico Operacional"
    ASPIRACOES = "aspiracoes", "Aspirações e Visão"
    RESTRICOES = "restricoes", "Restrições e Realidade"
    SINTESE = "sintese", "Síntese e Devolutiva"
    PONTE = "ponte", "Ponte para o Painel"


# =============================================================================
#  ROTEIRO IDENTIDADE — a "alma" estável
# =============================================================================


class RoteiroIdentidade(BaseEntity):
    """
    A identidade estável de um roteiro de discovery.

    Esta entidade NÃO carrega conteúdo — ela apenas representa "o conceito
    do Roteiro Universal Ferzion". O conteúdo vive nas versões.

    Quando você quer apontar para "este roteiro" no longo prazo (ex: em
    relatórios cross-version), aponte para a Identidade. Quando precisar
    do conteúdo de um momento específico, aponte para a Versão.
    """

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
        """Auto-gera slug a partir do nome se não informado."""
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)

    # -------------------------------------------------------------------------
    #  API de domínio
    # -------------------------------------------------------------------------
    @property
    def versao_publicada(self) -> RoteiroVersao | None:
        """Retorna a única versão publicada (no máximo uma)."""
        return self.versoes.filter(status=StatusVersao.PUBLISHED).first()

    @property
    def versao_em_draft(self) -> RoteiroVersao | None:
        """Retorna a versão em draft (no máximo uma por identidade)."""
        return self.versoes.filter(status=StatusVersao.DRAFT).first()

    def proximo_numero_versao(self) -> int:
        """Calcula o próximo número de versão (max + 1)."""
        ultima = self.versoes.order_by("-version").first()
        return (ultima.version + 1) if ultima else 1


# =============================================================================
#  ROTEIRO VERSÃO — uma "fotografia" imutável após publicação
# =============================================================================


class RoteiroVersao(BaseEntity):
    """
    Uma versão concreta de uma RoteiroIdentidade.

    Estados:
        draft     → editável; conteúdo (atos, perguntas) pode ser modificado.
        published → imutável; é a versão ativa (1 por identidade no máximo).
        archived  → imutável; foi published mas perdeu lugar para versão mais nova.

    Briefings sempre apontam para uma RoteiroVersao específica (pinning).
    Isso garante que o cliente João, que respondeu a metodologia v3, sempre
    "veja" a v3 mesmo depois de v4 ser publicada.
    """

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

    # --- Metadados de publicação ---
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Publicada em",
    )
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="roteiros_publicados",
        verbose_name="Publicada por",
    )
    archived_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Arquivada em",
    )

    # --- Snapshot ---
    # JSON congelado da estrutura completa no momento da publicação.
    # Atos, perguntas, opções, sinais, insights, regras — tudo aqui.
    # Existe RELACIONALMENTE também (Atos como linhas), mas o snapshot é
    # a fonte de verdade histórica imutável.
    snapshot_json = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Snapshot",
        help_text="Estrutura completa congelada. Preenchido na publicação.",
    )

    # --- Notas livres do autor ---
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
            # Garantia de unicidade do par (identidade, versão)
            models.UniqueConstraint(
                fields=["identidade", "version"],
                name="uniq_identidade_versao",
            ),
            # Garantia: no máximo 1 versão DRAFT por identidade
            models.UniqueConstraint(
                fields=["identidade"],
                condition=models.Q(status="draft"),
                name="uniq_draft_por_identidade",
            ),
            # Garantia: no máximo 1 versão PUBLISHED por identidade
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

    # -------------------------------------------------------------------------
    #  Auto-gerenciamento da versão e proteção de imutabilidade
    # -------------------------------------------------------------------------
    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Hook de proteção de imutabilidade.

        Se a versão já está PUBLISHED ou ARCHIVED, somente alterações em
        campos de gerenciamento (status, archived_at) são permitidas.
        Tentar mudar conteúdo de uma versão imutável levanta exceção.
        """
        is_new = self._state.adding

        # Auto-numeração na criação
        if is_new and not self.version:
            self.version = self.identidade.proximo_numero_versao()

        # Bloqueio de edição em versões já publicadas/arquivadas
        if not is_new and self.pk:
            try:
                original = type(self).objects.get(pk=self.pk)
            except type(self).DoesNotExist:
                original = None

            if original and original.status in (
                StatusVersao.PUBLISHED,
                StatusVersao.ARCHIVED,
            ):
                # Permitir apenas mudança de status (publicar→arquivar, etc.)
                # e atualização dos timestamps de gerenciamento
                campos_protegidos = {"notas_da_versao", "snapshot_json"}
                update_fields = kwargs.get("update_fields") or set()

                if not update_fields:
                    # Save completo em entity imutável → comparar com original
                    if any(
                        getattr(self, f) != getattr(original, f)
                        for f in campos_protegidos
                    ):
                        raise ImmutableEntityModificationAttempt(
                            f"Versão v{self.version} está {original.get_status_display()} "
                            "e não pode ter conteúdo modificado. "
                            "Crie uma nova versão a partir desta."
                        )

        super().save(*args, **kwargs)

    # -------------------------------------------------------------------------
    #  API de domínio — transições de estado
    # -------------------------------------------------------------------------
    @property
    def is_editable(self) -> bool:
        """True se a versão pode ter atos/perguntas modificados."""
        return self.status == StatusVersao.DRAFT

    @property
    def is_immutable(self) -> bool:
        """True se a versão está congelada."""
        return self.status in (StatusVersao.PUBLISHED, StatusVersao.ARCHIVED)

    @transaction.atomic
    def publish(self, by_user: Any = None) -> None:
        """
        Publica esta versão.

        Efeitos:
            1. Valida invariantes (existe ao menos 1 ato com ao menos 1 pergunta).
            2. Arquiva a versão atualmente publicada (se houver).
            3. Gera snapshot_json com estado completo da estrutura.
            4. Transiciona status: draft → published.

        Raises:
            InvalidStateTransition: se versão não está em draft.
            InvariantViolation: se estrutura é insuficiente para publicação.
        """
        if self.status != StatusVersao.DRAFT:
            raise InvalidStateTransition(
                f"Apenas versões em rascunho podem ser publicadas. "
                f"Versão atual: {self.get_status_display()}."
            )

        self._validate_publishable()

        # Arquiva versão atualmente publicada na mesma identidade
        publicada_atual = self.identidade.versao_publicada
        if publicada_atual:
            publicada_atual.archive()

        # Gera snapshot — fonte de verdade histórica
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
        """Arquiva versão (chamada automaticamente quando outra é publicada)."""
        if self.status == StatusVersao.ARCHIVED:
            return  # idempotente
        if self.status == StatusVersao.DRAFT:
            raise InvalidStateTransition(
                "Versões em rascunho não devem ser arquivadas — apenas excluídas."
            )

        self.archived_at = timezone.now()
        self.status = StatusVersao.ARCHIVED
        self.save(update_fields=["status", "archived_at", "updated_at"])

    @transaction.atomic
    def create_next_draft(self) -> RoteiroVersao:
        """
        Cria uma nova versão DRAFT a partir desta.

        Duplica toda a estrutura (atos, perguntas, etc.) na nova versão,
        para que a Ferzion possa editar sem afetar a versão atual.

        Returns:
            A nova RoteiroVersao em status draft.

        Raises:
            InvariantViolation: se já existe um draft pendente nesta identidade.
        """
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
        # Duplica estrutura — atos serão duplicados; perguntas serão
        # adicionadas na próxima mensagem quando modelarmos Pergunta.
        for ato in self.atos.all():
            ato.duplicate_to(nova)

        return nova

    # -------------------------------------------------------------------------
    #  Validação e snapshot — internos
    # -------------------------------------------------------------------------
    def _validate_publishable(self) -> None:
        """Garante que a versão tem estrutura mínima para ser publicada."""
        atos_count = self.atos.count()
        if atos_count == 0:
            raise InvariantViolation(
                "Esta versão não tem nenhum ato. "
                "Adicione pelo menos um ato antes de publicar."
            )

        # Validações adicionais (perguntas por ato) virão quando
        # modelarmos Pergunta na próxima mensagem.

    def _build_snapshot(self) -> dict[str, Any]:
        """
        Constrói o snapshot JSON congelado.

        O snapshot replica a estrutura relacional como uma árvore JSON.
        Funciona como audit trail e como fonte para reconstrução exata
        do que o cliente viu, mesmo que a estrutura relacional evolua.
        """
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
#  ATO — uma seção narrativa do roteiro (Acolhimento, Calibração, etc.)
# =============================================================================


class Ato(BaseEntity):
    """
    Um ato do roteiro — uma "cena" narrativa.

    Pertence a uma RoteiroVersao. Carrega slug canônico (acolhimento,
    calibracao, ...) que é contrato com o frontend.

    Conteúdo público (titulo_publico, subtitulo_publico) é o que o cliente
    vê na tela. Conteúdo interno (descricao_interna) é nota da Ferzion.
    """

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
    ordem = models.PositiveSmallIntegerField(
        verbose_name="Ordem",
        help_text="Posição na sequência narrativa (0, 1, 2, ...).",
    )

    # --- Conteúdo público (cliente vê) ---
    titulo_publico = models.CharField(
        max_length=200,
        verbose_name="Título público",
        help_text="Aparece para o cliente. Tom Ferzion: humano, claro.",
    )
    subtitulo_publico = models.CharField(
        max_length=400,
        blank=True,
        verbose_name="Subtítulo público",
        help_text="Frase de apoio que aparece abaixo do título.",
    )
    introducao_publica = models.TextField(
        blank=True,
        verbose_name="Introdução pública",
        help_text="Texto introdutório longo (opcional). Markdown aceito.",
    )

    # --- Conteúdo interno (Ferzion vê) ---
    descricao_interna = models.TextField(
        blank=True,
        verbose_name="Descrição interna",
        help_text="Notas/objetivos internos do ato. Não aparece para o cliente.",
    )

    # --- Configuração comportamental ---
    obrigatorio = models.BooleanField(
        default=True,
        verbose_name="Obrigatório",
        help_text="Se desmarcado, este ato pode ser pulado por certos perfis.",
    )

    # --- Configuração avançada (preparada para o futuro) ---
    # JSON livre para configurações específicas do ato sem precisar
    # adicionar colunas no futuro. Exemplo: tempo estimado, exibir
    # progresso, animação de entrada específica, etc.
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
            # Garantia: dentro de uma versão, slug é único
            models.UniqueConstraint(
                fields=["versao", "slug"],
                name="uniq_ato_slug_por_versao",
            ),
            # Garantia: dentro de uma versão, ordem é única
            models.UniqueConstraint(
                fields=["versao", "ordem"],
                name="uniq_ato_ordem_por_versao",
            ),
        ]
        indexes: ClassVar[list[models.Index]] = [
            models.Index(fields=["versao", "ordem"]),
        ]

    def __str__(self) -> str:
        return f"{self.versao.identidade.nome} v{self.versao.version} · {self.get_slug_display()}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Bloqueia edição se a versão pai está imutável."""
        if self.pk:  # update, não create
            if self.versao.is_immutable:
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

    # -------------------------------------------------------------------------
    #  API de domínio
    # -------------------------------------------------------------------------
    def duplicate_to(self, nova_versao: RoteiroVersao) -> Ato:
        """
        Duplica este ato para uma nova versão (usado em create_next_draft).

        Quando modelarmos Pergunta, este método também duplicará as
        perguntas filhas. Por enquanto duplica só os campos do próprio ato.
        """
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
        # TODO (próxima mensagem): duplicar self.perguntas.all() para novo
        return novo

    def to_snapshot_dict(self) -> dict[str, Any]:
        """Serializa para o snapshot da versão pai."""
        return {
            "id": str(self.id),
            "slug": self.slug,
            "ordem": self.ordem,
            "titulo_publico": self.titulo_publico,
            "subtitulo_publico": self.subtitulo_publico,
            "introducao_publica": self.introducao_publica,
            "obrigatorio": self.obrigatorio,
            "configuracao": self.configuracao,
            # "perguntas": [p.to_snapshot_dict() for p in self.perguntas.order_by("ordem")],
        }
