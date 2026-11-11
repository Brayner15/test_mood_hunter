from enum import StrEnum


class StatusCode(StrEnum):
    """Identificadores públicos y estables de los estados.

    La API expone y recibe estos códigos, nunca los ids internos de la BD.
    """

    CREATED = "created"
    IN_REVIEW = "in_review"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    DONE = "done"


# Orden lógico usado para presentar listas de estados de forma determinista.
STATUS_ORDER: tuple[StatusCode, ...] = (
    StatusCode.CREATED,
    StatusCode.IN_REVIEW,
    StatusCode.IN_PROGRESS,
    StatusCode.PAUSED,
    StatusCode.DONE,
)


def status_sort_key(status: StatusCode) -> int:
    return STATUS_ORDER.index(status)
