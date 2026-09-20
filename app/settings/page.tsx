import { AppShell } from '@/components/app-shell';
import { redirect } from 'next/navigation';
import { getAuthSession } from '@/lib/auth';

export default async function SettingsPage() {
  const session = await getAuthSession();
  if (!session?.user) {
    redirect('/login');
  }

  return (
    <AppShell>
      <div className="px-4 py-8 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl space-y-6">
          <div className="rounded-2xl border border-white/10 bg-surface/70 p-6 shadow-glow">
            <h1 className="text-2xl font-semibold">Settings</h1>
            <p className="mt-2 text-sm text-white/60">Configure bot credentials, templates, and profile settings.</p>
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <div className="rounded-2xl border border-white/10 bg-surface/80 p-6 shadow-glow">
              <h2 className="text-xl font-semibold">Bot Configuration</h2>
              <div className="mt-4 space-y-4">
                <label className="block text-sm">
                  <span className="mb-2 block text-white/60">Bot Token</span>
                  <input className="w-full rounded-xl border border-white/10 bg-background/60 px-4 py-3 outline-none" defaultValue={process.env.BOT_TOKEN ?? ''} />
                </label>
                <label className="block text-sm">
                  <span className="mb-2 block text-white/60">Approval Message Template</span>
                  <textarea className="w-full rounded-xl border border-white/10 bg-background/60 px-4 py-3 outline-none" rows={4} defaultValue="Your Gmail access request has been approved." />
                </label>
              </div>
            </div>

            <div className="rounded-2xl border border-white/10 bg-surface/80 p-6 shadow-glow">
              <h2 className="text-xl font-semibold">Admin Profile</h2>
              <div className="mt-4 space-y-4">
                <label className="block text-sm">
                  <span className="mb-2 block text-white/60">Email</span>
                  <input className="w-full rounded-xl border border-white/10 bg-background/60 px-4 py-3 outline-none" defaultValue={session.user.email ?? ''} />
                </label>
                <label className="block text-sm">
                  <span className="mb-2 block text-white/60">Password</span>
                  <input className="w-full rounded-xl border border-white/10 bg-background/60 px-4 py-3 outline-none" type="password" placeholder="••••••••" />
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
