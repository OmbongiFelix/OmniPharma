import { env } from "../config/env";

/**
 * Error type thrown by {@link apiFetch} for any non-2xx response.
 */
export class ApiError extends Error {
  /** HTTP status code returned by the backend. */
  status: number;
  /** Backend-provided error detail, when present. */
  detail?: string;

  constructor(status: number, message: string, detail?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
    Object.setPrototypeOf(this, ApiError.prototype);
  }
}

/**
 * Helper to transform snake_case keys into camelCase keys recursively.
 */
export function keysToCamel<T = unknown>(obj: unknown): T {
  if (Array.isArray(obj)) {
    return obj.map((v) => keysToCamel(v)) as unknown as T;
  }
  if (obj !== null && typeof obj === "object" && !(obj instanceof Date) && !(obj instanceof RegExp)) {
    const n: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(obj as Record<string, unknown>)) {
      const camelKey = k.replace(/_([a-z0-9])/g, (_, letter) => letter.toUpperCase());
      n[camelKey] = keysToCamel(v);
    }
    return n as T;
  }
  return obj as T;
}

/**
 * Helper to transform camelCase keys into snake_case keys recursively.
 */
export function keysToSnake<T = unknown>(obj: unknown): T {
  if (Array.isArray(obj)) {
    return obj.map((v) => keysToSnake(v)) as unknown as T;
  }
  if (obj !== null && typeof obj === "object" && !(obj instanceof Date) && !(obj instanceof RegExp)) {
    const n: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(obj as Record<string, unknown>)) {
      const snakeKey = k.replace(/[A-Z]/g, (letter) => `_${letter.toLowerCase()}`);
      n[snakeKey] = keysToSnake(v);
    }
    return n as T;
  }
  return obj as T;
}

/**
 * Generates a pseudo-unique request ID for tracing.
 */
function generateRequestId(): string {
  return "req-" + Math.random().toString(36).substring(2, 10) + "-" + Date.now().toString(36);
}

/**
 * Configured fetch wrapper for all OmniPharma backend calls.
 *
 * Reads the backend base URL from `import.meta.env.VITE_API_BASE_URL`
 * (see `src/config/env.ts`), attaches a request-ID header, and
 * normalizes non-2xx responses into a thrown `ApiError` so every caller
 * handles failures the same way.
 *
 * @param path - Path relative to the API base URL, e.g. "/api/v1/patients".
 * @param init - Standard fetch RequestInit, merged with default headers.
 * @returns Parsed JSON response body, typed by the caller via a generic.
 * @throws {ApiError} When the response status is not in the 200-299 range.
 *   Carries `status` and the backend's error `detail` string so a
 *   component can distinguish, e.g., a 404 (unknown patient) from a 503
 *   (evidence service unavailable).
 */
export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${env.apiBaseUrl}${path.startsWith("/") ? path : `/${path}`}`;
  const requestId = generateRequestId();

  const headers = new Headers(init?.headers || {});
  if (!headers.has("Accept")) {
    headers.set("Accept", "application/json");
  }
  if (!headers.has("X-Request-ID")) {
    headers.set("X-Request-ID", requestId);
  }

  let body = init?.body;
  if (body && typeof body === "string") {
    try {
      const parsed = JSON.parse(body);
      const snakeCaseBody = keysToSnake(parsed);
      body = JSON.stringify(snakeCaseBody);
      if (!headers.has("Content-Type")) {
        headers.set("Content-Type", "application/json");
      }
    } catch {
      // Body was plain string; leave as is
    }
  }

  let response: Response;
  try {
    response = await fetch(url, {
      ...init,
      headers,
      body,
    });
  } catch (err) {
    const errorMsg = err instanceof Error ? err.message : String(err);
    throw new ApiError(0, `Network error communicating with OmniPharma backend: ${errorMsg}`, errorMsg);
  }

  const responseRequestId = response.headers.get("X-Request-ID") || requestId;

  if (!response.ok) {
    let detail = "";
    try {
      const errorJson = await response.json();
      detail = typeof errorJson.detail === "string" 
        ? errorJson.detail 
        : JSON.stringify(errorJson.detail || errorJson);
    } catch {
      detail = await response.text();
    }
    const message = detail || `Request failed with HTTP status ${response.status}`;
    throw new ApiError(response.status, message, detail);
  }

  if (response.status === 204) {
    return {} as T;
  }

  const rawJson = await response.json();
  const converted = keysToCamel<T>(rawJson);

  // If the parsed result is an object, attach the response requestId for audit meta
  if (converted !== null && typeof converted === "object" && !Array.isArray(converted)) {
    (converted as Record<string, unknown>).requestId = responseRequestId;
  }

  return converted;
}
