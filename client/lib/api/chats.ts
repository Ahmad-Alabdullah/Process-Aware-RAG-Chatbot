import type { Chat, Message } from "@/types";

// Chat history is stored in localStorage for MVP
// TODO: Move to backend endpoints when available

const CHATS_KEY = "rag_chatbot_chats";
const MESSAGES_KEY = "rag_chatbot_messages";

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

/**
 * Get all chats for the current session
 */
export function getChats(): Chat[] {
  if (typeof window === "undefined") return [];
  const data = localStorage.getItem(CHATS_KEY);
  if (!data) return [];
  try {
    return JSON.parse(data) as Chat[];
  } catch {
    return [];
  }
}

/**
 * Get a single chat by ID
 */
export function getChat(chatId: string): Chat | null {
  const chats = getChats();
  return chats.find((c) => c.id === chatId) || null;
}

/**
 * Create a new chat
 */
export function createChat(title?: string): Chat {
  const chat: Chat = {
    id: generateId(),
    title: title || "New Chat",
    preview: "",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    message_count: 0,
  };

  const chats = getChats();
  chats.unshift(chat);
  localStorage.setItem(CHATS_KEY, JSON.stringify(chats));

  return chat;
}

/**
 * Update chat metadata
 */
export function updateChat(
  chatId: string,
  updates: Partial<Pick<Chat, "title" | "preview">>
): Chat | null {
  const chats = getChats();
  const index = chats.findIndex((c) => c.id === chatId);
  if (index === -1) return null;

  chats[index] = {
    ...chats[index],
    ...updates,
    updated_at: new Date().toISOString(),
  };

  localStorage.setItem(CHATS_KEY, JSON.stringify(chats));
  return chats[index];
}

/**
 * Delete a chat and its messages
 */
export function deleteChat(chatId: string): boolean {
  const chats = getChats();
  const filtered = chats.filter((c) => c.id !== chatId);
  if (filtered.length === chats.length) return false;

  localStorage.setItem(CHATS_KEY, JSON.stringify(filtered));

  // Also delete messages
  const allMessages = getAllMessages();
  const remainingMessages = Object.fromEntries(
    Object.entries(allMessages).filter(([id]) => !id.startsWith(chatId))
  );
  localStorage.setItem(MESSAGES_KEY, JSON.stringify(remainingMessages));

  return true;
}

/**
 * Get all messages (internal helper)
 */
function getAllMessages(): Record<string, Message[]> {
  if (typeof window === "undefined") return {};
  const data = localStorage.getItem(MESSAGES_KEY);
  if (!data) return {};
  try {
    return JSON.parse(data);
  } catch {
    return {};
  }
}

/**
 * Get messages for a chat
 */
export function getMessages(chatId: string): Message[] {
  const allMessages = getAllMessages();
  return allMessages[chatId] || [];
}

/**
 * Add a message to a chat
 */
export function addMessage(
  chatId: string,
  message: Omit<Message, "id" | "chat_id" | "created_at">
): Message {
  const fullMessage: Message = {
    ...message,
    id: generateId(),
    chat_id: chatId,
    created_at: new Date().toISOString(),
  };

  const allMessages = getAllMessages();
  if (!allMessages[chatId]) {
    allMessages[chatId] = [];
  }
  allMessages[chatId].push(fullMessage);
  localStorage.setItem(MESSAGES_KEY, JSON.stringify(allMessages));

  // Update chat preview and count
  const chats = getChats();
  const chatIndex = chats.findIndex((c) => c.id === chatId);
  if (chatIndex !== -1) {
    const preview =
      message.role === "user"
        ? message.content.slice(0, 100)
        : chats[chatIndex].preview;
    chats[chatIndex] = {
      ...chats[chatIndex],
      preview,
      message_count: allMessages[chatId].length,
      updated_at: new Date().toISOString(),
    };

    // Auto-title from first user message
    if (
      message.role === "user" &&
      chats[chatIndex].title === "New Chat" &&
      allMessages[chatId].length === 1
    ) {
      chats[chatIndex].title = message.content.slice(0, 50);
    }

    localStorage.setItem(CHATS_KEY, JSON.stringify(chats));
  }

  return fullMessage;
}

/**
 * Update the last message in a chat (for streaming updates)
 */
export function updateLastMessage(
  chatId: string,
  updates: Partial<Omit<Message, "id" | "chat_id" | "created_at">>
): Message | null {
  const allMessages = getAllMessages();
  const chatMessages = allMessages[chatId];
  
  if (!chatMessages || chatMessages.length === 0) return null;
  
  const lastIndex = chatMessages.length - 1;
  chatMessages[lastIndex] = {
    ...chatMessages[lastIndex],
    ...updates,
  };
  
  localStorage.setItem(MESSAGES_KEY, JSON.stringify(allMessages));
  return chatMessages[lastIndex];
}
