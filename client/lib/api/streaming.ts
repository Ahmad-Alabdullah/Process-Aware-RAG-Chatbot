import { API_BASE_URL } from "./client";
import { parseErrorResponse, handleNetworkError, APIError } from "./error-handler";
import type { AskRequest, EvidenceChunk } from "@/types";

/**
 * Enhanced Streaming API Client
 * 
 * Features:
 * - Timeout detection for stalled connections
 * - Progress tracking (connecting, streaming, done)
 * - Connection status updates
 * - Graceful error handling
 * 
 * SECURITY: API key is handled server-side in /api/proxy route
 * and never exposed to the client-side JavaScript bundle.
 */

export interface StreamMetadata {
  context: EvidenceChunk[];
  gating_mode: string;
  gating_hint: string;
  gating_metadata: Record<string, unknown>;
  used_model: string;
  used_hyde: boolean;
  used_rerank: boolean;
}

export type StreamStatus = 
  | "connecting"    // Initial connection being established
  | "waiting"       // Connected, waiting for first token
  | "streaming"     // Actively receiving tokens
  | "done"          // Stream completed successfully
  | "error";        // Stream ended with error

export interface StreamProgress {
  status: StreamStatus;
  tokenCount: number;
  elapsedMs: number;
}

interface StreamCallbacks {
  onMetadata?: (metadata: StreamMetadata) => void;
  onToken?: (token: string) => void;
  onDone?: () => void;
  onError?: (error: APIError) => void;
  onProgress?: (progress: StreamProgress) => void;
}

interface StreamOptions {
  /** Connection timeout in milliseconds (default: 30000) */
  connectionTimeoutMs?: number;
  /** Inactivity timeout - max time between tokens (default: 60000) */
  inactivityTimeoutMs?: number;
  /** Enable progress callbacks (default: true) */
  trackProgress?: boolean;
}

/**
 * Stream a question to the backend and receive tokens as they're generated
 */
export async function askQuestionStream(
  request: AskRequest,
  callbacks: StreamCallbacks,
  options: StreamOptions = {}
): Promise<void> {
  const {
    connectionTimeoutMs = 90000,
    inactivityTimeoutMs = 90000,
    trackProgress = true,
  } = options;

  let response: Response;
  const startTime = Date.now();
  let tokenCount = 0;
  let lastActivityTime = Date.now();

  // Helper to report progress
  const reportProgress = (status: StreamStatus) => {
    if (trackProgress && callbacks.onProgress) {
      callbacks.onProgress({
        status,
        tokenCount,
        elapsedMs: Date.now() - startTime,
      });
    }
  };

  // Report connecting status
  reportProgress("connecting");
  
  // Create AbortController for timeout handling
  const controller = new AbortController();
  let connectionTimeoutId: NodeJS.Timeout | undefined;

  try {
    // Set connection timeout
    connectionTimeoutId = setTimeout(() => {
      controller.abort();
    }, connectionTimeoutMs);

    response = await fetch(`${API_BASE_URL}/api/qa/ask/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
      signal: controller.signal,
    });

    // Clear connection timeout once we have a response
    clearTimeout(connectionTimeoutId);
    connectionTimeoutId = undefined;

  } catch (error) {
    if (connectionTimeoutId) clearTimeout(connectionTimeoutId);
    
    // Check if it was an abort (timeout)
    if ((error as Error).name === "AbortError") {
      const apiError = new APIError({
        code: "LLM_TIMEOUT",
        message: "Connection timeout",
        userMessage: "Verbindung zum Server konnte nicht hergestellt werden.",
        retryable: true,
      });
      reportProgress("error");
      callbacks.onError?.(apiError);
      throw apiError;
    }
    
    const apiError = handleNetworkError(error as Error);
    reportProgress("error");
    callbacks.onError?.(apiError);
    throw apiError;
  }

  if (!response.ok) {
    let body;
    try {
      body = await response.json();
    } catch {
      body = undefined;
    }
    const apiError = parseErrorResponse(response.status, body);
    reportProgress("error");
    callbacks.onError?.(apiError);
    throw apiError;
  }

  if (!response.body) {
    const apiError = new APIError({
      code: "UNKNOWN_ERROR",
      message: "No response body",
      userMessage: "Keine Antwort vom Server erhalten.",
      retryable: true,
    });
    reportProgress("error");
    callbacks.onError?.(apiError);
    throw apiError;
  }

  // Report waiting status (connected, waiting for first data)
  reportProgress("waiting");

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  // Inactivity timeout check
  let inactivityTimeoutId: NodeJS.Timeout | undefined;
  
  const resetInactivityTimeout = () => {
    if (inactivityTimeoutId) clearTimeout(inactivityTimeoutId);
    lastActivityTime = Date.now();
    
    inactivityTimeoutId = setTimeout(() => {
      reader.cancel();
    }, inactivityTimeoutMs);
  };

  // Start inactivity timer
  resetInactivityTimeout();

  try {
    // Helper function to parse SSE events from lines
    const parseSSELines = (lines: string[]) => {
      let eventType = "";
      let eventData = "";

      for (const line of lines) {
        if (line.startsWith("event: ")) {
          eventType = line.slice(7).trim();
        } else if (line.startsWith("data: ")) {
          eventData = line.slice(6);

          if (eventType && eventData) {
            try {
              const parsed = JSON.parse(eventData);

              if (eventType === "metadata") {
                callbacks.onMetadata?.(parsed as StreamMetadata);
              } else if (eventType === "token") {
                tokenCount++;
                if (tokenCount === 1) {
                  reportProgress("streaming");
                }
                callbacks.onToken?.(parsed as string);
              } else if (eventType === "done") {
                if (inactivityTimeoutId) clearTimeout(inactivityTimeoutId);
                reportProgress("done");
                callbacks.onDone?.();
              }
            } catch (e) {
              // If it's a token event, the data might be a plain string
              if (eventType === "token") {
                tokenCount++;
                if (tokenCount === 1) {
                  reportProgress("streaming");
                }
                callbacks.onToken?.(eventData);
              }
            }

            eventType = "";
            eventData = "";
          }
        }
      }
    };

    while (true) {
      const { done, value } = await reader.read();

      if (done) {
        // Stream reader finished - process any remaining buffer content
        // This is critical for fast responses where events may still be in buffer
        if (buffer.trim()) {
          const remainingLines = buffer.split("\n");
          parseSSELines(remainingLines);
        }
        if (inactivityTimeoutId) clearTimeout(inactivityTimeoutId);
        break;
      }

      // Reset inactivity timer on each chunk
      resetInactivityTimeout();

      buffer += decoder.decode(value, { stream: true });

      // Parse SSE events
      const lines = buffer.split("\n");
      buffer = lines.pop() || ""; // Keep incomplete line in buffer

      parseSSELines(lines);
    }
  } catch (error) {
    if (inactivityTimeoutId) clearTimeout(inactivityTimeoutId);
    
    // Check if it was a cancellation due to inactivity timeout
    if (Date.now() - lastActivityTime >= inactivityTimeoutMs) {
      const apiError = new APIError({
        code: "LLM_TIMEOUT",
        message: "Stream inactivity timeout",
        userMessage: "Die Antwortgenerierung wurde unterbrochen (keine Aktivität).",
        retryable: true,
      });
      reportProgress("error");
      callbacks.onError?.(apiError);
      throw apiError;
    }
    
    // If it's already an APIError, rethrow it
    if (error instanceof APIError) {
      reportProgress("error");
      throw error;
    }
    
    // Otherwise wrap it
    const apiError = handleNetworkError(error as Error);
    reportProgress("error");
    callbacks.onError?.(apiError);
    throw apiError;
  }
}

/**
 * Check if the streaming API is available
 */
export async function checkStreamingHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`, {
      method: "GET",
      signal: AbortSignal.timeout(5000),
    });
    return response.ok;
  } catch {
    return false;
  }
}

