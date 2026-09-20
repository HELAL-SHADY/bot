import { AppShell } from '@/components/app-shell';
import { prisma } from '@/lib/db';
import { redirect } from 'next/navigation';
import { getAuthSession } from '@/lib/auth';

export default async function UsersPage() {
  const session = await getAuthSession();
  if (!session?.user) {
    redirect('/login');
  }

  const users = await prisma.user.findMany({
    include: { requests: true },
    orderBy: { createdAt: 'desc' }
  });

  return (
    <AppShell>
      <div className="px-4 py-8 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl space-y-6">
          <div className="rounded-2xl border border-white/10 bg-surface/70 p-6 shadow-glow">
            <h1 className="text-2xl font-semibold">Users Management</h1>
            <p className="mt-2 text-sm text-white/60">Manage users, apply bans, and view their request activity.</p>
          </div>

          <div className="overflow-hidden rounded-2xl border border-white/10 bg-surface/80">
            <table className="min-w-full divide-y divide-white/10 text-sm">
              <thead className="bg-white/5 text-left text-white/60">
                <tr>
                  <th className="px-4 py-3">Telegram ID</th>
                  <th className="px-4 py-3">Username</th>
                  <th className="px-4 py-3">Registration Date</th>
                  <th className="px-4 py-3">Requests</th>
                  <th className="px-4 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/10">
                {users.map((user) => (
                  <tr key={user.id} className="bg-background/20">
                    <td className="px-4 py-3">{user.telegramId}</td>
                    <td className="px-4 py-3">{user.username ?? '—'}</td>
                    <td className="px-4 py-3">{new Date(user.createdAt).toLocaleDateString()}</td>
                    <td className="px-4 py-3">{user.requests.length}</td>
                    <td className="px-4 py-3">
                      <a href={`/users/${user.id}`} className="text-accent underline-offset-2 hover:underline">
                        View profile
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
