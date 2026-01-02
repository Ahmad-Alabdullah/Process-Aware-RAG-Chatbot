"use client";

import { useState, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { ChatSidebar } from "@/components/feature/chat/chat-sidebar";
import { ChatView } from "@/components/feature/chat/chat-view";
import { Composer } from "@/components/feature/chat/composer";
import { ContextBar } from "@/components/feature/context-bar/context-bar";
import { useChats, useChatMessages } from "@/hooks/use-chats";
import { useContextState } from "@/hooks/use-context-state";
import { askQuestionStream } from "@/lib/api/streaming";
import { buildAskRequest } from "@/lib/utils/mode-mapping";
import { computeAnswerConfidence } from "@/lib/utils/confidence";
import type { Message, EvidenceChunk } from "@/types";

interface ChatContainerProps {
  chatId?: string;
}

export function ChatContainer({ chatId }: ChatContainerProps) {
  const router = useRouter();
  const { createChat, refreshChats } = useChats();
  const { messages, addMessage, updateLastMessage, refreshMessages } = useChatMessages(chatId || null);
  const contextState = useContextState();
  const [isLoading, setIsLoading] = useState(false);
  const streamedContentRef = useRef("");
  const metadataRef = useRef<{ context: EvidenceChunk[]; gating_mode: string } | null>(null);

  const handleSend = useCallback(
    async (content: string) => {
      // Create new chat if needed
      let activeChatId = chatId;
      if (!activeChatId) {
        const newChat = createChat(content.slice(0, 50));
        activeChatId = newChat.id;
        router.push(`/chat/${newChat.id}`);
      }

      // Add user message (hook already refreshes state)
      addMessage({
        role: "user",
        content,
      });

      // Reset streaming state
      streamedContentRef.current = "";
      metadataRef.current = null;

      // Add placeholder assistant message
      addMessage({
        role: "assistant",
        content: "",
      });

      setIsLoading(true);

      try {
        // Build request with context
        const request = buildAskRequest(content, contextState.state, {
          use_rerank: true,
          top_k: 5,
        });

        // Stream response from backend
        await askQuestionStream(request, {
          onMetadata: (metadata) => {
            metadataRef.current = {
              context: metadata.context,
              gating_mode: metadata.gating_mode,
            };
          },
          onToken: (token) => {
            streamedContentRef.current += token;
            // Update message content progressively
            updateLastMessage({
              content: streamedContentRef.current,
            });
          },
          onDone: () => {
            // Compute confidence from evidence
            const context = metadataRef.current?.context || [];
            const confidence = computeAnswerConfidence(context);

            // Update final message with evidence and confidence
            updateLastMessage({
              content: streamedContentRef.current,
              evidence: context,
              confidence,
              gating_mode: metadataRef.current?.gating_mode,
            });
            refreshChats();
          },
          onError: (error) => {
            console.error("Stream error:", error);
            updateLastMessage({
              content: "Es tut mir leid, ich konnte keine Antwort generieren. Bitte versuche es erneut.",
            });
          },
        });
      } catch (error) {
        console.error("Failed to get response:", error);
        updateLastMessage({
          content: "Es tut mir leid, ich konnte keine Antwort generieren. Bitte versuche es erneut.",
        });
      } finally {
        setIsLoading(false);
      }
    },
    [chatId, createChat, addMessage, updateLastMessage, refreshChats, router, contextState.state]
  );

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      <ChatSidebar activeChatId={chatId} />

      <main className="flex-1 flex flex-col min-h-0 min-w-0">
        {/* Chat Messages */}
        <ChatView messages={messages} isLoading={isLoading} />

        {/* Bottom Area: Context Bar + Composer */}
        <div className="border-t border-border p-4 space-y-3">
          <ContextBar
            state={contextState.state}
            onProcessChange={contextState.setProcess}
            onTaskChange={contextState.setTask}
            onScopeChange={contextState.setScope}
            onClearProcess={contextState.clearProcess}
            onClearTask={contextState.clearTask}
          />

          <Composer onSend={handleSend} isLoading={isLoading} />
        </div>
      </main>
    </div>
  );
}
