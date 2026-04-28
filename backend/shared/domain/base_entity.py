"""
Ferzion Discovery — Shared / Domain / Base Entity.

Toda entidade de negócio do sistema herda desta classe base.

Princípios:
    - UUID como identificador (não auto-incremento). Razões:
        * Pinning robusto entre tabelas versionadas.
        * URLs públicas não revelam contagem de registros.
        * Fusão de bases distintas é trivial.
    - Auditoria temporal: created_at, updated_at automáticos.
    - "Soft delete" (is_deleted + deleted_at) para preservar histórico.

NÃO usar para entidades transversais do Django (User, Group, etc).
USAR para todo model de domínio em apps/methodology, apps/briefing, etc.
"""

from __future__ import annotations

import uuid
from typing import ClassVar

from django.db import models
from django.utils import timezone


class BaseEntity(models.Model):
    """Classe base abstrata para todas as entidades de domínio."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="Identificador único",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name="Criado em",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Atualizado em",
    )

    # Soft delete — preserva histórico mesmo após "remoção"
    is_deleted = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="Excluído (soft)",
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Excluído em",
    )

    class Meta:
        abstract = True
        ordering: ClassVar[list[str]] = ["-created_at"]

    # -------------------------------------------------------------------------
    #  Soft delete API
    # -------------------------------------------------------------------------
    def soft_delete(self) -> None:
        """Marca como excluído sem remover do banco."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at", "updated_at"])

    def restore(self) -> None:
        """Restaura entidade soft-deletada."""
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=["is_deleted", "deleted_at", "updated_at"])
