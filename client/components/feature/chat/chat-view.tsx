"use client";

import { useRef, useEffect } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { MessageBubble } from "./message-bubble";
import type { Message } from "@/types";
import type { StreamStatus } from "@/lib/api/streaming";

interface ChatViewProps {
  messages: Message[];
  isLoading?: boolean;
  streamStatus?: StreamStatus;
}

// Loading indicator component with different states
function LoadingIndicator({ status }: { status?: StreamStatus }) {
  const getStatusText = () => {
    switch (status) {
      case "connecting":
        return "Verbindung wird hergestellt...";
      case "waiting":
        return "Denke nach...";
      case "streaming":
        return ""; // No text needed during streaming
      default:
        return "Verarbeite...";
    }
  };

  const statusText = getStatusText();

  return (
    <div className="flex gap-3">
      <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
        <span className="text-xs">AI</span>
      </div>
      <div className="bg-muted rounded-lg p-4 max-w-[80%]">
        <div className="flex items-center gap-2">
          {/* Animated dots */}
          <div className="flex gap-1">
            <span className="w-2 h-2 rounded-full bg-primary/60 animate-bounce" style={{ animationDelay: "0ms" }} />
            <span className="w-2 h-2 rounded-full bg-primary/60 animate-bounce" style={{ animationDelay: "150ms" }} />
            <span className="w-2 h-2 rounded-full bg-primary/60 animate-bounce" style={{ animationDelay: "300ms" }} />
          </div>
          {statusText && (
            <span className="text-sm text-muted-foreground ml-2">
              {statusText}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

export function ChatView({ messages, isLoading, streamStatus }: ChatViewProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    // Use setTimeout to ensure DOM is updated
    const timer = setTimeout(() => {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, 50);
    return () => clearTimeout(timer);
  }, [messages]);

  // Scroll to bottom on initial mount
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "instant" });
  }, []);

  if (messages.length === 0 && !isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center min-h-0 overflow-hidden">
        <div className="text-center text-muted-foreground">
          <h2 className="text-xl font-semibold mb-2">Willkommen!</h2>
          <p className="text-sm">
            Stelle eine Frage, um zu beginnen.
            <br />
            Wähle optional einen Prozess für kontextbezogene Antworten.
          </p>
        </div>
      </div>
    );
  }

  // Determine if we should show loading indicator
  // Don't show if streaming (the message content is already updating)
  const showLoadingIndicator = isLoading && streamStatus !== "streaming" && streamStatus !== "done";

  return (
    <div className="flex-1 overflow-y-auto min-h-0" ref={scrollRef}>
      <div className="max-w-3xl mx-auto py-6 px-4 space-y-4">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        {showLoadingIndicator && (
          <LoadingIndicator status={streamStatus} />
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}

