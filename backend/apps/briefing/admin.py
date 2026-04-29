"""
Ferzion Discovery — Briefing / Admin.

Admin de QA. Sessões são read-only no admin — não se edita briefing
a mão. Existe para inspeção, debug e analytics manuais.
"""

from __future__ import annotations

from typing import Any

from django.contrib import admin
from django.utils.html import format_html

from .models import (
    BriefingSessao,
    EventoBriefing,
    RespostaPergunta,
    SinalCapturado,
)


class RespostaInline(admin.TabularInline):
    model = RespostaPergunta
    extra = 0
    fields = ("pergunta_codigo", "pergunta_tipo", "valor", "versao", "pulada", "created_at")
    readonly_fields = fields
    can_delete = False

    def has_add_permission(self, *args: Any, **kwargs: Any) -> bool:
        return False


class SinalInline(admin.TabularInline):
    model = SinalCapturado
    extra = 0
    fields = ("sinal", "valor", "peso", "origem_resposta", "created_at")
    readonly_fields = fields
    autocomplete_fields = ("sinal",)
    can_delete = False

    def has_add_permission(self, *args: Any, **kwargs: Any) -> bool:
        return False


class EventoInline(admin.TabularInline):
    model = EventoBriefing
    extra = 0
    fields = ("tipo", "payload", "created_at")
    readonly_fields = fields
    can_delete = False

    def has_add_permission(self, *args: Any, **kwargs: Any) -> bool:
        return False


@admin.register(BriefingSessao)
class BriefingSessaoAdmin(admin.ModelAdmin):
    list_display = (
        "__str__",
        "status_label",
        "perfil_calculado",
        "respondidas",
        "sinais_count",
        "iniciada_em",
        "ultima_atividade_em",
    )
    list_filter = ("status", "perfil_calculado", "roteiro_versao__identidade")
    search_fields = ("token", "nome_empresa", "nome_respondente", "email_respondente")
    readonly_fields = (
        "id",
        "token",
        "iniciada_em",
        "concluida_em",
        "ultima_atividade_em",
        "user_agent",
        "ip_address",
        "devolutiva_json",
        "created_at",
        "updated_at",
    )
    autocomplete_fields = ("roteiro_versao", "pergunta_atual")
    inlines = (RespostaInline, SinalInline, EventoInline)

    fieldsets = (
        (
            "Identificação",
            {
                "fields": ("roteiro_versao", "token", "status", "perfil_calculado"),
            },
        ),
        (
            "Cliente",
            {
                "fields": ("nome_empresa", "nome_respondente", "email_respondente"),
            },
        ),
        (
            "Posição no fluxo",
            {
                "fields": ("ato_atual", "pergunta_atual"),
            },
        ),
        (
            "Devolutiva",
            {
                "classes": ("collapse",),
                "fields": ("devolutiva_json",),
            },
        ),
        (
            "Origem e telemetria",
            {
                "classes": ("collapse",),
                "fields": ("origem", "user_agent", "ip_address"),
            },
        ),
        (
            "Carimbos",
            {
                "classes": ("collapse",),
                "fields": (
                    "iniciada_em",
                    "concluida_em",
                    "ultima_atividade_em",
                    "id",
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )

    def has_add_permission(self, *args: Any, **kwargs: Any) -> bool:
        # Sessão de briefing nunca é criada manualmente
        return False

    def status_label(self, obj: BriefingSessao) -> Any:
        cores = {
            "iniciada": ("#856404", "#fff3cd"),
            "em_andamento": ("#0c5460", "#d1ecf1"),
            "concluida": ("#155724", "#d4edda"),
            "abandonada": ("#6c757d", "#e9ecef"),
        }
        cor, bg = cores.get(obj.status, ("#666", "#eee"))
        return format_html(
            '<span style="background:{}; color:{}; padding:2px 8px; '
            'border-radius:10px; font-size:11px; font-weight:600;">{}</span>',
            bg,
            cor,
            obj.get_status_display(),
        )

    status_label.short_description = "Status"

    def respondidas(self, obj: BriefingSessao) -> int:
        return obj.total_perguntas_respondidas

    respondidas.short_description = "Respondidas"

    def sinais_count(self, obj: BriefingSessao) -> int:
        return obj.total_sinais_capturados

    sinais_count.short_description = "Sinais"


@admin.register(SinalCapturado)
class SinalCapturadoAdmin(admin.ModelAdmin):
    list_display = ("sessao_token", "sinal", "valor", "peso", "created_at")
    list_filter = ("sinal__categoria", "sinal")
    search_fields = ("sessao__token", "sinal__chave")
    autocomplete_fields = ("sessao", "sinal")
    raw_id_fields = ("origem_resposta",)
    readonly_fields = ("created_at", "updated_at")

    def sessao_token(self, obj: SinalCapturado) -> str:
        return obj.sessao.token[:12]

    sessao_token.short_description = "Sessão"


@admin.register(EventoBriefing)
class EventoBriefingAdmin(admin.ModelAdmin):
    list_display = ("sessao_token", "tipo", "created_at")
    list_filter = ("tipo",)
    search_fields = ("sessao__token",)
    readonly_fields = ("sessao", "tipo", "payload", "created_at", "updated_at")

    def sessao_token(self, obj: EventoBriefing) -> str:
        return obj.sessao.token[:12]

    sessao_token.short_description = "Sessão"

    def has_add_permission(self, *args: Any, **kwargs: Any) -> bool:
        return False

    def has_change_permission(self, *args: Any, **kwargs: Any) -> bool:
        return False
