"""Máquina de estados de las solicitudes.

Este módulo es intencionadamente puro: no conoce HTTP, base de datos ni
frameworks. Así las reglas del flujo se pueden probar de forma exhaustiva y
reutilizar desde cualquier capa.

Flujo principal:  created -> in_review -> in_progress -> done
Rama de pausa:    in_review | in_progress -> paused
Reanudación:      paused -> in_review | in_progress
"""

from collections.abc import Mapping
from types import MappingProxyType

from app.domain.errors import InvalidTransitionError
from app.domain.status import StatusCode

_ALLOWED: dict[StatusCode, frozenset[StatusCode]] = {
    StatusCode.CREATED: frozenset({StatusCode.IN_REVIEW}),
    StatusCode.IN_REVIEW: frozenset({StatusCode.IN_PROGRESS, StatusCode.PAUSED}),
    StatusCode.IN_PROGRESS: frozenset({StatusCode.DONE, StatusCode.PAUSED}),
    StatusCode.PAUSED: frozenset({StatusCode.IN_PROGRESS, StatusCode.IN_REVIEW}),
    StatusCode.DONE: frozenset(),
}

# Vista inmutable para que ninguna capa pueda alterar las reglas en runtime.
ALLOWED_TRANSITIONS: Mapping[StatusCode, frozenset[StatusCode]] = MappingProxyType(
    _ALLOWED
)


def allowed_transitions(current: StatusCode) -> frozenset[StatusCode]:
    """Estados a los que se puede pasar desde `current`."""
    return ALLOWED_TRANSITIONS[current]


def can_transition(current: StatusCode, target: StatusCode) -> bool:
    """Indica si la transición `current -> target` está permitida."""
    return target in ALLOWED_TRANSITIONS[current]


def ensure_transition(current: StatusCode, target: StatusCode) -> None:
    """Valida la transición y lanza InvalidTransitionError si no es válida.

    Se llama siempre antes de escribir en la base de datos.
    """
    if not can_transition(current, target):
        raise InvalidTransitionError(
            current=current,
            target=target,
            allowed=allowed_transitions(current),
        )
