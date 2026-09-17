import type { ApiError, Universe } from "@/lib/types";

export class DashboardError extends Error {
  code: string;
  remedy: string;

  constructor(error: ApiError) {
    super(error.message);
    this.code = error.code;
    this.remedy = error.remedy;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init);
  if (response.ok) {
    return (await response.json()) as T;
  }
  let error: ApiError = {
    code: "http-error",
    message: `The API answered ${response.status}.`,
    remedy: "Check the terminal running `dtu-lite dashboard`.",
  };
  try {
    error = (await response.json()) as ApiError;
  } catch {
    // Not one of the library's failures; the generic message stands.
  }
  throw new DashboardError(error);
}

export function listUniverses(): Promise<Universe[]> {
  return request<Universe[]>("/api/universes");
}

export function getUniverse(id: string): Promise<Universe> {
  return request<Universe>(`/api/universes/${encodeURIComponent(id)}`);
}

export async function destroyUniverse(id: string): Promise<void> {
  await request<unknown>(`/api/universes/${encodeURIComponent(id)}`, {
    method: "DELETE",
  });
}

export function describe(cause: unknown): string {
  if (cause instanceof DashboardError) {
    return `${cause.message} ${cause.remedy}`;
  }
  return cause instanceof Error ? cause.message : String(cause);
}
