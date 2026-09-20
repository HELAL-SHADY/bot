import { redirect } from 'next/navigation';
import { getAuthSession } from '@/lib/auth';
import { DashboardHome } from '@/components/dashboard-home';

export default async function HomePage() {
  const session = await getAuthSession();

  if (!session?.user) {
    redirect('/login');
  }

  return <DashboardHome />;
}
