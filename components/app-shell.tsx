"use client";

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { signOut } from 'next-auth/react';
import { LayoutDashboard, ListChecks, Users, Logs, Settings, LogOut } from 'lucide-react';

const navItems = [
  { href: '/' as const, label: 'Home', icon: LayoutDashboard },
  { href: '/requests' as const, label: 'Requests', icon: ListChecks },
  { href: '/users' as const, label: 'Users', icon: Users },
  { href: '/logs' as const, label: 'Logs', icon: Logs },
  { href: '/settings' as const, label: 'Settings', icon: Settings }
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();

  return (
    <div className="min-h-screen bg-background text-white">
      <aside className="fixed inset-y-0 left-0 hidden w-72 border-r border-white/10 bg-surface/90 p-6 backdrop-blur lg:block">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent/20 text-accent">GB</div>
          <div>
            <p className="text-lg font-semibold">Gmail Bot</p>
            <p className="text-sm text-white/60">Admin Console</p>
          </div>
        </div>

        <nav className="mt-8 space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 rounded-xl px-4 py-3 text-sm transition ${active ? 'bg-accent text-white' : 'text-white/70 hover:bg-white/5 hover:text-white'}`}
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>

        <button
          onClick={() => signOut({ callbackUrl: '/login' })}
          className="mt-8 flex w-full items-center gap-3 rounded-xl border border-white/10 px-4 py-3 text-sm text-white/70 transition hover:bg-white/5"
        >
          <LogOut className="h-4 w-4" />
          Logout
        </button>
      </aside>

      <div className="lg:pl-72">
        <header className="border-b border-white/10 bg-background/80 px-4 py-4 backdrop-blur sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm uppercase tracking-[0.25em] text-accent">Operations Center</p>
              <h2 className="text-xl font-semibold">Control Panel</h2>
            </div>
            <button
              onClick={() => signOut({ callbackUrl: '/login' })}
              className="rounded-xl border border-white/10 bg-surface px-4 py-2 text-sm text-white/80 transition hover:bg-white/5"
            >
              Logout
            </button>
          </div>
        </header>
        <main>{children}</main>
      </div>
    </div>
  );
}
