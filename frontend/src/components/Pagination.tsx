interface Props {
  page: number;
  pageSize: number;
  total: number;
  onChange: (page: number) => void;
}

export function Pagination({ page, pageSize, total, onChange }: Props) {
  if (total === 0) return null;

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <nav className="pagination" aria-label="Paginación de solicitudes">
      <span className="pagination-info">
        Página {page} de {totalPages} · {total} en total
      </span>
      <div className="button-row">
        <button
          type="button"
          className="btn btn-ghost btn-small"
          onClick={() => onChange(page - 1)}
          disabled={page <= 1}
        >
          Anterior
        </button>
        <button
          type="button"
          className="btn btn-ghost btn-small"
          onClick={() => onChange(page + 1)}
          disabled={page >= totalPages}
        >
          Siguiente
        </button>
      </div>
    </nav>
  );
}
