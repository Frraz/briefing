"""
Ferzion Discovery — Shared / Domain / Base Value Object.

Value Objects são objetos imutáveis identificados por seus VALORES,
não por identidade. Exemplo: "Faixa de Investimento R$30k-80k" é o
mesmo VO para qualquer briefing — não tem identidade própria.

Usamos Pydantic v2 como base porque:
    - Imutabilidade nativa via `frozen=True`.
    - Validação no construtor.
    - Serialização para JSON trivial (essencial para snapshots).
    - Type-checking forte com mypy.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class BaseValueObject(BaseModel):
    """Base imutável para todos os value objects do domínio."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )
