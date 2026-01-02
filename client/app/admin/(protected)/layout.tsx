import { redirect } from "next/navigation";
import { getServerSession } from "next-auth";
import { authOptions } from "@/app/api/auth/[...nextauth]/route";
import { Button } from "@/components/ui/button";
import { LogOut, MessageSquare, LayoutDashboard, Settings } from "lucide-react";
import Link from "next/link";

export default async function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await getServerSession(authOptions);

  // Redirect to login if not authenticated
  if (!session?.user) {
    redirect("/admin/login");
  }

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <aside className="w-64 border-r border-border bg-sidebar flex flex-col">
        <div className="p-4 border-b border-border">
          <h1 className="font-bold text-lg">Admin Dashboard</h1>
          <p className="text-sm text-muted-foreground">{session.user.name}</p>
        </div>

        <nav className="flex-1 p-2 space-y-1">
          <Link
            href="/admin"
            className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors hover:bg-sidebar-accent"
          >
            <LayoutDashboard className="h-4 w-4" />
            Übersicht
          </Link>
          <Link
            href="/admin/chats"
            className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors hover:bg-sidebar-accent"
          >
            <MessageSquare className="h-4 w-4" />
            Alle Chats
          </Link>
          <Link
            href="/admin/settings"
            className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors hover:bg-sidebar-accent"
          >
            <Settings className="h-4 w-4" />
            Einstellungen
          </Link>
        </nav>

        <div className="p-2 border-t border-border">
          <form action="/api/auth/signout" method="POST">
            <Button variant="ghost" className="w-full justify-start gap-3" type="submit">
              <LogOut className="h-4 w-4" />
              Abmelden
            </Button>
          </form>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  );
}
