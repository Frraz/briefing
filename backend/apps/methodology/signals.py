"""
Ferzion Discovery — Methodology / Signals.

Side-effects de domínio que acontecem em resposta a eventos de persistência.

Sinal central: quando uma RoteiroIdentidade é criada, o sistema cria
automaticamente uma RoteiroVersao v1 em status DRAFT. Isso garante que
nunca exista uma identidade "órfã" sem versão para popular.
"""

from __future__ import annotations

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import RoteiroIdentidade, RoteiroVersao, StatusVersao


@receiver(post_save, sender=RoteiroIdentidade)
def cria_versao_inicial_em_draft(
    sender: type[RoteiroIdentidade],
    instance: RoteiroIdentidade,
    created: bool,
    **kwargs: object,
) -> None:
    """
    Cria automaticamente uma RoteiroVersao v1 em DRAFT quando a identidade
    é criada.

    Comportamento:
        - Apenas no momento de criação (`created=True`).
        - Apenas se a identidade ainda não tem nenhuma versão (proteção
          contra criação duplicada em fixtures/testes).
    """
    if not created:
        return

    if instance.versoes.exists():
        return

    RoteiroVersao.objects.create(
        identidade=instance,
        status=StatusVersao.DRAFT,
        notas_da_versao="Versão inicial criada automaticamente.",
    )
