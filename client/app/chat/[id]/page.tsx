import { ChatContainer } from "@/components/feature/chat/chat-container";

interface ChatIdPageProps {
  params: Promise<{ id: string }>;
}

export default async function ChatIdPage({ params }: ChatIdPageProps) {
  const { id } = await params;
  return <ChatContainer chatId={id} />;
}
