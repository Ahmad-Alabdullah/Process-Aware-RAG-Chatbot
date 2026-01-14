import { API_BASE_URL } from "./client";
import { parseErrorResponse, handleNetworkError, APIError } from "./error-handler";
import type { AskRequest, EvidenceChunk } from "@/types";

/**
 * Enhanced SSE (Server-Sent Events) Streaming Client
 * 
 * Implements the SSE specification for robust event parsing:
 * - Handles events spanning multiple network chunks
 * - Proper timeout handling for connection and inactivity
 * - Progress tracking for UI status updates
 * - Graceful error handling with retryable flags
 * 
 * SSE Event Format:
 *   event: <event-type>
 *   data: <json-data>
 *   
 *   (empty line separates events)
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
  /** Connection timeout in milliseconds (default: 90000) */
  connectionTimeoutMs?: number;
  /** Inactivity timeout - max time between chunks (default: 90000) */
  inactivityTimeoutMs?: number;
  /** Enable progress callbacks (default: true) */
  trackProgress?: boolean;
}

/**
 * SSE Parser State Machine
 * Handles parsing of SSE events that may span multiple network chunks
 */
class SSEParser {
  private currentEventType = "";
  private currentEventData = "";
  private callbacks: StreamCallbacks;
  private tokenCount = 0;
  private reportProgress: (status: StreamStatus) => void;
  private clearInactivityTimeout: () => void;

  constructor(
    callbacks: StreamCallbacks,
    reportProgress: (status: StreamStatus) => void,
    clearInactivityTimeout: () => void
  ) {
    this.callbacks = callbacks;
    this.reportProgress = reportProgress;
    this.clearInactivityTimeout = clearInactivityTimeout;
  }

  getTokenCount(): number {
    return this.tokenCount;
  }

  /**
   * Parse SSE lines according to the SSE specification
   * Lines are expected to be split by newline already
   */
  parseLines(lines: string[]): void {
    for (const line of lines) {
      // Empty line signals end of an event (SSE spec)
      if (line === "") {
        this.dispatchEvent();
        continue;
      }

      // Parse field:value format
      if (line.startsWith("event:")) {
        this.currentEventType = line.slice(6).trim();
      } else if (line.startsWith("data:")) {
        // Append to data (SSE allows multiple data: lines)
        const data = line.slice(5).trim();
        if (this.currentEventData) {
          this.currentEventData += "\n" + data;
        } else {
          this.currentEventData = data;
        }
      }
      // Ignore other fields like "id:", "retry:", comments (lines starting with :)
    }
  }

  /**
   * Force dispatch any pending event (for end of stream)
   */
  flush(): void {
    if (this.currentEventType || this.currentEventData) {
      this.dispatchEvent();
    }
  }

  /**
   * Dispatch the current event to callbacks
   */
  private dispatchEvent(): void {
    if (!this.currentEventType || !this.currentEventData) {
      // Reset and skip if incomplete
      this.currentEventType = "";
      this.currentEventData = "";
      return;
    }

    try {
      const eventType = this.currentEventType;
      const eventData = this.currentEventData;
      
      // Reset before parsing (in case callback throws)
      this.currentEventType = "";
      this.currentEventData = "";

      if (eventType === "metadata") {
        const parsed = JSON.parse(eventData) as StreamMetadata;
        this.callbacks.onMetadata?.(parsed);
      } else if (eventType === "token") {
        this.tokenCount++;
        if (this.tokenCount === 1) {
          this.reportProgress("streaming");
        }
        // Token data is a JSON string
        try {
          const parsed = JSON.parse(eventData) as string;
          this.callbacks.onToken?.(parsed);
        } catch {
          // If not valid JSON, use as-is (plain text token)
          this.callbacks.onToken?.(eventData);
        }
      } else if (eventType === "done") {
        this.clearInactivityTimeout();
        this.reportProgress("done");
        this.callbacks.onDone?.();
      }
    } catch (e) {
      // JSON parse error - log but don't crash
      console.error("[SSE] Failed to parse event data:", e);
    }
  }
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
  let lastActivityTime = Date.now();

  // Helper to report progress
  const reportProgress = (status: StreamStatus) => {
    if (trackProgress && callbacks.onProgress) {
      callbacks.onProgress({
        status,
        tokenCount: sseParser?.getTokenCount() ?? 0,
        elapsedMs: Date.now() - startTime,
      });
    }
  };

  // Inactivity timeout management
  let inactivityTimeoutId: NodeJS.Timeout | undefined;
  let reader: ReadableStreamDefaultReader<Uint8Array> | undefined;

  const clearInactivityTimeout = () => {
    if (inactivityTimeoutId) {
      clearTimeout(inactivityTimeoutId);
      inactivityTimeoutId = undefined;
    }
  };

  const resetInactivityTimeout = () => {
    clearInactivityTimeout();
    lastActivityTime = Date.now();
    
    inactivityTimeoutId = setTimeout(() => {
      reader?.cancel();
    }, inactivityTimeoutMs);
  };

  // Create SSE parser (initialized after timeout functions are available)
  let sseParser: SSEParser | undefined;

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

  // Handle HTTP errors
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

  // Validate response body
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

  // Initialize stream reader and SSE parser
  reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  sseParser = new SSEParser(callbacks, reportProgress, clearInactivityTimeout);

  // Start inactivity timer
  resetInactivityTimeout();

  try {
    while (true) {
      const { done, value } = await reader.read();

      if (done) {
        // Stream finished - process remaining buffer and flush parser
        if (buffer.trim()) {
          const remainingLines = buffer.split("\n");
          sseParser.parseLines(remainingLines);
        }
        sseParser.flush();
        clearInactivityTimeout();
        break;
      }

      // Reset inactivity timer on each chunk
      resetInactivityTimeout();

      // Decode and add to buffer
      buffer += decoder.decode(value, { stream: true });

      // Split buffer into lines, keeping incomplete line in buffer
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      // Parse complete lines
      sseParser.parseLines(lines);
    }
  } catch (error) {
    clearInactivityTimeout();
    
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
