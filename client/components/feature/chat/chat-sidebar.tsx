"use client";

import { useRouter } from "next/navigation";
import { Plus, MessageSquare, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useChats } from "@/hooks/use-chats";
import { cn } from "@/lib/utils";

interface ChatSidebarProps {
  activeChatId?: string;
}

export function ChatSidebar({ activeChatId }: ChatSidebarProps) {
  const router = useRouter();
  const { chats, createChat, deleteChat } = useChats();

  const handleNewChat = () => {
    const chat = createChat();
    router.push(`/chat/${chat.id}`);
  };

  const handleOpenChat = (chatId: string) => {
    router.push(`/chat/${chatId}`);
  };

  const handleDeleteChat = (e: React.MouseEvent, chatId: string) => {
    e.stopPropagation();
    deleteChat(chatId);
    if (chatId === activeChatId) {
      router.push("/chat");
    }
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffDays = Math.floor(
      (now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24)
    );

    if (diffDays === 0) {
      return date.toLocaleTimeString("de-DE", {
        hour: "2-digit",
        minute: "2-digit",
      });
    } else if (diffDays === 1) {
      return "Gestern";
    } else if (diffDays < 7) {
      return date.toLocaleDateString("de-DE", { weekday: "short" });
    }
    return date.toLocaleDateString("de-DE", { day: "2-digit", month: "2-digit" });
  };

  return (
    <aside className="flex h-full w-full flex-col border-r border-border bg-sidebar">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border">
        <h1 className="font-semibold text-lg">Chats</h1>
        <Button
          variant="ghost"
          size="icon"
          onClick={handleNewChat}
          title="Neuer Chat"
        >
          <Plus className="h-5 w-5" />
        </Button>
      </div>

      {/* Chat List */}
      <ScrollArea className="flex-1">
        <div className="p-2 space-y-1">
          {chats.length === 0 ? (
            <div className="p-4 text-center text-muted-foreground text-sm">
              Keine Chats vorhanden.
              <br />
              Starte einen neuen Chat!
            </div>
          ) : (
            chats.map((chat) => (
              <div
                key={chat.id}
                onClick={() => handleOpenChat(chat.id)}
                className={cn(
                  "group flex items-start gap-2 rounded-lg p-2.5 cursor-pointer transition-colors",
                  "hover:bg-sidebar-accent",
                  activeChatId === chat.id && "bg-sidebar-accent"
                )}
              >
                <MessageSquare className="h-4 w-4 mt-0.5 shrink-0 text-muted-foreground" />
                <div className="flex-1 min-w-0 overflow-hidden">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium truncate flex-1">
                      {chat.title}
                    </span>
                    <span className="text-[10px] text-muted-foreground shrink-0 tabular-nums">
                      {formatTime(chat.updated_at)}
                    </span>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-5 w-5 opacity-0 group-hover:opacity-100 shrink-0 -mt-0.5"
                  onClick={(e) => handleDeleteChat(e, chat.id)}
                  title="Chat löschen"
                >
                  <Trash2 className="h-3 w-3" />
                </Button>
              </div>
            ))
          )}
        </div>
      </ScrollArea>
    </aside>
  );
}
