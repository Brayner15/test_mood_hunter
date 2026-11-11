import type { RequestInput, RequestItem, StatusCode } from "../api/types";
import { RequestCard } from "./RequestCard";

interface Props {
  items: RequestItem[];
  onUpdate: (id: number, input: RequestInput) => Promise<void>;
  onTransition: (id: number, to: StatusCode) => Promise<void>;
}

export function RequestList({ items, onUpdate, onTransition }: Props) {
  if (items.length === 0) {
    return (
      <div className="empty-state">
        <strong>No hay solicitudes para mostrar.</strong>
        <p>Crea la primera con el formulario o cambia el filtro de estado.</p>
      </div>
    );
  }

  return (
    <div className="request-grid">
      {items.map((item) => (
        <RequestCard
          key={item.id}
          item={item}
          onUpdate={onUpdate}
          onTransition={onTransition}
        />
      ))}
    </div>
  );
}
