"use client";

import ReactMarkdown from "react-markdown";
import { User, Bot } from "lucide-react";
import { cn } from "@/lib/utils";
import { Quellenstempel } from "../evidence/quellenstempel";
import { ConfidenceBadge } from "../evidence/confidence-badge";
import type { Message } from "@/types";

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div
      className={cn("flex gap-3", isUser && "flex-row-reverse")}
    >
      {/* Avatar */}
      <div
        className={cn(
          "h-8 w-8 rounded-full flex items-center justify-center shrink-0",
          isUser
            ? "bg-primary text-primary-foreground"
            : "bg-muted text-muted-foreground"
        )}
      >
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>

      {/* Message Content */}
      <div
        className={cn(
          "rounded-lg p-4 max-w-[80%]",
          isUser
            ? "bg-primary text-primary-foreground"
            : "bg-muted"
        )}
      >
        {/* Confidence Badge (assistant only) */}
        {!isUser && message.confidence && (
          <div className="flex justify-end mb-2">
            <ConfidenceBadge confidence={message.confidence} />
          </div>
        )}

        {/* Message Text */}
        <div className={cn("prose prose-sm max-w-none", !isUser && "dark:prose-invert")}>
          {isUser ? (
            <p className="whitespace-pre-wrap m-0">{message.content}</p>
          ) : (
            <ReactMarkdown
              components={{
                p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                ul: ({ children }) => <ul className="mb-2 list-disc pl-4">{children}</ul>,
                ol: ({ children }) => <ol className="mb-2 list-decimal pl-4">{children}</ol>,
                li: ({ children }) => <li className="mb-1">{children}</li>,
                code: ({ children }) => (
                  <code className="bg-background/50 px-1 py-0.5 rounded text-xs">
                    {children}
                  </code>
                ),
                pre: ({ children }) => (
                  <pre className="bg-background/50 p-2 rounded overflow-x-auto text-xs">
                    {children}
                  </pre>
                ),
              }}
            >
              {message.content}
            </ReactMarkdown>
          )}
        </div>

        {/* Quellenstempel (assistant only) */}
        {!isUser && message.evidence && message.evidence.length > 0 && (
          <div className="mt-3 pt-3 border-t border-border/50">
            <Quellenstempel evidence={message.evidence} />
          </div>
        )}
      </div>
    </div>
  );
}
