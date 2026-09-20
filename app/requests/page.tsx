import { AppShell } from '@/components/app-shell';
import { RequestTable } from '@/components/request-table';
import { prisma } from '@/lib/db';
import { redirect } from 'next/navigation';
import { getAuthSession } from '@/lib/auth';

export default async function RequestsPage() {
  const session = await getAuthSession();
  if (!session?.user) {
    redirect('/login');
  }

  const requests = await prisma.request.findMany({
    include: { user: true },
    orderBy: { createdAt: 'desc' }
  });

  return (
    <AppShell>
      <div className="px-4 py-8 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl space-y-6">
          <div className="rounded-2xl border border-white/10 bg-surface/70 p-6 shadow-glow">
            <h1 className="text-2xl font-semibold">Requests Management</h1>
            <p className="mt-2 text-sm text-white/60">Review, approve, reject, and track Gmail service requests.</p>
          </div>
          <RequestTable initialRequests={requests as any} />
        </div>
      </div>
    </AppShell>
  );
}
