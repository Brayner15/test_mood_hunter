import type {
  RequestInput,
  RequestItem,
  RequestPage,
  Status,
  StatusCode,
  SummaryResponse,
} from "./types";

const BASE_URL =
  (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "") ||
  "http://localhost:8000/api/v1";

interface ErrorPayload {
  error?: {
    code?: string;
    message?: string;
    details?: unknown;
  };
}

export class ApiError extends Error {
  readonly code: string;
  readonly status: number;
  readonly details: unknown;

  constructor(
    message: string,
    code: string,
    status: number,
    details: unknown = null,
  ) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    let payload: ErrorPayload | null = null;
    try {
      payload = (await response.json()) as ErrorPayload;
    } catch {
      // La respuesta de error no era JSON; se usa el mensaje genérico.
    }
    throw new ApiError(
      payload?.error?.message ?? `La API respondió con error ${response.status}.`,
      payload?.error?.code ?? "UNKNOWN",
      response.status,
      payload?.error?.details ?? null,
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export function listStatuses(): Promise<Status[]> {
  return request<Status[]>("/statuses");
}

export function fetchRequests(params: {
  page: number;
  pageSize: number;
  status: StatusCode | null;
  signal?: AbortSignal;
}): Promise<RequestPage> {
  const search = new URLSearchParams({
    page: String(params.page),
    page_size: String(params.pageSize),
  });
  if (params.status) {
    search.set("status", params.status);
  }
  return request<RequestPage>(`/requests?${search.toString()}`, {
    signal: params.signal,
  });
}

export function createRequest(input: RequestInput): Promise<RequestItem> {
  return request<RequestItem>("/requests", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function updateRequest(
  id: number,
  input: RequestInput,
): Promise<RequestItem> {
  return request<RequestItem>(`/requests/${id}`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

export function transitionRequest(
  id: number,
  to: StatusCode,
): Promise<RequestItem> {
  return request<RequestItem>(`/requests/${id}/transitions`, {
    method: "POST",
    body: JSON.stringify({ to }),
  });
}

export function fetchSummary(): Promise<SummaryResponse> {
  return request<SummaryResponse>("/requests/summary");
}

export function toMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }
  if (error instanceof TypeError) {
    return "No se pudo conectar con el servidor. Verifica que la API esté en marcha.";
  }
  return "Ocurrió un error inesperado. Intenta de nuevo.";
}
