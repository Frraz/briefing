"""Ferzion Discovery — Methodology / Admin / Insight."""

from __future__ import annotations

from typing import Any

from django.contrib import admin, messages
from django.http import HttpRequest

from apps.methodology.models import Insight

from ._helpers import severidade_badge, short_description


@admin.register(Insight)
class InsightAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "titulo_publico",
        "severidade_label",
        "categoria",
        "momento_disparo",
        "prioridade",
        "versao_label",
    )
    list_filter = (
        "versao__status",
        "severidade",
        "categoria",
        "momento_disparo",
    )
    search_fields = (
        "codigo",
        "titulo_publico",
        "texto_publico",
        "objetivo_interno",
    )
    ordering = ("versao", "categoria", "-prioridade")
    autocomplete_fields = ("versao", "ato_de_disparo")

    fieldsets = (
        (
            "Identificação",
            {"fields": ("versao", "codigo")},
        ),
        (
            "Conteúdo público (cliente vê)",
            {
                "fields": ("titulo_publico", "texto_publico"),
                "description": (
                    "Microcopy do insight. Pode usar variáveis: "
                    "{nome_empresa}, {valor_sinal:porte_operacional}, etc."
                ),
            },
        ),
        (
            "Classificação",
            {"fields": ("severidade", "categoria")},
        ),
        (
            "Disparo",
            {
                "fields": ("momento_disparo", "ato_de_disparo"),
                "description": (
                    "Para 'durante_ato' ou 'ambos', o ato precisa ser definido. "
                    "Para 'sintese_final', deixar ato em branco."
                ),
            },
        ),
        (
            "Condições e composição",
            {
                "fields": ("condicoes", "prioridade", "limite_simultaneos"),
                "description": (
                    "Condições baseadas em sinais. Prioridade 0-100 ordena "
                    "exibição. Limite simultâneo = 0 significa sem limite."
                ),
            },
        ),
        (
            "Objetivo interno",
            {"fields": ("objetivo_interno",)},
        ),
        (
            "Auditoria",
            {
                "classes": ("collapse",),
                "fields": ("id", "created_at", "updated_at"),
            },
        ),
    )
    readonly_fields = ("id", "created_at", "updated_at")

    # -------------------------------------------------------------------------
    #  Bloqueio em insight cuja versão é imutável
    # -------------------------------------------------------------------------
    def get_readonly_fields(
        self, request: HttpRequest, obj: Insight | None = None
    ) -> tuple[str, ...]:
        ro = list(super().get_readonly_fields(request, obj))
        if obj and obj.versao.is_immutable:
            for f in self.model._meta.get_fields():
                if f.concrete and not f.many_to_many and not f.auto_created and f.name not in ro:
                    ro.append(f.name)
        return tuple(ro)

    def has_delete_permission(self, request: HttpRequest, obj: Insight | None = None) -> bool:
        if obj and obj.versao.is_immutable:
            return False
        return super().has_delete_permission(request, obj)

    def render_change_form(
        self,
        request: HttpRequest,
        context: dict[str, Any],
        add: bool = False,
        change: bool = False,
        form_url: str = "",
        obj: Insight | None = None,
    ) -> Any:
        if obj and obj.versao.is_immutable:
            messages.warning(
                request,
                f"A versão deste insight ({obj.versao}) está "
                f"{obj.versao.get_status_display().upper()}. "
                "O conteúdo está congelado.",
            )
        return super().render_change_form(request, context, add, change, form_url, obj)

    @short_description("Severidade")
    def severidade_label(self, obj: Insight) -> Any:
        return severidade_badge(obj.severidade, obj.get_severidade_display())

    @short_description("Versão")
    def versao_label(self, obj: Insight) -> str:
        return f"{obj.versao.identidade.nome} v{obj.versao.version}"
