"""
Ferzion Discovery — Methodology / Admin / Helpers.

Mixins, ações e utilitários compartilhados entre os admins do app.

Princípios desta camada:
    - Bloqueio visual coerente: versões imutáveis ficam read-only no admin.
    - Banner informativo no topo dos formulários quando a versão está
      published/archived.
    - Helpers de exibição (badges coloridos, contagens) reutilizáveis.
"""

from __future__ import annotations

from typing import Any

from django.utils.html import format_html
from django.utils.safestring import SafeString

# =============================================================================
#  Mixin de imutabilidade
# =============================================================================


class ImmutableAwareAdminMixin:
    """
    Mixin que torna o admin sensível ao estado de imutabilidade.

    Aplicação:
        - Quando o objeto pai (RoteiroVersao) está published/archived,
          todos os campos viram read-only.
        - Botão de "Salvar" some, restando apenas "Voltar".
        - Banner informativo aparece no topo via `change_form_template`.

    Subclasses devem implementar `get_versao_for_obj(obj)` retornando
    a RoteiroVersao relacionada, ou None se não aplicável.
    """

    def get_versao_for_obj(self, obj: Any) -> Any:
        """Subclasse implementa: dado o obj, retorna a RoteiroVersao dele."""
        raise NotImplementedError(
            "Subclasses de ImmutableAwareAdminMixin precisam implementar get_versao_for_obj()."
        )

    def _is_immutable_context(self, obj: Any) -> bool:
        """True se o objeto pertence a uma versão published/archived."""
        if obj is None:
            return False
        try:
            versao = self.get_versao_for_obj(obj)
        except Exception:
            return False
        return bool(versao and versao.is_immutable)

    def get_readonly_fields(self, request: Any, obj: Any = None) -> tuple[str, ...]:
        """Em contexto imutável, todos os campos viram readonly."""
        base = super().get_readonly_fields(request, obj)  # type: ignore[misc]
        if not self._is_immutable_context(obj):
            return base

        # Pega TODOS os campos do form e marca como readonly
        all_fields: list[str] = list(base)
        for field in self.model._meta.get_fields():  # type: ignore[attr-defined]
            if field.concrete and not field.many_to_many and not field.auto_created:
                if field.name not in all_fields:
                    all_fields.append(field.name)
        return tuple(all_fields)

    def has_delete_permission(self, request: Any, obj: Any = None) -> bool:
        if self._is_immutable_context(obj):
            return False
        return super().has_delete_permission(request, obj)  # type: ignore[misc]

    def has_change_permission(self, request: Any, obj: Any = None) -> bool:
        # Não bloqueia o GET — usuário precisa poder VER. Apenas readonly.
        return super().has_change_permission(request, obj)  # type: ignore[misc]


# =============================================================================
#  Helpers de exibição — badges coloridos
# =============================================================================


def badge(texto: str, cor: str = "#666", bg: str = "#eee") -> SafeString:
    """Renderiza um pill colorido para listagem do admin."""
    return format_html(
        '<span style="background:{}; color:{}; padding:2px 8px; '
        "border-radius:10px; font-size:11px; font-weight:600; "
        'text-transform:uppercase;">{}</span>',
        bg,
        cor,
        texto,
    )


# Mapeamentos de cores padronizados para uso nos admins
STATUS_VERSAO_CORES = {
    "draft": ("#856404", "#fff3cd"),  # amarelo
    "published": ("#155724", "#d4edda"),  # verde
    "archived": ("#6c757d", "#e9ecef"),  # cinza
}

SEVERIDADE_INSIGHT_CORES = {
    "info": ("#0c5460", "#d1ecf1"),  # azul
    "atencao": ("#856404", "#fff3cd"),  # amarelo
    "critico": ("#721c24", "#f8d7da"),  # vermelho
    "positivo": ("#155724", "#d4edda"),  # verde
}

CATEGORIA_SINAL_CORES = {
    "perfil": ("#5a3d6b", "#e7d9ee"),
    "negocio": ("#1f4e79", "#d6e4f1"),
    "operacao": ("#7d4e1d", "#f3e1c4"),
    "dor": ("#7a1f24", "#f5d2d4"),
    "aspiracao": ("#4a6b1d", "#e1efc8"),
    "restricao": ("#5a5a5a", "#e2e2e2"),
    "meta": ("#3a3a3a", "#dadada"),
}


def status_badge(status: str, label: str) -> SafeString:
    cor, bg = STATUS_VERSAO_CORES.get(status, ("#666", "#eee"))
    return badge(label, cor=cor, bg=bg)


def severidade_badge(severidade: str, label: str) -> SafeString:
    cor, bg = SEVERIDADE_INSIGHT_CORES.get(severidade, ("#666", "#eee"))
    return badge(label, cor=cor, bg=bg)


def categoria_sinal_badge(categoria: str, label: str) -> SafeString:
    cor, bg = CATEGORIA_SINAL_CORES.get(categoria, ("#666", "#eee"))
    return badge(label, cor=cor, bg=bg)


# =============================================================================
#  Decoradores curtos para listagem
# =============================================================================


def short_description(text: str):
    """Atalho para definir short_description em métodos de admin."""

    def wrapper(func):
        func.short_description = text
        return func

    return wrapper


def boolean_icon(value: bool) -> SafeString:
    """Ícone de check/x para listagem."""
    if value:
        return format_html('<span style="color:#28a745;">✓</span>')
    return format_html('<span style="color:#dc3545;">✗</span>')
