export type StatusCode =
  | "created"
  | "in_review"
  | "in_progress"
  | "paused"
  | "done";

export interface Status {
  code: StatusCode;
  label: string;
  is_final: boolean;
}

export interface RequestItem {
  id: number;
  title: string;
  description: string | null;
  status: Status;
  created_at: string;
  updated_at: string;
  allowed_transitions: StatusCode[];
}

export interface RequestPage {
  items: RequestItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface RequestInput {
  title: string;
  description: string | null;
}

export interface SummaryResponse {
  status: "ok" | "unavailable";
  summary: string | null;
  generated_at: string | null;
  cached: boolean;
  message: string | null;
}
