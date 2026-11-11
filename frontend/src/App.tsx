import type { StatusCode } from "./api/types";
import { Pagination } from "./components/Pagination";
import { RequestForm } from "./components/RequestForm";
import { RequestList } from "./components/RequestList";
import { SummaryPanel } from "./components/SummaryPanel";
import { useRequests } from "./hooks/useRequests";
import { useSummary } from "./hooks/useSummary";

function LoadingState() {
  return (
    <div className="loading" role="status">
      <span className="spinner" aria-hidden="true" />
      Cargando solicitudes…
    </div>
  );
}

export default function App() {
  const requests = useRequests();
  const summary = useSummary();
  const total = requests.data?.total ?? 0;

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">Full stack · FastAPI + React</p>
          <h1>Tablero de solicitudes</h1>
          <p className="subtitle">
            Crea, edita y mueve solicitudes por su flujo de estados.
          </p>
        </div>
        <div className="header-badge" aria-live="polite">
          <strong>{total}</strong>
          <span>{total === 1 ? "solicitud" : "solicitudes"}</span>
        </div>
      </header>

      <main className="layout">
        <section className="main-column" aria-labelledby="list-heading">
          <RequestForm onCreate={requests.create} />

          <section className="panel" aria-busy={requests.isLoading}>
            <div className="panel-header">
              <div>
                <h2 id="list-heading">Listado</h2>
                <p className="hint">
                  Las acciones se calculan desde el estado actual de cada
                  solicitud.
                </p>
              </div>

              <label className="filter">
                <span>Estado</span>
                <select
                  value={requests.statusFilter ?? ""}
                  onChange={(event) =>
                    requests.setStatusFilter(
                      (event.target.value || null) as StatusCode | null,
                    )
                  }
                >
                  <option value="">Todos</option>
                  {requests.statuses.map((status) => (
                    <option key={status.code} value={status.code}>
                      {status.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            {requests.isLoading && requests.data && (
              <p className="refreshing" role="status">
                Actualizando…
              </p>
            )}

            {requests.error && (
              <div className="alert" role="alert">
                <p>{requests.error}</p>
                <button
                  type="button"
                  className="btn btn-ghost btn-small"
                  onClick={requests.reload}
                >
                  Reintentar
                </button>
              </div>
            )}

            {requests.isLoading && !requests.data ? (
              <LoadingState />
            ) : (
              <>
                <RequestList
                  items={requests.data?.items ?? []}
                  onUpdate={requests.update}
                  onTransition={requests.transition}
                />
                <Pagination
                  page={requests.page}
                  pageSize={requests.pageSize}
                  total={total}
                  onChange={requests.setPage}
                />
              </>
            )}
          </section>
        </section>

        <aside className="side-column">
          <SummaryPanel {...summary} />
        </aside>
      </main>
    </div>
  );
}
