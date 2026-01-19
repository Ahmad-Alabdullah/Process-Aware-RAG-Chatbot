import { ChatContainer } from "@/components/feature/chat/chat-container";

interface ChatPageProps {
  params: Promise<{ id?: string[] }>;
}

/**
 * Optional Catch-All Route for Chat
 * 
 * This handles BOTH:
 * - /chat (new chat, id = undefined)
 * - /chat/abc123 (existing chat, id = ["abc123"])
 * 
 * Using [[...id]] instead of separate pages prevents component remount
 * when navigating from /chat to /chat/[id] after creating a new chat.
 * 
 * This is the recommended pattern from Vercel AI SDK for chat applications.
 */
export default async function ChatPage({ params }: ChatPageProps) {
  const { id } = await params;
  // id is an array for catch-all routes, get first element or undefined
  const chatId = id?.[0];
  return <ChatContainer chatId={chatId} />;
}
