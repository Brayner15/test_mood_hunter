import pytest

from app.domain.errors import InvalidTransitionError
from app.domain.status import StatusCode
from app.domain.transitions import (
    ALLOWED_TRANSITIONS,
    allowed_transitions,
    can_transition,
    ensure_transition,
)

ALL_STATUSES = list(StatusCode)

VALID_TRANSITIONS = {
    (StatusCode.CREATED, StatusCode.IN_REVIEW),
    (StatusCode.IN_REVIEW, StatusCode.IN_PROGRESS),
    (StatusCode.IN_REVIEW, StatusCode.PAUSED),
    (StatusCode.IN_PROGRESS, StatusCode.DONE),
    (StatusCode.IN_PROGRESS, StatusCode.PAUSED),
    (StatusCode.PAUSED, StatusCode.IN_PROGRESS),
    (StatusCode.PAUSED, StatusCode.IN_REVIEW),
}


@pytest.mark.parametrize("current", ALL_STATUSES)
@pytest.mark.parametrize("target", ALL_STATUSES)
def test_todas_las_combinaciones_origen_destino(
    current: StatusCode, target: StatusCode
) -> None:
    """Cubre las 25 combinaciones: solo las 7 permitidas deben pasar."""
    expected = (current, target) in VALID_TRANSITIONS

    assert can_transition(current, target) is expected

    if expected:
        ensure_transition(current, target)  # no lanza
    else:
        with pytest.raises(InvalidTransitionError) as exc_info:
            ensure_transition(current, target)

        error = exc_info.value
        assert error.current == current
        assert error.target == target
        assert set(error.allowed) == set(ALLOWED_TRANSITIONS[current])
        assert f"'{current}'" in error.message
        assert f"'{target}'" in error.message


def test_created_no_puede_saltar_a_in_progress() -> None:
    with pytest.raises(InvalidTransitionError):
        ensure_transition(StatusCode.CREATED, StatusCode.IN_PROGRESS)


def test_paused_no_puede_terminar_directamente() -> None:
    with pytest.raises(InvalidTransitionError):
        ensure_transition(StatusCode.PAUSED, StatusCode.DONE)


def test_paused_solo_se_alcanza_desde_in_review_e_in_progress() -> None:
    origins = {
        status
        for status in ALL_STATUSES
        if can_transition(status, StatusCode.PAUSED)
    }
    assert origins == {StatusCode.IN_REVIEW, StatusCode.IN_PROGRESS}


def test_done_es_estado_final() -> None:
    assert allowed_transitions(StatusCode.DONE) == frozenset()
    for target in ALL_STATUSES:
        assert not can_transition(StatusCode.DONE, target)


def test_todas_las_transiciones_apuntan_a_estados_conocidos() -> None:
    for origin, destinations in ALLOWED_TRANSITIONS.items():
        assert origin in ALL_STATUSES
        assert destinations <= set(ALL_STATUSES)


def test_reglas_son_inmutables() -> None:
    with pytest.raises(TypeError):
        ALLOWED_TRANSITIONS[StatusCode.CREATED] = frozenset()  # type: ignore[index]

    with pytest.raises(AttributeError):
        allowed_transitions(StatusCode.CREATED).add(  # type: ignore[attr-defined]
            StatusCode.DONE
        )


def test_error_incluye_transiciones_disponibles_en_orden_de_flujo() -> None:
    with pytest.raises(InvalidTransitionError) as exc_info:
        ensure_transition(StatusCode.PAUSED, StatusCode.DONE)

    assert exc_info.value.allowed == (
        StatusCode.IN_REVIEW,
        StatusCode.IN_PROGRESS,
    )
