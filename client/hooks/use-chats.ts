"use client";

import { useState, useCallback, useEffect } from "react";
import type { Chat, Message } from "@/types";
import {
  getChats,
  getChat,
  createChat as createChatApi,
  updateChat,
  deleteChat as deleteChatApi,
  getMessages,
  addMessage as addMessageApi,
  updateLastMessage as updateLastMessageApi,
} from "@/lib/api/chats";

export function useChats() {
  const [chats, setChats] = useState<Chat[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Load chats on mount
  useEffect(() => {
    setChats(getChats());
    setIsLoading(false);
    
    // Listen for chat updates from other components
    const handleChatUpdate = () => {
      setChats(getChats());
    };
    window.addEventListener("chats-updated", handleChatUpdate);
    return () => window.removeEventListener("chats-updated", handleChatUpdate);
  }, []);

  const createChat = useCallback((title?: string): Chat => {
    const chat = createChatApi(title);
    setChats(getChats());
    // Notify other components
    window.dispatchEvent(new Event("chats-updated"));
    return chat;
  }, []);

  const deleteChat = useCallback((chatId: string) => {
    deleteChatApi(chatId);
    setChats(getChats());
    // Notify other components
    window.dispatchEvent(new Event("chats-updated"));
  }, []);

  const renameChat = useCallback((chatId: string, title: string) => {
    updateChat(chatId, { title });
    setChats(getChats());
    // Notify other components
    window.dispatchEvent(new Event("chats-updated"));
  }, []);

  const refreshChats = useCallback(() => {
    setChats(getChats());
    // Notify other components
    window.dispatchEvent(new Event("chats-updated"));
  }, []);

  return {
    chats,
    isLoading,
    createChat,
    deleteChat,
    renameChat,
    refreshChats,
  };
}

export function useChatMessages(chatId: string | null) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [chat, setChat] = useState<Chat | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load messages when chatId changes
  useEffect(() => {
    if (!chatId) {
      setMessages([]);
      setChat(null);
      setIsLoading(false);
      return;
    }

    setChat(getChat(chatId));
    setMessages(getMessages(chatId));
    setIsLoading(false);
  }, [chatId]);

  const addMessage = useCallback(
    (message: Omit<Message, "id" | "chat_id" | "created_at">): Message | null => {
      if (!chatId) return null;
      const newMessage = addMessageApi(chatId, message);
      setMessages(getMessages(chatId));
      setChat(getChat(chatId));
      return newMessage;
    },
    [chatId]
  );

  const updateLastMessage = useCallback(
    (updates: Partial<Omit<Message, "id" | "chat_id" | "created_at">>): Message | null => {
      if (!chatId) return null;
      const updated = updateLastMessageApi(chatId, updates);
      setMessages(getMessages(chatId));
      return updated;
    },
    [chatId]
  );

  const refreshMessages = useCallback(() => {
    if (!chatId) return;
    setMessages(getMessages(chatId));
    setChat(getChat(chatId));
  }, [chatId]);

  return {
    chat,
    messages,
    isLoading,
    addMessage,
    updateLastMessage,
    refreshMessages,
  };
}

