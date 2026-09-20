import { AppShell } from '@/components/app-shell';
import { prisma } from '@/lib/db';
import { redirect } from 'next/navigation';
import { getAuthSession } from '@/lib/auth';

export default async function UserProfilePage({ params }: { params: Promise<{ id: string }> }) {
  const session = await getAuthSession();
  if (!session?.user) {
    redirect('/login');
  }

  const { id } = await params;
  const user = await prisma.user.findUnique({
    where: { id },
    include: { requests: true }
  });

  if (!user) {
    redirect('/users');
  }

  return (
    <AppShell>
      <div className="px-4 py-8 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl space-y-6">
          <div className="rounded-2xl border border-white/10 bg-surface/70 p-6 shadow-glow">
            <h1 className="text-2xl font-semibold">User Profile</h1>
            <p className="mt-2 text-sm text-white/60">Detailed view of the selected Telegram user and their request history.</p>
          </div>

          <div className="grid gap-6 lg:grid-cols-[1fr_2fr]">
            <div className="rounded-2xl border border-white/10 bg-surface/80 p-6 shadow-glow">
              <p className="text-sm text-white/60">Telegram ID</p>
              <p className="mt-2 text-xl font-semibold">{user.telegramId}</p>
              <p className="mt-4 text-sm text-white/60">Username</p>
              <p className="mt-2 text-lg">{user.username ?? '—'}</p>
              <p className="mt-4 text-sm text-white/60">First Name</p>
              <p className="mt-2 text-lg">{user.firstName ?? '—'}</p>
              <p className="mt-4 text-sm text-white/60">Banned</p>
              <p className="mt-2 text-lg">{user.isBanned ? 'Yes' : 'No'}</p>
            </div>

            <div className="rounded-2xl border border-white/10 bg-surface/80 p-6 shadow-glow">
              <h2 className="text-xl font-semibold">Request History</h2>
              <div className="mt-4 space-y-3">
                {user.requests.map((request) => (
                  <div key={request.id} className="rounded-xl border border-white/10 bg-background/60 p-4">
                    <div className="flex items-center justify-between">
                      <p className="font-medium">{request.gmail}</p>
                      <span className={`rounded-full px-2.5 py-1 text-xs ${request.status === 'approved' ? 'bg-emerald-500/20 text-emerald-300' : request.status === 'rejected' ? 'bg-rose-500/20 text-rose-300' : 'bg-amber-500/20 text-amber-300'}`}>
                        {request.status}
                      </span>
                    </div>
                    <p className="mt-2 text-sm text-white/60">{new Date(request.createdAt).toLocaleString()}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
