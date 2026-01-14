"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { ChatSidebar } from "@/components/feature/chat/chat-sidebar";
import { ChatView } from "@/components/feature/chat/chat-view";
import { Composer } from "@/components/feature/chat/composer";
import { ContextBar } from "@/components/feature/context-bar/context-bar";
import {
  ResizablePanelGroup,
  ResizablePanel,
  ResizableHandle,
} from "@/components/ui/resizable";
import { useChats, useChatMessages } from "@/hooks/use-chats";
import { useContextState } from "@/hooks/use-context-state";
import { askQuestionStream, type StreamStatus } from "@/lib/api/streaming";
import { buildAskRequest } from "@/lib/utils/mode-mapping";
import { computeAnswerConfidence } from "@/lib/utils/confidence";
import { showErrorToast, APIError } from "@/lib/api/error-handler";
import {
  addMessage as addMessageApi,
  updateLastMessage as updateLastMessageApi,
  getMessages,
} from "@/lib/api/chats";
import type { Message, EvidenceChunk } from "@/types";

interface ChatContainerProps {
  chatId?: string;
}

export function ChatContainer({ chatId }: ChatContainerProps) {
  const router = useRouter();
  const { createChat, refreshChats } = useChats();
  const { messages: hookMessages, refreshMessages } = useChatMessages(chatId || null);
  const contextState = useContextState();
  
  // Local messages state to handle new chat case before navigation completes
  const [localMessages, setLocalMessages] = useState<Message[]>([]);
  const [activeChatIdState, setActiveChatIdState] = useState<string | null>(chatId || null);
  
  const [isLoading, setIsLoading] = useState(false);
  const [streamStatus, setStreamStatus] = useState<StreamStatus | undefined>(undefined);
  const streamedContentRef = useRef("");
  const metadataRef = useRef<{ context: EvidenceChunk[]; gating_mode: string } | null>(null);
  const lastRequestRef = useRef<{ content: string; chatId: string } | null>(null);
  const localMessagesRef = useRef<Message[]>([]);  // Ref to track current messages for closures

  // Keep ref in sync with state
  useEffect(() => {
    localMessagesRef.current = localMessages;
  }, [localMessages]);

  // Sync local state with hook messages when chatId matches
  useEffect(() => {
    if (chatId && chatId === activeChatIdState) {
      // When we have a chatId and it matches our active state, use hook messages
      setLocalMessages(hookMessages);
    } else if (chatId && chatId !== activeChatIdState) {
      // ChatId changed (navigated to different chat), reset to hook messages
      setActiveChatIdState(chatId);
      setLocalMessages(hookMessages);
    } else if (!chatId) {
      // No chatId (new chat page), keep local messages if we have an active chat
      if (!activeChatIdState) {
        setLocalMessages([]);
      }
    }
  }, [chatId, activeChatIdState, hookMessages]);

  // Refresh local messages from localStorage
  const refreshLocalMessages = useCallback((targetChatId: string) => {
    setLocalMessages(getMessages(targetChatId));
  }, []);

  const handleSend = useCallback(
    async (content: string) => {
      // Create new chat if needed
      let targetChatId = chatId;
      if (!targetChatId) {
        const newChat = createChat(content.slice(0, 50));
        targetChatId = newChat.id;
        setActiveChatIdState(targetChatId);
        router.push(`/chat/${newChat.id}`);
      }

      // Store request for potential retry
      lastRequestRef.current = { content, chatId: targetChatId };

      // Add user message using direct API call with correct chatId
      const userMessage = addMessageApi(targetChatId, {
        role: "user",
        content,
      });
      
      // Update local state immediately
      setLocalMessages(prev => [...prev, userMessage]);

      // Reset streaming state
      streamedContentRef.current = "";
      metadataRef.current = null;

      // Add placeholder assistant message
      const assistantMessage = addMessageApi(targetChatId, {
        role: "assistant",
        content: "",
      });
      
      // Update local state with placeholder
      setLocalMessages(prev => [...prev, assistantMessage]);

      setIsLoading(true);
      setStreamStatus("connecting");

      try {
        // Use ref to get fresh messages (avoids closure stale state issue)
        // localMessagesRef is always in sync with the current localMessages state
        const currentMessages = localMessagesRef.current;
        const recentHistory = currentMessages.slice(-6).map(m => ({
          role: m.role as "user" | "assistant",
          content: m.content.slice(0, 500), // Keep more chars for context check
        }));
        
        console.log("[DEBUG] Chat history being sent:", recentHistory.length, "messages", 
          recentHistory.map(h => `${h.role}: ${h.content.slice(0, 30)}...`));

        // Build request with context and history
        const request = buildAskRequest(content, contextState.state, {
          use_rerank: true,
          top_k: 5,
          chat_history: recentHistory.length > 0 ? recentHistory : undefined,
        });

        // Stream response from backend
        await askQuestionStream(request, {
          onMetadata: (metadata) => {
            // Debug: Log metadata receipt
            if (!metadata.context || metadata.context.length === 0) {
              console.warn("[PROD DEBUG] onMetadata received with EMPTY context!", metadata);
            } else {
              console.log("[PROD DEBUG] onMetadata received:", metadata.context.length, "chunks");
            }
            metadataRef.current = {
              context: metadata.context,
              gating_mode: metadata.gating_mode,
            };
          },
          onToken: (token) => {
            streamedContentRef.current += token;
            // Update message content progressively
            updateLastMessageApi(targetChatId, {
              content: streamedContentRef.current,
            });
            // Refresh local messages to show streaming content
            refreshLocalMessages(targetChatId);
          },
          onDone: () => {
            // Debug: Log state when onDone fires
            console.log("[PROD DEBUG] onDone called:", {
              hasMetadata: !!metadataRef.current,
              contextLength: metadataRef.current?.context?.length || 0,
              gatingMode: metadataRef.current?.gating_mode,
            });
            
            const context = metadataRef.current?.context || [];
            const gatingMode = metadataRef.current?.gating_mode;
            
            // Only compute confidence for actual RAG responses, not guardrail fallbacks
            const confidence = gatingMode === "guardrail" 
              ? undefined 
              : computeAnswerConfidence(context);
            
            console.log("[PROD DEBUG] Confidence computed:", confidence?.score, "from", context.length, "chunks");

            // Update final message with evidence and confidence
            updateLastMessageApi(targetChatId, {
              content: streamedContentRef.current,
              evidence: gatingMode === "guardrail" ? undefined : context,
              confidence,
              gating_mode: gatingMode,
            });
            refreshLocalMessages(targetChatId);
            setStreamStatus("done");
            refreshChats();
          },
          onProgress: (progress) => {
            setStreamStatus(progress.status);
          },
          onError: (error: APIError) => {
            console.error("Stream error:", error);
            
            // Show user-friendly error message in chat
            updateLastMessageApi(targetChatId, {
              content: `⚠️ ${error.userMessage}`,
              isError: true,
            });
            refreshLocalMessages(targetChatId);

            // Show toast with retry option if retryable
            showErrorToast(error, {
              onRetry: error.retryable
                ? () => {
                    if (lastRequestRef.current) {
                      handleSend(lastRequestRef.current.content);
                    }
                  }
                : undefined,
            });
          },
        });
      } catch (error) {
        console.error("Failed to get response:", error);
        
        const apiError = error instanceof APIError 
          ? error 
          : new APIError({
              code: "UNKNOWN_ERROR",
              message: String(error),
              userMessage: "Ein unerwarteter Fehler ist aufgetreten.",
              retryable: true,
            });

        // Show error in chat
        updateLastMessageApi(targetChatId, {
          content: `⚠️ ${apiError.userMessage}`,
          isError: true,
        });
        refreshLocalMessages(targetChatId);

        // Show toast with retry option
        showErrorToast(apiError, {
          onRetry: () => {
            if (lastRequestRef.current) {
              handleSend(lastRequestRef.current.content);
            }
          },
        });
      } finally {
        setIsLoading(false);
        setStreamStatus(undefined);
      }
    },
    [chatId, createChat, refreshChats, router, contextState.state, refreshLocalMessages]
  );

  // Use local messages which are always up-to-date
  const displayMessages = localMessages;

  return (
    <ResizablePanelGroup
      direction="horizontal"
      className="h-screen bg-background"
    >
      {/* Resizable Sidebar Panel */}
      <ResizablePanel
        defaultSize={20}
        minSize={15}
        maxSize={35}
        className="min-w-0"
      >
        <ChatSidebar activeChatId={chatId || activeChatIdState || undefined} />
      </ResizablePanel>

      <ResizableHandle withHandle />

      {/* Main Chat Panel */}
      <ResizablePanel defaultSize={80} minSize={50} className="min-w-0">
        <main className="flex h-full flex-col min-h-0 min-w-0">
          {/* Chat Messages*/}
          <ChatView messages={displayMessages} isLoading={isLoading} streamStatus={streamStatus} />

          {/* Bottom Area: Context Bar + Composer*/}
          <div className="shrink-0 border-t border-border p-4 space-y-2">
            <ContextBar
              state={contextState.state}
              onProcessChange={contextState.setProcess}
              onRoleChange={contextState.setRole}
              onTaskChange={contextState.setTask}
              onScopeChange={contextState.setScope}
              onClearProcess={contextState.clearProcess}
              onClearTask={contextState.clearTask}
            />

            <Composer onSend={handleSend} isLoading={isLoading} />
          </div>
        </main>
      </ResizablePanel>
    </ResizablePanelGroup>
  );
}
