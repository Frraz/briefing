"""
Ferzion Discovery — Methodology / Admin / Roteiro.

Admins de RoteiroIdentidade e RoteiroVersao.

Recursos:
    - Botões de ação na listagem de versões (publicar, arquivar, criar nova).
    - Banner de imutabilidade no formulário de versões publicadas.
    - List displays com contagens de atos, perguntas, insights, regras.
    - Filtros laterais por status, tipo, identidade.
"""

from __future__ import annotations

from typing import Any

from django.contrib import admin, messages
from django.db.models import Count, QuerySet
from django.http import HttpRequest
from django.utils.html import format_html

from apps.methodology.models import (
    RoteiroIdentidade,
    RoteiroVersao,
)
from shared.exceptions import (
    ImmutableEntityModificationAttempt,
    InvalidStateTransition,
    InvariantViolation,
)

from ._helpers import (
    short_description,
    status_badge,
)

# =============================================================================
#  RoteiroIdentidade
# =============================================================================


@admin.register(RoteiroIdentidade)
class RoteiroIdentidadeAdmin(admin.ModelAdmin):
    list_display = (
        "nome",
        "tipo",
        "is_active",
        "total_versoes",
        "versao_atual_label",
    )
    list_filter = ("tipo", "is_active")
    search_fields = ("nome", "slug", "descricao_interna")
    prepopulated_fields = {"slug": ("nome",)}
    ordering = ("nome",)

    fieldsets = (
        (
            "Identificação",
            {
                "fields": ("nome", "slug", "tipo", "is_active"),
                "description": (
                    "Ao criar uma nova identidade, uma versão v1 em rascunho "
                    "é criada automaticamente para você popular."
                ),
            },
        ),
        ("Documentação", {"fields": ("descricao_interna",)}),
        (
            "Auditoria",
            {
                "classes": ("collapse",),
                "fields": ("id", "created_at", "updated_at"),
            },
        ),
    )
    readonly_fields = ("id", "created_at", "updated_at")

    def get_queryset(self, request: HttpRequest) -> QuerySet[RoteiroIdentidade]:
        return super().get_queryset(request).annotate(_total_versoes=Count("versoes"))

    @short_description("Versões")
    def total_versoes(self, obj: RoteiroIdentidade) -> int:
        return obj._total_versoes  # type: ignore[attr-defined]

    @short_description("Versão atual")
    def versao_atual_label(self, obj: RoteiroIdentidade) -> Any:
        publicada = obj.versao_publicada
        if publicada:
            return status_badge("published", f"v{publicada.version} publicada")
        em_draft = obj.versao_em_draft
        if em_draft:
            return status_badge("draft", f"v{em_draft.version} em rascunho")
        return format_html('<span style="color:#999;">sem versões</span>')


# =============================================================================
#  RoteiroVersao
# =============================================================================


@admin.register(RoteiroVersao)
class RoteiroVersaoAdmin(admin.ModelAdmin):
    list_display = (
        "__str__",
        "status_label",
        "version",
        "published_at",
        "contagem_resumo",
    )
    list_filter = ("status", "identidade__tipo", "identidade")
    search_fields = (
        "identidade__nome",
        "notas_da_versao",
    )
    ordering = ("-identidade__nome", "-version")
    autocomplete_fields = ("identidade",)
    actions = ("acao_publicar", "acao_arquivar", "acao_criar_proxima_versao")

    fieldsets = (
        (
            "Identificação",
            {
                "fields": ("identidade", "version", "status"),
            },
        ),
        (
            "Notas",
            {
                "fields": ("notas_da_versao",),
                "description": (
                    "Notas da versão são editáveis mesmo após publicação — "
                    "úteis para changelogs retroativos."
                ),
            },
        ),
        (
            "Publicação",
            {
                "classes": ("collapse",),
                "fields": ("published_at", "published_by", "archived_at"),
            },
        ),
        (
            "Snapshot (apenas leitura)",
            {
                "classes": ("collapse",),
                "fields": ("snapshot_json",),
                "description": (
                    "Estrutura completa congelada da versão. Gerada na "
                    "publicação, nunca editada manualmente."
                ),
            },
        ),
        (
            "Auditoria",
            {
                "classes": ("collapse",),
                "fields": ("id", "created_at", "updated_at"),
            },
        ),
    )

    readonly_fields = (
        "id",
        "version",
        "published_at",
        "published_by",
        "archived_at",
        "snapshot_json",
        "created_at",
        "updated_at",
    )

    # -------------------------------------------------------------------------
    #  Bloqueio total de edição em versões imutáveis
    # -------------------------------------------------------------------------
    def get_readonly_fields(
        self, request: HttpRequest, obj: RoteiroVersao | None = None
    ) -> tuple[str, ...]:
        ro = list(super().get_readonly_fields(request, obj))
        if obj and obj.is_immutable:
            # Em versão imutável, status, notas e identidade também viram readonly
            for f in ("status", "notas_da_versao", "identidade"):
                if f not in ro:
                    ro.append(f)
        return tuple(ro)

    def has_delete_permission(self, request: HttpRequest, obj: RoteiroVersao | None = None) -> bool:
        # Só permite excluir versões em DRAFT
        if obj and obj.is_immutable:
            return False
        return super().has_delete_permission(request, obj)

    def render_change_form(
        self,
        request: HttpRequest,
        context: dict[str, Any],
        add: bool = False,
        change: bool = False,
        form_url: str = "",
        obj: RoteiroVersao | None = None,
    ) -> Any:
        """Adiciona banner informativo no formulário."""
        if obj and obj.is_immutable:
            mensagem = (
                f"Esta versão está {obj.get_status_display().upper()}. "
                "O conteúdo está congelado e não pode ser modificado. "
                "Para evoluir a metodologia, use a ação "
                "'Criar próxima versão' a partir desta."
            )
            messages.warning(request, mensagem)
        return super().render_change_form(request, context, add, change, form_url, obj)

    # -------------------------------------------------------------------------
    #  Listagem
    # -------------------------------------------------------------------------
    @short_description("Status")
    def status_label(self, obj: RoteiroVersao) -> Any:
        return status_badge(obj.status, obj.get_status_display())

    @short_description("Conteúdo")
    def contagem_resumo(self, obj: RoteiroVersao) -> Any:
        atos_count = obj.atos.count()
        perguntas_count = sum(a.perguntas.count() for a in obj.atos.all())
        insights_count = obj.insights.count()
        regras_count = obj.regras_de_sintese.count()

        return format_html(
            '<span style="color:#444; font-size:11px;">'
            "<strong>{}</strong> atos · "
            "<strong>{}</strong> perguntas · "
            "<strong>{}</strong> insights · "
            "<strong>{}</strong> regras"
            "</span>",
            atos_count,
            perguntas_count,
            insights_count,
            regras_count,
        )

    # -------------------------------------------------------------------------
    #  Ações em massa
    # -------------------------------------------------------------------------
    @admin.action(description="Publicar versões selecionadas (apenas drafts)")
    def acao_publicar(
        self,
        request: HttpRequest,
        queryset: QuerySet[RoteiroVersao],
    ) -> None:
        sucessos = 0
        for versao in queryset:
            try:
                versao.publish(by_user=request.user)
                sucessos += 1
            except (InvalidStateTransition, InvariantViolation) as exc:
                self.message_user(
                    request,
                    f"v{versao.version} de {versao.identidade.nome}: {exc}",
                    level=messages.WARNING,
                )
        if sucessos:
            self.message_user(
                request,
                f"{sucessos} versão(ões) publicada(s) com sucesso.",
                level=messages.SUCCESS,
            )

    @admin.action(description="Arquivar versões selecionadas")
    def acao_arquivar(
        self,
        request: HttpRequest,
        queryset: QuerySet[RoteiroVersao],
    ) -> None:
        sucessos = 0
        for versao in queryset:
            try:
                versao.archive()
                sucessos += 1
            except InvalidStateTransition as exc:
                self.message_user(
                    request,
                    f"v{versao.version} de {versao.identidade.nome}: {exc}",
                    level=messages.WARNING,
                )
        if sucessos:
            self.message_user(
                request,
                f"{sucessos} versão(ões) arquivada(s) com sucesso.",
                level=messages.SUCCESS,
            )

    @admin.action(description="Criar próxima versão (rascunho derivado)")
    def acao_criar_proxima_versao(
        self,
        request: HttpRequest,
        queryset: QuerySet[RoteiroVersao],
    ) -> None:
        sucessos = 0
        for versao in queryset:
            try:
                nova = versao.create_next_draft()
                sucessos += 1
                self.message_user(
                    request,
                    f"Criada {nova} a partir de v{versao.version}.",
                    level=messages.SUCCESS,
                )
            except (InvariantViolation, ImmutableEntityModificationAttempt) as exc:
                self.message_user(
                    request,
                    f"v{versao.version} de {versao.identidade.nome}: {exc}",
                    level=messages.WARNING,
                )
        if sucessos == 0:
            self.message_user(
                request,
                "Nenhuma versão criada.",
                level=messages.WARNING,
            )
