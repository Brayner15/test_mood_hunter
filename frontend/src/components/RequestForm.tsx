import { useId, useState, type FormEvent } from "react";

import { toMessage } from "../api/client";
import type { RequestInput } from "../api/types";

interface Props {
  onCreate: (input: RequestInput) => Promise<void>;
}

export function RequestForm({ onCreate }: Props) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const formId = useId();
  const titleId = `${formId}-title`;
  const descriptionId = `${formId}-description`;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const cleanTitle = title.trim();

    if (cleanTitle.length < 3) {
      setError("El título debe tener al menos 3 caracteres.");
      return;
    }

    setIsSubmitting(true);
    setError(null);
    try {
      await onCreate({
        title: cleanTitle,
        description: description.trim() || null,
      });
      setTitle("");
      setDescription("");
    } catch (err) {
      setError(toMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="panel" aria-labelledby={`${formId}-heading`}>
      <div className="panel-header">
        <div>
          <h2 id={`${formId}-heading`}>Nueva solicitud</h2>
          <p className="hint">Entra automáticamente en estado “Creada”.</p>
        </div>
      </div>

      <form className="request-form" onSubmit={handleSubmit} noValidate>
        <div className="form-row">
          <label htmlFor={titleId}>Título</label>
          <input
            id={titleId}
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            maxLength={150}
            placeholder="Ej. Migrar formulario de contacto"
            autoComplete="off"
          />
        </div>

        <div className="form-row">
          <label htmlFor={descriptionId}>
            Descripción <span className="optional">(opcional)</span>
          </label>
          <textarea
            id={descriptionId}
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            maxLength={5000}
            rows={3}
            placeholder="Detalle breve de la solicitud"
          />
        </div>

        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}

        <div className="form-actions">
          <span className="hint">Mínimo 3 caracteres en el título.</span>
          <button
            className="btn btn-primary"
            type="submit"
            disabled={isSubmitting}
          >
            {isSubmitting ? "Creando…" : "Crear solicitud"}
          </button>
        </div>
      </form>
    </section>
  );
}
