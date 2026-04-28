"""Ferzion Discovery — Methodology / Admin / RegraDeSintese."""

from __future__ import annotations

from typing import Any

from django.contrib import admin, messages
from django.http import HttpRequest

from apps.methodology.models import RegraDeSintese

from ._helpers import short_description


@admin.register(RegraDeSintese)
class RegraDeSinteseAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "titulo_interno",
        "tipo",
        "prioridade",
        "impacto_estimado",
        "modulo_sugerido_codigo",
        "versao_label",
    )
    list_filter = (
        "versao__status",
        "tipo",
        "impacto_estimado",
    )
    search_fields = (
        "codigo",
        "titulo_interno",
        "template",
        "modulo_sugerido_codigo",
    )
    ordering = ("versao", "tipo", "-prioridade")
    autocomplete_fields = ("versao",)

    fieldsets = (
        (
            "Identificação",
            {"fields": ("versao", "codigo", "tipo")},
        ),
        (
            "Conteúdo",
            {
                "fields": ("titulo_interno", "template"),
                "description": (
                    "O template é renderizado quando a regra é aplicada. "
                    "Aceita variáveis no formato {variavel}. Tom Ferzion."
                ),
            },
        ),
        (
            "Aplicação",
            {
                "fields": ("condicoes", "prioridade", "perfis_aplicaveis"),
                "description": (
                    "Condições baseadas em sinais. perfis_aplicaveis vazio = todos os perfis."
                ),
            },
        ),
        (
            "Específico de oportunidades / módulos",
            {
                "classes": ("collapse",),
                "fields": ("impacto_estimado", "modulo_sugerido_codigo"),
                "description": (
                    "Preencher para regras de tipo OPORTUNIDADE ou "
                    "MODULO_SUGERIDO. impacto_estimado: 'alto' / 'medio' / "
                    "'baixo'. modulo_sugerido_codigo: gancho com módulos "
                    "do sistema do cliente (ex: 'crm_basico', 'auditoria')."
                ),
            },
        ),
        ("Notas internas", {"fields": ("notas_internas",)}),
        (
            "Auditoria",
            {
                "classes": ("collapse",),
                "fields": ("id", "created_at", "updated_at"),
            },
        ),
    )
    readonly_fields = ("id", "created_at", "updated_at")

    def get_readonly_fields(
        self, request: HttpRequest, obj: RegraDeSintese | None = None
    ) -> tuple[str, ...]:
        ro = list(super().get_readonly_fields(request, obj))
        if obj and obj.versao.is_immutable:
            for f in self.model._meta.get_fields():
                if f.concrete and not f.many_to_many and not f.auto_created and f.name not in ro:
                    ro.append(f.name)
        return tuple(ro)

    def has_delete_permission(
        self, request: HttpRequest, obj: RegraDeSintese | None = None
    ) -> bool:
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
        obj: RegraDeSintese | None = None,
    ) -> Any:
        if obj and obj.versao.is_immutable:
            messages.warning(
                request,
                f"A versão desta regra ({obj.versao}) está "
                f"{obj.versao.get_status_display().upper()}. "
                "O conteúdo está congelado.",
            )
        return super().render_change_form(request, context, add, change, form_url, obj)

    @short_description("Versão")
    def versao_label(self, obj: RegraDeSintese) -> str:
        return f"{obj.versao.identidade.nome} v{obj.versao.version}"
