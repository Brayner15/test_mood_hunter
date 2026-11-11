import { useId, useState, type FormEvent } from "react";

import { toMessage } from "../api/client";
import type { RequestInput, RequestItem, StatusCode } from "../api/types";
import { formatDate } from "../utils/format";
import { StatusBadge } from "./StatusBadge";

const ACTION_LABELS: Record<StatusCode, string> = {
  created: "Devolver a creada",
  in_review: "Enviar a revisión",
  in_progress: "Iniciar trabajo",
  paused: "Pausar",
  done: "Finalizar",
};

function actionLabel(from: StatusCode, to: StatusCode): string {
  if (from === "paused" && to === "in_progress") return "Reanudar";
  if (from === "paused" && to === "in_review") return "Volver a revisión";
  return ACTION_LABELS[to];
}

interface Props {
  item: RequestItem;
  onUpdate: (id: number, input: RequestInput) => Promise<void>;
  onTransition: (id: number, to: StatusCode) => Promise<void>;
}

export function RequestCard({ item, onUpdate, onTransition }: Props) {
  const [isEditing, setIsEditing] = useState(false);
  const [draftTitle, setDraftTitle] = useState(item.title);
  const [draftDescription, setDraftDescription] = useState(
    item.description ?? "",
  );
  const [isSaving, setIsSaving] = useState(false);
  const [pendingTransition, setPendingTransition] =
    useState<StatusCode | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const formId = useId();
  const titleId = `${formId}-title`;
  const descriptionId = `${formId}-description`;

  const isBusy = isSaving || pendingTransition !== null;

  function startEditing() {
    setDraftTitle(item.title);
    setDraftDescription(item.description ?? "");
    setActionError(null);
    setIsEditing(true);
  }

  function cancelEditing() {
    setIsEditing(false);
    setActionError(null);
  }

  async function handleSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const cleanTitle = draftTitle.trim();

    if (cleanTitle.length < 3) {
      setActionError("El título debe tener al menos 3 caracteres.");
      return;
    }

    setIsSaving(true);
    setActionError(null);
    try {
      await onUpdate(item.id, {
        title: cleanTitle,
        description: draftDescription.trim() || null,
      });
      setIsEditing(false);
    } catch (err) {
      setActionError(toMessage(err));
    } finally {
      setIsSaving(false);
    }
  }

  async function handleTransition(to: StatusCode) {
    setPendingTransition(to);
    setActionError(null);
    try {
      await onTransition(item.id, to);
    } catch (err) {
      setActionError(toMessage(err));
    } finally {
      setPendingTransition(null);
    }
  }

  return (
    <article className="request-card" aria-busy={isBusy}>
      <div className="request-card-header">
        <h3 className="request-title">
          {isEditing ? "Editar solicitud" : item.title}
        </h3>
        <StatusBadge status={item.status} />
      </div>

      {isEditing ? (
        <form className="request-edit" onSubmit={handleSave} noValidate>
          <div className="form-row">
            <label htmlFor={titleId}>Título</label>
            <input
              id={titleId}
              value={draftTitle}
              onChange={(event) => setDraftTitle(event.target.value)}
              maxLength={150}
            />
          </div>
          <div className="form-row">
            <label htmlFor={descriptionId}>Descripción</label>
            <textarea
              id={descriptionId}
              value={draftDescription}
              onChange={(event) => setDraftDescription(event.target.value)}
              maxLength={5000}
              rows={3}
            />
          </div>

          {actionError && (
            <p className="form-error" role="alert">
              {actionError}
            </p>
          )}

          <div className="request-edit-actions">
            <button
              type="button"
              className="btn btn-ghost btn-small"
              onClick={cancelEditing}
              disabled={isSaving}
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="btn btn-primary btn-small"
              disabled={isSaving}
            >
              {isSaving ? "Guardando…" : "Guardar"}
            </button>
          </div>
        </form>
      ) : (
        <>
          <p className="request-description">
            {item.description || "Sin descripción."}
          </p>

          <div className="request-meta">
            <span>Creada: {formatDate(item.created_at)}</span>
            <span>Actualizada: {formatDate(item.updated_at)}</span>
          </div>

          {actionError && (
            <p className="form-error" role="alert">
              {actionError}
            </p>
          )}

          <div className="request-actions">
            <button
              type="button"
              className="btn btn-ghost btn-small"
              onClick={startEditing}
              disabled={isBusy}
            >
              Editar
            </button>

            {item.allowed_transitions.map((to) => (
              <button
                key={to}
                type="button"
                className={`btn btn-small ${
                  to === "done" ? "btn-primary" : "btn-ghost"
                }`}
                onClick={() => void handleTransition(to)}
                disabled={isBusy}
              >
                {pendingTransition === to
                  ? "Procesando…"
                  : actionLabel(item.status.code, to)}
              </button>
            ))}

            {item.allowed_transitions.length === 0 && (
              <span className="hint">Sin acciones disponibles.</span>
            )}
          </div>
        </>
      )}
    </article>
  );
}
