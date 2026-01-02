import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { MessageSquare, Users, TrendingUp } from "lucide-react";

// TODO: Replace with real data from backend admin endpoints
const mockStats = {
  totalChats: 42,
  totalMessages: 156,
  activeUsers: 12,
};

export default function AdminDashboardPage() {
  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Gesamte Chats
            </CardTitle>
            <MessageSquare className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{mockStats.totalChats}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Nachrichten
            </CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{mockStats.totalMessages}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Aktive Nutzer (7d)
            </CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{mockStats.activeUsers}</div>
          </CardContent>
        </Card>
      </div>

      {/* Info */}
      <Card>
        <CardHeader>
          <CardTitle>Hinweis</CardTitle>
        </CardHeader>
        <CardContent className="text-muted-foreground">
          <p>
            Das Admin-Dashboard zeigt derzeit Beispieldaten. Um echte Daten zu
            sehen, müssen die Backend-Admin-Endpoints implementiert werden:
          </p>
          <ul className="list-disc list-inside mt-2 space-y-1">
            <li>
              <code>GET /api/admin/chats</code> - Alle Chats aller Nutzer
            </li>
            <li>
              <code>GET /api/admin/chats/:id/messages</code> - Nachrichten eines
              Chats
            </li>
            <li>
              <code>GET /api/admin/stats</code> - Statistiken
            </li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
