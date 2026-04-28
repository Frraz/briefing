"""
Ferzion Discovery — Shared / Exceções de domínio.

Hierarquia de exceções de domínio. Todas herdam de DomainException
para que possam ser capturadas em handlers de API (DRF) e renderizadas
como respostas HTTP estruturadas.
"""


class DomainException(Exception):
    """Exceção base para qualquer violação de regra de domínio."""

    default_message: str = "Erro de domínio"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.default_message)


class InvariantViolation(DomainException):
    """Viola uma invariante de negócio (estado inválido detectado)."""

    default_message = "Invariante de domínio violada"


class ImmutableEntityModificationAttempt(DomainException):
    """
    Tentativa de modificar entidade imutável (ex: RoteiroVersao já publicado).

    Esta exceção é central para o padrão append-only. Ela é levantada toda
    vez que código tenta editar algo que já foi congelado.
    """

    default_message = "Esta entidade está congelada e não pode ser modificada"


class InvalidStateTransition(DomainException):
    """Transição inválida em uma máquina de estados (ex: archived → published)."""

    default_message = "Transição de estado não permitida"
