from collections.abc import Iterable

from app.domain.status import StatusCode, status_sort_key


class DomainError(Exception):
    """Error de negocio que la capa HTTP traducirá a una respuesta concreta."""

    code = "DOMAIN_ERROR"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class InvalidTransitionError(DomainError):
    """Se intentó un cambio de estado que la máquina de estados no permite."""

    code = "INVALID_TRANSITION"

    def __init__(
        self,
        current: StatusCode,
        target: StatusCode,
        allowed: Iterable[StatusCode],
    ) -> None:
        self.current = current
        self.target = target
        self.allowed = tuple(sorted(allowed, key=status_sort_key))
        super().__init__(
            f"No se puede pasar de '{current}' a '{target}'."
        )


class RequestNotFoundError(DomainError):
    """La solicitud solicitada no existe."""

    code = "REQUEST_NOT_FOUND"

    def __init__(self, request_id: int) -> None:
        self.request_id = request_id
        super().__init__(f"La solicitud {request_id} no existe.")


class UnknownStatusError(DomainError):
    """El código de estado no pertenece al catálogo."""

    code = "UNKNOWN_STATUS"

    def __init__(self, status: str) -> None:
        self.status = status
        super().__init__(f"El estado '{status}' no existe en el catálogo.")
