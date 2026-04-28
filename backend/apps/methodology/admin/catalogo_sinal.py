"""
Ferzion Discovery — Methodology / Admin / CatalogoSinal.

O catálogo de sinais é o vocabulário compartilhado entre todos os
roteiros. Editar com cuidado — afeta interpretação histórica.
"""

from __future__ import annotations

from typing import Any

from django.contrib import admin
from django.utils.html import format_html

from apps.methodology.models import CatalogoSinal

from ._helpers import categoria_sinal_badge, short_description


@admin.register(CatalogoSinal)
class CatalogoSinalAdmin(admin.ModelAdmin):
    list_display = (
        "chave",
        "nome",
        "categoria_badge",
        "tipo_valor",
        "valores_validos_resumido",
        "uso",
    )
    list_filter = ("categoria", "tipo_valor")
    search_fields = ("chave", "nome", "descricao")
    ordering = ("categoria", "chave")

    fieldsets = (
        (
            "Identificação",
            {
                "fields": ("chave", "nome", "categoria"),
                "description": (
                    "A chave é IMUTÁVEL na prática — alterá-la quebra "
                    "mapeamentos históricos. Use somente em correção de "
                    "typo recém-criado."
                ),
            },
        ),
        (
            "Tipo e domínio",
            {
                "fields": ("tipo_valor", "valores_validos"),
                "description": (
                    "Para CATEGÓRICO: lista de strings. Para ESCALA: [min, max]. "
                    "Para BOOLEANO/TEXTO/NUMÉRICO: deixar vazio."
                ),
            },
        ),
        ("Documentação", {"fields": ("descricao", "notas_internas")}),
        (
            "Auditoria",
            {
                "classes": ("collapse",),
                "fields": ("id", "created_at", "updated_at"),
            },
        ),
    )

    readonly_fields = ("id", "created_at", "updated_at")

    @short_description("Categoria")
    def categoria_badge(self, obj: CatalogoSinal) -> Any:
        return categoria_sinal_badge(obj.categoria, obj.get_categoria_display())

    @short_description("Domínio")
    def valores_validos_resumido(self, obj: CatalogoSinal) -> str:
        if not obj.valores_validos:
            return "—"
        if len(obj.valores_validos) > 5:
            return f"{', '.join(map(str, obj.valores_validos[:3]))}, … (+{len(obj.valores_validos) - 3})"
        return ", ".join(map(str, obj.valores_validos))

    @short_description("Em uso")
    def uso(self, obj: CatalogoSinal) -> str:
        count = obj.mapeamentos.count()
        if count == 0:
            return format_html('<span style="color:#999;">não usado</span>')
        return format_html(
            '<span style="color:#155724;">{} mapeamento{}</span>',
            count,
            "" if count == 1 else "s",
        )
