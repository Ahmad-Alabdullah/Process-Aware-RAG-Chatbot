"use client";

import { useRef, useEffect } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { MessageBubble } from "./message-bubble";
import type { Message } from "@/types";

interface ChatViewProps {
  messages: Message[];
  isLoading?: boolean;
}

export function ChatView({ messages, isLoading }: ChatViewProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  if (messages.length === 0 && !isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
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

  return (
    <ScrollArea className="flex-1 min-h-0">
      <div className="max-w-3xl mx-auto py-6 px-4 space-y-4">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        {isLoading && (
          <div className="flex gap-3">
            <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
              <span className="text-xs">AI</span>
            </div>
            <div className="bg-muted rounded-lg p-4 max-w-[80%]">
              <div className="flex gap-1">
                <span className="animate-pulse">●</span>
                <span className="animate-pulse delay-100">●</span>
                <span className="animate-pulse delay-200">●</span>
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  );
}
