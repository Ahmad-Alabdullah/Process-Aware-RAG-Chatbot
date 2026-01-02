"use client";

import { useState } from "react";
import Link from "next/link";
import { Search, MessageSquare, ExternalLink } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

// TODO: Replace with real data from backend
const mockChats = [
  {
    id: "chat-1",
    session_id: "anon_a3f2c1e8",
    title: "Urlaubsantrag einreichen",
    message_count: 8,
    created_at: "2026-01-02T10:30:00Z",
    updated_at: "2026-01-02T12:15:00Z",
  },
  {
    id: "chat-2",
    session_id: "anon_b5d4e2f9",
    title: "Dienstreise genehmigen",
    message_count: 12,
    created_at: "2026-01-01T14:20:00Z",
    updated_at: "2026-01-02T09:45:00Z",
  },
  {
    id: "chat-3",
    session_id: "anon_c7f6a3b0",
    title: "Bestellung aufgeben",
    message_count: 5,
    created_at: "2025-12-30T16:00:00Z",
    updated_at: "2025-12-30T16:30:00Z",
  },
];

export default function AdminChatsPage() {
  const [search, setSearch] = useState("");

  const filteredChats = mockChats.filter(
    (chat) =>
      chat.title.toLowerCase().includes(search.toLowerCase()) ||
      chat.session_id.toLowerCase().includes(search.toLowerCase())
  );

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString("de-DE", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Alle Chats</h1>
        <Badge variant="secondary">{mockChats.length} Chats</Badge>
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Suche nach Titel oder Session-ID..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-10"
        />
      </div>

      {/* Table */}
      <div className="rounded-lg border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Session</TableHead>
              <TableHead>Titel</TableHead>
              <TableHead className="text-center">Nachrichten</TableHead>
              <TableHead>Erstellt</TableHead>
              <TableHead>Letzte Aktivität</TableHead>
              <TableHead className="w-12"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredChats.map((chat) => (
              <TableRow key={chat.id}>
                <TableCell>
                  <code className="text-xs bg-muted px-1.5 py-0.5 rounded">
                    {chat.session_id}
                  </code>
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-2">
                    <MessageSquare className="h-4 w-4 text-muted-foreground" />
                    {chat.title}
                  </div>
                </TableCell>
                <TableCell className="text-center">
                  <Badge variant="secondary">{chat.message_count}</Badge>
                </TableCell>
                <TableCell className="text-muted-foreground text-sm">
                  {formatDate(chat.created_at)}
                </TableCell>
                <TableCell className="text-muted-foreground text-sm">
                  {formatDate(chat.updated_at)}
                </TableCell>
                <TableCell>
                  <Link
                    href={`/admin/chats/${chat.id}`}
                    className="text-primary hover:underline"
                  >
                    <ExternalLink className="h-4 w-4" />
                  </Link>
                </TableCell>
              </TableRow>
            ))}
            {filteredChats.length === 0 && (
              <TableRow>
                <TableCell
                  colSpan={6}
                  className="text-center text-muted-foreground py-8"
                >
                  Keine Chats gefunden
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
