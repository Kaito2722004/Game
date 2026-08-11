/**
 * Central Axios configuration.
 *
 * Everything the rest of the app knows about HTTP lives here: the base URL,
 * the JWT header, unwrapping the backend's `{success, data, message}`
 * envelope, and turning failures into a single `ApiError` shape. No component
 * or feature module imports Axios directly.
 */

import axios, { AxiosError, type AxiosRequestConfig, type AxiosInstance } from "axios";
import type { ApiError, ApiErrorBody, ApiResponse } from "@/types";

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

export const USE_MOCK_API = import.meta.env.VITE_USE_MOCK_API === "true";

const TOKEN_STORAGE_KEY = "pd_access_token";

export function getStoredToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_STORAGE_KEY);
  } catch {
    return null;
  }
}

export function setStoredToken(token: string | null): void {
  try {
    if (token) localStorage.setItem(TOKEN_STORAGE_KEY, token);
    else localStorage.removeItem(TOKEN_STORAGE_KEY);
  } catch {
    /* storage unavailable (private mode): the session simply won't persist */
  }
}

export const httpClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 60_000,
});

httpClient.interceptors.request.use((config) => {
  const token = getStoredToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Demo Mode: swap in the fixture adapter. Loaded dynamically so the mock data
// is never bundled into a normal production build.
if (USE_MOCK_API) {
  void import("./mock/mockAdapter").then(({ mockAdapter }) => {
    httpClient.defaults.adapter = mockAdapter;
  });
  console.warn(
    "[Demo Mode] Using the local mock adapter. Set VITE_USE_MOCK_API=false to talk to FastAPI.",
  );
}

/** Human-readable message for each status the backend can return. */
function messageForStatus(status: number, backendMessage?: string): string {
  if (backendMessage) return backendMessage;
  switch (status) {
    case 400:
      return "The request was rejected as invalid.";
    case 401:
      return "You need to sign in to do that.";
    case 403:
      return "Your account does not have permission for this action.";
    case 404:
      return "That item could not be found.";
    case 409:
      return "That conflicts with something that already exists.";
    case 422:
      return "Some of the values supplied were not valid.";
    case 500:
      return "The backend hit an unexpected error.";
    default:
      return "The request failed.";
  }
}

/** Flatten FastAPI/Pydantic validation errors into readable lines. */
function extractDetails(errors: unknown): string[] {
  if (!Array.isArray(errors)) return [];
  return errors.map((entry) => {
    if (typeof entry === "string") return entry;
    if (entry && typeof entry === "object") {
      const record = entry as Record<string, unknown>;
      const field = typeof record.field === "string" ? record.field : "";
      const msg = typeof record.message === "string" ? record.message : JSON.stringify(entry);
      return field ? `${field}: ${msg}` : msg;
    }
    return String(entry);
  });
}

export function toApiError(error: unknown): ApiError {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<ApiErrorBody>;

    if (!axiosError.response) {
      return {
        status: 0,
        message:
          "Unable to connect to the backend. Please make sure the FastAPI server is running " +
          `at ${API_BASE_URL}.`,
        details: [],
        isNetworkError: true,
      };
    }

    const { status, data } = axiosError.response;
    return {
      status,
      message: messageForStatus(status, data?.message),
      details: extractDetails(data?.errors),
      isNetworkError: false,
    };
  }

  return {
    status: 0,
    message: error instanceof Error ? error.message : "Something went wrong.",
    details: [],
    isNetworkError: false,
  };
}

export function isApiError(value: unknown): value is ApiError {
  return (
    typeof value === "object" &&
    value !== null &&
    "status" in value &&
    "message" in value &&
    "isNetworkError" in value
  );
}

/**
 * Perform a request and return the unwrapped `data` field.
 *
 * Throws an `ApiError` on any failure, so callers never deal with Axios
 * error shapes.
 */
export async function request<T>(config: AxiosRequestConfig): Promise<T> {
  try {
    const response = await httpClient.request<ApiResponse<T>>(config);
    return response.data.data;
  } catch (error) {
    throw toApiError(error);
  }
}

/** Fetch a text/csv endpoint as a Blob for download. */
export async function requestBlob(url: string): Promise<Blob> {
  try {
    const response = await httpClient.get(url, { responseType: "blob" });
    return response.data as Blob;
  } catch (error) {
    throw toApiError(error);
  }
}

export const get = <T>(url: string, config?: AxiosRequestConfig) =>
  request<T>({ ...config, method: "GET", url });

export const post = <T>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
  request<T>({ ...config, method: "POST", url, data });

export const put = <T>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
  request<T>({ ...config, method: "PUT", url, data });

export const del = <T>(url: string, config?: AxiosRequestConfig) =>
  request<T>({ ...config, method: "DELETE", url });
