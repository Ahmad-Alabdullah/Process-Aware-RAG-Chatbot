import Link from "next/link";
import { ArrowLeft, Bot, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";

// TODO: Fetch from backend admin endpoint
const mockChat = {
  id: "chat-1",
  session_id: "anon_a3f2c1e8",
  title: "Urlaubsantrag einreichen",
  created_at: "2026-01-02T10:30:00Z",
};

const mockMessages = [
  {
    id: "msg-1",
    role: "user" as const,
    content: "Wie reiche ich einen Urlaubsantrag ein?",
    created_at: "2026-01-02T10:30:00Z",
  },
  {
    id: "msg-2",
    role: "assistant" as const,
    content:
      "Um einen Urlaubsantrag einzureichen, müssen Sie folgende Schritte durchführen:\n\n1. **Antrag erstellen**: Öffnen Sie das Urlaubsportal und wählen Sie 'Neuer Antrag'\n2. **Daten eingeben**: Tragen Sie den gewünschten Zeitraum ein\n3. **Einreichen**: Senden Sie den Antrag zur Genehmigung\n\nIhr Vorgesetzter wird dann benachrichtigt.",
    created_at: "2026-01-02T10:31:00Z",
  },
  {
    id: "msg-3",
    role: "user" as const,
    content: "Wer muss den Antrag genehmigen?",
    created_at: "2026-01-02T10:32:00Z",
  },
  {
    id: "msg-4",
    role: "assistant" as const,
    content:
      "Der Antrag muss von Ihrem direkten Vorgesetzten genehmigt werden. Bei Abwesenheit kann auch ein Stellvertreter die Genehmigung erteilen.\n\nNach der Genehmigung erhalten Sie eine Bestätigungsmail.",
    created_at: "2026-01-02T10:33:00Z",
  },
];

interface AdminChatDetailPageProps {
  params: Promise<{ id: string }>;
}

export default async function AdminChatDetailPage({
  params,
}: AdminChatDetailPageProps) {
  const { id } = await params;

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="border-b p-4 flex items-center gap-4">
        <Link href="/admin/chats">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div className="flex-1">
          <h1 className="font-semibold">{mockChat.title}</h1>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <code className="bg-muted px-1.5 py-0.5 rounded text-xs">
              {mockChat.session_id}
            </code>
            <span>·</span>
            <span>Chat ID: {id}</span>
          </div>
        </div>
        <Badge variant="secondary">{mockMessages.length} Nachrichten</Badge>
      </div>

      {/* Messages */}
      <ScrollArea className="flex-1">
        <div className="max-w-3xl mx-auto p-6 space-y-4">
          {mockMessages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-3 ${
                message.role === "user" ? "flex-row-reverse" : ""
              }`}
            >
              <div
                className={`h-8 w-8 rounded-full flex items-center justify-center shrink-0 ${
                  message.role === "user"
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted text-muted-foreground"
                }`}
              >
                {message.role === "user" ? (
                  <User className="h-4 w-4" />
                ) : (
                  <Bot className="h-4 w-4" />
                )}
              </div>
              <div
                className={`rounded-lg p-4 max-w-[80%] ${
                  message.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted"
                }`}
              >
                <p className="whitespace-pre-wrap">{message.content}</p>
                <p className="text-xs opacity-50 mt-2">
                  {new Date(message.created_at).toLocaleTimeString("de-DE")}
                </p>
              </div>
            </div>
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}
