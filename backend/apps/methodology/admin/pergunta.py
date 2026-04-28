"""
Ferzion Discovery — Methodology / Admin / Pergunta.

Admin de Pergunta com Opções e Mapeamentos inline.
"""

from __future__ import annotations

from typing import Any

from django.contrib import admin, messages
from django.http import HttpRequest
from django.utils.html import format_html

from apps.methodology.models import (
    MapeamentoDeSinal,
    OpcaoDePergunta,
    Pergunta,
)

from ._helpers import short_description


class OpcaoDePerguntaInline(admin.TabularInline):
    model = OpcaoDePergunta
    extra = 0
    fields = ("ordem", "codigo_interno", "texto_publico", "icone")
    ordering = ("ordem",)

    def has_add_permission(self, request: HttpRequest, obj: Pergunta | None = None) -> bool:
        if obj and obj.ato.versao.is_immutable:
            return False
        return super().has_add_permission(request, obj)

    def has_delete_permission(self, request: HttpRequest, obj: Pergunta | None = None) -> bool:
        if obj and obj.ato.versao.is_immutable:
            return False
        return super().has_delete_permission(request, obj)


class MapeamentoDeSinalInline(admin.TabularInline):
    model = MapeamentoDeSinal
    extra = 0
    fields = ("sinal", "condicao", "valor_extraido", "peso")
    autocomplete_fields = ("sinal",)

    def has_add_permission(self, request: HttpRequest, obj: Pergunta | None = None) -> bool:
        if obj and obj.ato.versao.is_immutable:
            return False
        return super().has_add_permission(request, obj)

    def has_delete_permission(self, request: HttpRequest, obj: Pergunta | None = None) -> bool:
        if obj and obj.ato.versao.is_immutable:
            return False
        return super().has_delete_permission(request, obj)


@admin.register(Pergunta)
class PerguntaAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "texto_resumido",
        "tipo",
        "ato_nome",
        "versao_status",
        "obrigatoria",
        "opcoes_count",
        "mapeamentos_count",
    )
    list_filter = (
        "ato__versao__status",
        "tipo",
        "obrigatoria",
        "ato__slug",
    )
    search_fields = (
        "codigo",
        "texto_publico",
        "objetivo_interno",
        "ato__versao__identidade__nome",
    )
    ordering = ("ato__versao", "ato__ordem", "ordem")
    autocomplete_fields = ("ato",)

    inlines = (OpcaoDePerguntaInline, MapeamentoDeSinalInline)

    fieldsets = (
        (
            "Identificação",
            {"fields": ("ato", "codigo", "ordem", "tipo", "obrigatoria")},
        ),
        (
            "Conteúdo público (cliente vê)",
            {
                "fields": (
                    "texto_publico",
                    "placeholder",
                    "helper_text",
                ),
                "description": (
                    "Tom Ferzion: simples, humano, sem corporativês. Microcopy importa muito aqui."
                ),
            },
        ),
        (
            "Objetivo interno",
            {
                "fields": ("objetivo_interno",),
                "description": (
                    "O que esta pergunta busca descobrir? "
                    "Não aparece para o cliente, mas é referência crucial."
                ),
            },
        ),
        (
            "Comportamento adaptativo",
            {
                "fields": ("perfis_minimos", "precondicoes"),
                "description": (
                    "perfis_minimos: lista de perfis nos quais esta pergunta "
                    "aparece. Vazio = sempre. "
                    "precondicoes: condições baseadas em sinais já capturados."
                ),
            },
        ),
        (
            "Configuração específica do tipo",
            {
                "fields": ("tipo_config",),
                "description": (
                    "JSON com schema dependente do tipo. "
                    "Ex.: para escala, {'min': 1, 'max': 5}; "
                    "para texto, {'max_chars': 200}; "
                    "para escolha_unica_com_outro, {'rotulo_outro': 'Outro: descreva'}."
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
    #  Bloqueio em pergunta cuja versão é imutável
    # -------------------------------------------------------------------------
    def get_readonly_fields(
        self, request: HttpRequest, obj: Pergunta | None = None
    ) -> tuple[str, ...]:
        ro = list(super().get_readonly_fields(request, obj))
        if obj and obj.ato.versao.is_immutable:
            for f in self.model._meta.get_fields():
                if f.concrete and not f.many_to_many and not f.auto_created and f.name not in ro:
                    ro.append(f.name)
        return tuple(ro)

    def has_delete_permission(self, request: HttpRequest, obj: Pergunta | None = None) -> bool:
        if obj and obj.ato.versao.is_immutable:
            return False
        return super().has_delete_permission(request, obj)

    def render_change_form(
        self,
        request: HttpRequest,
        context: dict[str, Any],
        add: bool = False,
        change: bool = False,
        form_url: str = "",
        obj: Pergunta | None = None,
    ) -> Any:
        if obj and obj.ato.versao.is_immutable:
            messages.warning(
                request,
                f"A versão desta pergunta ({obj.ato.versao}) está "
                f"{obj.ato.versao.get_status_display().upper()}. "
                "O conteúdo está congelado.",
            )
        return super().render_change_form(request, context, add, change, form_url, obj)

    # -------------------------------------------------------------------------
    #  Display helpers
    # -------------------------------------------------------------------------
    @short_description("Texto")
    def texto_resumido(self, obj: Pergunta) -> str:
        return (obj.texto_publico[:80] + "…") if len(obj.texto_publico) > 80 else obj.texto_publico

    @short_description("Ato")
    def ato_nome(self, obj: Pergunta) -> str:
        return obj.ato.get_slug_display()

    @short_description("Status da versão")
    def versao_status(self, obj: Pergunta) -> str:
        return obj.ato.versao.get_status_display()

    @short_description("Opções")
    def opcoes_count(self, obj: Pergunta) -> Any:
        count = obj.opcoes.count()
        if obj.requer_opcoes and count == 0:
            return format_html('<span style="color:#dc3545;">0 ⚠</span>')
        return count

    @short_description("Mapeamentos")
    def mapeamentos_count(self, obj: Pergunta) -> int:
        return obj.mapeamentos.count()
