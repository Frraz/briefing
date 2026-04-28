"""
Ferzion Discovery — Methodology / Admin / Ato.

Admin de Ato com listagem de perguntas inline.
"""

from __future__ import annotations

from typing import Any

from django.contrib import admin, messages
from django.http import HttpRequest
from django.utils.html import format_html

from apps.methodology.models import Ato, Pergunta

from ._helpers import short_description


class PerguntaInline(admin.TabularInline):
    """
    Listagem inline de perguntas dentro de um ato.

    Inline tabular (compacto) — para edição completa de uma pergunta,
    o usuário clica no link da pergunta e vai para o admin dedicado.
    """

    model = Pergunta
    extra = 0
    fields = (
        "ordem",
        "codigo",
        "tipo",
        "texto_publico",
        "obrigatoria",
    )
    show_change_link = True
    ordering = ("ordem",)

    def has_add_permission(self, request: HttpRequest, obj: Ato | None = None) -> bool:
        if obj and obj.versao.is_immutable:
            return False
        return super().has_add_permission(request, obj)

    def has_delete_permission(self, request: HttpRequest, obj: Ato | None = None) -> bool:
        if obj and obj.versao.is_immutable:
            return False
        return super().has_delete_permission(request, obj)


@admin.register(Ato)
class AtoAdmin(admin.ModelAdmin):
    list_display = (
        "__str__",
        "versao_status",
        "ordem",
        "perguntas_count",
        "obrigatorio",
    )
    list_filter = (
        "versao__status",
        "slug",
        "versao__identidade",
    )
    search_fields = (
        "titulo_publico",
        "subtitulo_publico",
        "descricao_interna",
        "versao__identidade__nome",
    )
    ordering = ("versao", "ordem")
    autocomplete_fields = ("versao",)

    inlines = (PerguntaInline,)

    fieldsets = (
        (
            "Identificação",
            {"fields": ("versao", "slug", "ordem", "obrigatorio")},
        ),
        (
            "Conteúdo público (cliente vê)",
            {
                "fields": (
                    "titulo_publico",
                    "subtitulo_publico",
                    "introducao_publica",
                ),
                "description": "Tom Ferzion: humano, claro, sem corporativês.",
            },
        ),
        (
            "Notas internas",
            {"fields": ("descricao_interna",)},
        ),
        (
            "Configuração avançada",
            {
                "classes": ("collapse",),
                "fields": ("configuracao",),
                "description": (
                    "JSON livre para configurações específicas do ato. "
                    "Ex: {'tempo_estimado_minutos': 5}."
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
    readonly_fields = ("id", "created_at", "updated_at")

    # -------------------------------------------------------------------------
    #  Bloqueio em ato cuja versão é imutável
    # -------------------------------------------------------------------------
    def get_readonly_fields(self, request: HttpRequest, obj: Ato | None = None) -> tuple[str, ...]:
        ro = list(super().get_readonly_fields(request, obj))
        if obj and obj.versao.is_immutable:
            for f in self.model._meta.get_fields():
                if f.concrete and not f.many_to_many and not f.auto_created and f.name not in ro:
                    ro.append(f.name)
        return tuple(ro)

    def has_delete_permission(self, request: HttpRequest, obj: Ato | None = None) -> bool:
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
        obj: Ato | None = None,
    ) -> Any:
        if obj and obj.versao.is_immutable:
            messages.warning(
                request,
                f"A versão deste ato ({obj.versao}) está "
                f"{obj.versao.get_status_display().upper()}. "
                "O conteúdo está congelado.",
            )
        return super().render_change_form(request, context, add, change, form_url, obj)

    # -------------------------------------------------------------------------
    #  Display helpers
    # -------------------------------------------------------------------------
    @short_description("Status da versão")
    def versao_status(self, obj: Ato) -> str:
        return obj.versao.get_status_display()

    @short_description("Perguntas")
    def perguntas_count(self, obj: Ato) -> Any:
        count = obj.perguntas.count()
        if count == 0 and obj.slug not in ("acolhimento", "sintese", "ponte"):
            return format_html('<span style="color:#dc3545;">0 ⚠</span>')
        return count
