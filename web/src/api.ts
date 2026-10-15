import type {
  Inspection,
  Job,
  JobList,
  ModelMetadata,
  Review,
  ReviewCreate,
  ReviewList,
} from "./types";
export class ApiError extends Error {
  readonly code: string;
  readonly retryable: boolean;
  readonly request_id: string;
  constructor(
    code: string,
    message: string,
    retryable = false,
    request_id = "",
  ) {
    super(message);
    this.code = code;
    this.retryable = retryable;
    this.request_id = request_id;
  }
}
async function request<T>(url: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(url, init);
  const data: unknown = await response.json();
  if (!response.ok) {
    const value = data as {
      error?: {
        code: string;
        message: string;
        retryable: boolean;
        request_id: string;
      };
    };
    throw new ApiError(
      value.error?.code ?? "NETWORK",
      value.error?.message ?? "Request failed",
      value.error?.retryable ?? true,
      value.error?.request_id ?? "",
    );
  }
  return data as T;
}
export const api = {
  models: (signal?: AbortSignal) =>
    request<ModelMetadata>("/api/models", { signal }),
  jobs: (signal?: AbortSignal, cursor?: string) =>
    request<JobList>(
      `/api/jobs?limit=30${cursor ? `&cursor=${encodeURIComponent(cursor)}` : ""}`,
      { signal },
    ),
  job: (id: string, signal?: AbortSignal) =>
    request<Job>(`/api/jobs/${encodeURIComponent(id)}`, { signal }),
  inspection: (id: string, signal?: AbortSignal) =>
    request<Inspection>(`/api/inspections/${id}`, { signal }),
  reviews: (id: string, signal?: AbortSignal) =>
    request<ReviewList>(`/api/inspections/${id}/reviews`, { signal }),
  submit: (
    file: File,
    revision: string,
    mode: Job["data_mode"],
    key: string,
  ) => {
    const body = new FormData();
    body.set("image", file);
    body.set("model_revision", revision);
    body.set("data_mode", mode);
    return request<Job>("/api/jobs", {
      method: "POST",
      body,
      headers: { "Idempotency-Key": key },
    });
  },
  review: (id: string, input: ReviewCreate, key: string) =>
    request<Review>(`/api/inspections/${id}/reviews`, {
      method: "POST",
      body: JSON.stringify(input),
      headers: { "Content-Type": "application/json", "Idempotency-Key": key },
    }),
};
export function errorText(error: unknown): string {
  return error instanceof ApiError
    ? `${error.code}: ${error.message}${error.request_id ? ` (request ${error.request_id})` : ""}`
    : error instanceof Error
      ? error.message
      : "Request failed. Retry when the local API is available.";
}
