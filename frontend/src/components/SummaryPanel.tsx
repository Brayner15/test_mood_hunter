import type { SummaryResponse } from "../api/types";
import { formatDateTime } from "../utils/format";

interface Props {
  result: SummaryResponse | null;
  isLoading: boolean;
  error: string | null;
  generate: () => Promise<void>;
}

export function SummaryPanel({ result, isLoading, error, generate }: Props) {
  return (
    <section className="panel summary-panel" aria-labelledby="summary-heading">
      <div className="panel-header">
        <div>
          <p className="eyebrow">IA</p>
          <h2 id="summary-heading">Resumen del tablero</h2>
          <p className="hint">Se genera bajo demanda con datos agregados.</p>
        </div>
      </div>

      <button
        type="button"
        className="btn btn-primary"
        onClick={() => void generate()}
        disabled={isLoading}
      >
        {isLoading ? (
          <>
            <span className="spinner" aria-hidden="true" />
            Generando…
          </>
        ) : result ? (
          "Actualizar resumen"
        ) : (
          "Generar resumen"
        )}
      </button>

      {error && (
        <p className="alert" role="alert">
          {error}
        </p>
      )}

      <div aria-live="polite">
        {result?.status === "unavailable" && (
          <p className="notice" role="status">
            {result.message ?? "El resumen no está disponible en este momento."}
          </p>
        )}

        {result?.status === "ok" && result.summary && (
          <div>
            <p className="summary-text">{result.summary}</p>
            <p className="summary-footer">
              {result.generated_at
                ? `Generado el ${formatDateTime(result.generated_at)}`
                : "Resumen generado"}
              {result.cached ? " · desde caché" : ""}
            </p>
          </div>
        )}

        {!result && !isLoading && !error && (
          <p className="hint">
            Aún no hay resumen. El listado funciona aunque el modelo falle.
          </p>
        )}
      </div>
    </section>
  );
}
