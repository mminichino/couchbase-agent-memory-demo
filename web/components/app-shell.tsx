import Link from "next/link";
import { AppShellStatus } from "@/components/app-shell-status";
import { LayoutToggle } from "@/components/layout-toggle";
import { LogoutForm } from "@/components/logout-form";
import type { Account } from "@/lib/types";

type AppShellProps = {
  user: Account;
  children: React.ReactNode;
};

export function AppShell({ user, children }: AppShellProps) {
  return (
    <div className="flex h-[100dvh] max-h-[100dvh] flex-col overflow-hidden bg-canvas">
      <header className="sticky top-0 z-50 shrink-0 border-b border-border bg-panel/95 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-7xl items-center gap-3 px-4 md:px-6 mobile:h-auto mobile:flex-wrap mobile:gap-y-1 mobile:px-3 mobile:py-2 projector:h-[4.25rem] projector:max-w-none">
          <div className="min-w-0 flex-1">
            <p className="text-xs uppercase tracking-wide text-muted mobile:hidden">Couchbase AI Data Plane</p>
            <h1 className="text-sm font-semibold text-foreground mobile:truncate projector:text-base">
              Agent Memory + MCP + Agent Catalog
            </h1>
          </div>
          <AppShellStatus />
          <nav className="flex shrink-0 items-center gap-3 mobile:order-last mobile:w-full mobile:gap-1 projector:gap-2">
            <LayoutToggle />
            <Link
              href="/app"
              className="rounded-md px-3 py-2 text-sm text-foreground transition hover:bg-panelMuted mobile:flex-1 mobile:px-2 mobile:py-3 mobile:text-center projector:px-4 projector:py-2.5"
            >
              Chat
            </Link>
            <Link
              href="/app/settings"
              className="rounded-md px-3 py-2 text-sm text-foreground transition hover:bg-panelMuted mobile:flex-1 mobile:px-2 mobile:py-3 mobile:text-center projector:px-4 projector:py-2.5"
            >
              Settings
            </Link>
            <Link
              href="/admin/accounts"
              className="rounded-md px-3 py-2 text-sm text-foreground transition hover:bg-panelMuted mobile:flex-1 mobile:px-2 mobile:py-3 mobile:text-center projector:px-4 projector:py-2.5"
            >
              Accounts
            </Link>
            <div className="hidden text-right text-xs text-muted md:block mobile:hidden projector:text-sm">
              <p>{user.first_name || user.user_id}</p>
              <p>{user.user_id}</p>
            </div>
            <LogoutForm />
          </nav>
        </div>
      </header>
      <main className="mx-auto flex min-h-0 w-full max-w-7xl flex-1 flex-col overflow-hidden px-4 py-4 md:px-6 lg:max-w-[90rem] mobile:max-w-none mobile:px-2 mobile:py-2 projector:max-w-none projector:py-3">
        {children}
      </main>
    </div>
  );
}
