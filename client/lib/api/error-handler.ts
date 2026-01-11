/**
 * API Error Handler
 *
 * Centralized error handling with:
 * - Error classification (network, rate limit, server, validation)
 * - Automatic retry for transient errors
 * - User-friendly messages
 * - Integration with toast notifications
 */

import { toast } from "sonner";

// Error codes from backend
export type ErrorCode =
  | "RATE_LIMIT_EXCEEDED"
  | "SERVICE_UNAVAILABLE"
  | "LLM_TIMEOUT"
  | "VALIDATION_ERROR"
  | "RETRIEVAL_FAILED"
  | "NEO4J_UNAVAILABLE"
  | "NETWORK_ERROR"
  | "UNKNOWN_ERROR";

// Structured API error
export class APIError extends Error {
  code: ErrorCode;
  retryable: boolean;
  retryAfter?: number;
  userMessage: string;
  requestId?: string;
  details?: Record<string, unknown>;

  constructor(options: {
    code: ErrorCode;
    message: string;
    userMessage: string;
    retryable?: boolean;
    retryAfter?: number;
    requestId?: string;
    details?: Record<string, unknown>;
  }) {
    super(options.message);
    this.name = "APIError";
    this.code = options.code;
    this.userMessage = options.userMessage;
    this.retryable = options.retryable ?? false;
    this.retryAfter = options.retryAfter;
    this.requestId = options.requestId;
    this.details = options.details;
  }
}

// User-friendly messages for each error code
const ERROR_MESSAGES: Record<ErrorCode, string> = {
  RATE_LIMIT_EXCEEDED:
    "Du hast zu viele Anfragen gesendet. Bitte warte einen Moment.",
  SERVICE_UNAVAILABLE: "Der Dienst ist vorübergehend nicht verfügbar.",
  LLM_TIMEOUT: "Die Antwortgenerierung hat zu lange gedauert.",
  VALIDATION_ERROR: "Ungültige Eingabe. Bitte überprüfe deine Anfrage.",
  RETRIEVAL_FAILED: "Die Dokumentensuche ist fehlgeschlagen.",
  NEO4J_UNAVAILABLE: "Prozessdaten sind momentan nicht verfügbar.",
  NETWORK_ERROR:
    "Keine Verbindung zum Server. Überprüfe deine Internetverbindung.",
  UNKNOWN_ERROR: "Ein unerwarteter Fehler ist aufgetreten.",
};

// Retryable error codes
const RETRYABLE_ERRORS: ErrorCode[] = [
  "SERVICE_UNAVAILABLE",
  "LLM_TIMEOUT",
  "NETWORK_ERROR",
];

/**
 * Parse error response from backend
 */
export function parseErrorResponse(
  status: number,
  body?: { error?: { code?: string; message?: string; details?: unknown } }
): APIError {
  // Handle rate limiting
  if (status === 429) {
    const retryAfter = body?.error?.details
      ? (body.error.details as { retry_after?: number }).retry_after
      : undefined;
    return new APIError({
      code: "RATE_LIMIT_EXCEEDED",
      message: body?.error?.message || "Rate limit exceeded",
      userMessage: retryAfter
        ? `Zu viele Anfragen. Bitte warte ${retryAfter} Sekunden.`
        : ERROR_MESSAGES.RATE_LIMIT_EXCEEDED,
      retryable: true,
      retryAfter,
    });
  }

  // Handle server errors
  if (status >= 500) {
    const code =
      status === 503 ? "SERVICE_UNAVAILABLE" : status === 504 ? "LLM_TIMEOUT" : "UNKNOWN_ERROR";
    return new APIError({
      code,
      message: body?.error?.message || `Server error ${status}`,
      userMessage: ERROR_MESSAGES[code],
      retryable: RETRYABLE_ERRORS.includes(code),
    });
  }

  // Handle validation errors
  if (status === 422) {
    return new APIError({
      code: "VALIDATION_ERROR",
      message: body?.error?.message || "Validation error",
      userMessage: body?.error?.message || ERROR_MESSAGES.VALIDATION_ERROR,
      retryable: false,
    });
  }

  // Handle other client errors
  if (status >= 400) {
    return new APIError({
      code: "UNKNOWN_ERROR",
      message: body?.error?.message || `Client error ${status}`,
      userMessage: ERROR_MESSAGES.UNKNOWN_ERROR,
      retryable: false,
    });
  }

  return new APIError({
    code: "UNKNOWN_ERROR",
    message: "Unknown error",
    userMessage: ERROR_MESSAGES.UNKNOWN_ERROR,
    retryable: false,
  });
}

/**
 * Handle network/fetch errors
 */
export function handleNetworkError(error: Error): APIError {
  if (error.name === "TypeError" && error.message.includes("fetch")) {
    return new APIError({
      code: "NETWORK_ERROR",
      message: error.message,
      userMessage: ERROR_MESSAGES.NETWORK_ERROR,
      retryable: true,
    });
  }

  return new APIError({
    code: "UNKNOWN_ERROR",
    message: error.message,
    userMessage: ERROR_MESSAGES.UNKNOWN_ERROR,
    retryable: false,
  });
}

/**
 * Show toast notification for an error
 */
export function showErrorToast(
  error: APIError,
  options?: {
    onRetry?: () => void;
  }
): void {
  if (error.retryable && options?.onRetry) {
    toast.error(error.userMessage, {
      action: {
        label: "Wiederholen",
        onClick: options.onRetry,
      },
      duration: error.retryAfter ? error.retryAfter * 1000 : 5000,
    });
  } else {
    toast.error(error.userMessage, {
      duration: 5000,
    });
  }
}

/**
 * Retry helper with exponential backoff
 */
export async function withRetry<T>(
  fn: () => Promise<T>,
  options: {
    maxRetries?: number;
    initialDelayMs?: number;
    maxDelayMs?: number;
    onRetry?: (attempt: number, error: Error) => void;
  } = {}
): Promise<T> {
  const {
    maxRetries = 3,
    initialDelayMs = 1000,
    maxDelayMs = 10000,
    onRetry,
  } = options;

  let lastError: Error = new Error("No attempts made");

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error as Error;

      // Check if error is retryable
      const apiError =
        error instanceof APIError ? error : handleNetworkError(error as Error);

      if (!apiError.retryable || attempt === maxRetries) {
        throw apiError;
      }

      // Calculate delay with exponential backoff
      const delay = Math.min(
        initialDelayMs * Math.pow(2, attempt),
        maxDelayMs
      );

      onRetry?.(attempt + 1, lastError);

      // Wait before retry
      await new Promise((resolve) => setTimeout(resolve, delay));
    }
  }

  throw lastError;
}

/**
 * Show success toast
 */
export function showSuccessToast(message: string): void {
  toast.success(message, {
    duration: 3000,
  });
}

/**
 * Show info toast
 */
export function showInfoToast(message: string): void {
  toast.info(message, {
    duration: 4000,
  });
}

/**
 * Show loading toast that can be updated
 */
export function showLoadingToast(message: string): string | number {
  return toast.loading(message);
}

/**
 * Update or dismiss a toast by ID
 */
export function updateToast(
  id: string | number,
  options: {
    type: "success" | "error" | "info";
    message: string;
  }
): void {
  if (options.type === "success") {
    toast.success(options.message, { id });
  } else if (options.type === "error") {
    toast.error(options.message, { id });
  } else {
    toast.info(options.message, { id });
  }
}

export function dismissToast(id: string | number): void {
  toast.dismiss(id);
}
