import { useCallback, useEffect, useState } from "react";

import {
  createRequest,
  fetchRequests,
  listStatuses,
  toMessage,
  transitionRequest,
  updateRequest,
} from "../api/client";
import type {
  RequestInput,
  RequestPage,
  Status,
  StatusCode,
} from "../api/types";

const PAGE_SIZE = 8;

export function useRequests() {
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilterState] = useState<StatusCode | null>(null);
  const [data, setData] = useState<RequestPage | null>(null);
  const [statuses, setStatuses] = useState<Status[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let active = true;
    listStatuses()
      .then((items) => {
        if (active) setStatuses(items);
      })
      .catch(() => {
        if (active) setStatuses([]);
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;
    const controller = new AbortController();
    setIsLoading(true);
    setError(null);

    fetchRequests({
      page,
      pageSize: PAGE_SIZE,
      status: statusFilter,
      signal: controller.signal,
    })
      .then((result) => {
        if (active) setData(result);
      })
      .catch((err: unknown) => {
        if (!active) return;
        if (err instanceof DOMException && err.name === "AbortError") return;
        setError(toMessage(err));
      })
      .finally(() => {
        if (active) setIsLoading(false);
      });

    return () => {
      active = false;
      controller.abort();
    };
  }, [page, statusFilter, reloadKey]);

  const reload = useCallback(() => setReloadKey((key) => key + 1), []);

  const setStatusFilter = useCallback((value: StatusCode | null) => {
    setStatusFilterState(value);
    setPage(1);
  }, []);

  const create = useCallback(async (input: RequestInput) => {
    await createRequest(input);
    // Al crear, se quita el filtro para que la nueva solicitud sea visible.
    setStatusFilterState(null);
    setPage(1);
    setReloadKey((key) => key + 1);
  }, []);

  const update = useCallback(async (id: number, input: RequestInput) => {
    const updated = await updateRequest(id, input);
    setData((current) =>
      current
        ? {
            ...current,
            items: current.items.map((item) =>
              item.id === id ? updated : item,
            ),
          }
        : current,
    );
  }, []);

  const transition = useCallback(
    async (id: number, to: StatusCode) => {
      const updated = await transitionRequest(id, to);

      // Si el filtro activo ya no coincide, recargar en vez de dejar
      // una tarjeta visible que no pertenece al filtro.
      if (statusFilter && updated.status.code !== statusFilter) {
        setReloadKey((key) => key + 1);
        return;
      }

      setData((current) =>
        current
          ? {
              ...current,
              items: current.items.map((item) =>
                item.id === id ? updated : item,
              ),
            }
          : current,
      );
    },
    [statusFilter],
  );

  return {
    data,
    statuses,
    isLoading,
    error,
    page,
    pageSize: PAGE_SIZE,
    statusFilter,
    setPage,
    setStatusFilter,
    reload,
    create,
    update,
    transition,
  };
}
