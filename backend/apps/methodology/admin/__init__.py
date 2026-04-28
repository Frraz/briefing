"""
Ferzion Discovery — Methodology / Admin.

Cada model do app methodology tem um admin dedicado em arquivo próprio.
Este __init__ apenas faz os imports necessários para que o decorador
@admin.register seja executado quando o Django carrega os admins.
"""

from . import (  # noqa: F401
    ato,
    catalogo_sinal,
    insight,
    pergunta,
    regra,
    roteiro,
)
