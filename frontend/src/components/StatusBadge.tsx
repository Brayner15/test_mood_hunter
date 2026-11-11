import type { Status } from "../api/types";

export function StatusBadge({ status }: { status: Status }) {
  return (
    <span className={`badge status-${status.code}`}>{status.label}</span>
  );
}
