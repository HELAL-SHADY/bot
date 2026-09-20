import { AppShell } from '@/components/app-shell';
import { prisma } from '@/lib/db';
import { redirect } from 'next/navigation';
import { getAuthSession } from '@/lib/auth';

export default async function LogsPage() {
  const session = await getAuthSession();
  if (!session?.user) {
    redirect('/login');
  }

  const logs = await prisma.logEntry.findMany({
    orderBy: { createdAt: 'desc' }
  });

  return (
    <AppShell>
      <div className="px-4 py-8 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl space-y-6">
          <div className="rounded-2xl border border-white/10 bg-surface/70 p-6 shadow-glow">
            <h1 className="text-2xl font-semibold">Admin Logs</h1>
            <p className="mt-2 text-sm text-white/60">Track actions, timestamps, and moderation history.</p>
          </div>

          <div className="overflow-hidden rounded-2xl border border-white/10 bg-surface/80">
            <table className="min-w-full divide-y divide-white/10 text-sm">
              <thead className="bg-white/5 text-left text-white/60">
                <tr>
                  <th className="px-4 py-3">Action</th>
                  <th className="px-4 py-3">Details</th>
                  <th className="px-4 py-3">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/10">
                {logs.map((log) => (
                  <tr key={log.id} className="bg-background/20">
                    <td className="px-4 py-3">{log.action}</td>
                    <td className="px-4 py-3">{log.details}</td>
                    <td className="px-4 py-3">{new Date(log.createdAt).toLocaleString()}</td>
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
