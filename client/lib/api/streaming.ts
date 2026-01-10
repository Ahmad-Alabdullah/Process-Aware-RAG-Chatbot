import { API_BASE_URL } from "./client";
import type { AskRequest, EvidenceChunk } from "@/types";

const API_KEY = process.env.NEXT_PUBLIC_API_KEY || "";

function getStreamHeaders(): Record<string, string> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (API_KEY) {
    headers["X-API-Key"] = API_KEY;
  }
  return headers;
}

interface StreamMetadata {
  context: EvidenceChunk[];
  gating_mode: string;
  gating_hint: string;
  gating_metadata: Record<string, unknown>;
  used_model: string;
  used_hyde: boolean;
  used_rerank: boolean;
}

interface StreamCallbacks {
  onMetadata?: (metadata: StreamMetadata) => void;
  onToken?: (token: string) => void;
  onDone?: () => void;
  onError?: (error: Error) => void;
}

/**
 * Stream a question to the backend and receive tokens as they're generated
 */
export async function askQuestionStream(
  request: AskRequest,
  callbacks: StreamCallbacks
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/qa/ask/stream`, {
    method: "POST",
    headers: getStreamHeaders(),
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = new Error(`HTTP error ${response.status}`);
    callbacks.onError?.(error);
    throw error;
  }

  if (!response.body) {
    const error = new Error("No response body");
    callbacks.onError?.(error);
    throw error;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();

      if (done) {
        callbacks.onDone?.();
        break;
      }

      buffer += decoder.decode(value, { stream: true });

      // Parse SSE events
      const lines = buffer.split("\n");
      buffer = lines.pop() || ""; // Keep incomplete line in buffer

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
                callbacks.onToken?.(parsed as string);
              } else if (eventType === "done") {
                callbacks.onDone?.();
              }
            } catch (e) {
              // If it's a token event, the data might be a plain string
              if (eventType === "token") {
                callbacks.onToken?.(eventData);
              }
            }

            eventType = "";
            eventData = "";
          }
        }
      }
    }
  } catch (error) {
    callbacks.onError?.(error as Error);
    throw error;
  }
}
