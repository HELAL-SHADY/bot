"use client";

import { useEffect, useMemo, useState } from 'react';
import { AreaChart, Area, ResponsiveContainer, XAxis, YAxis, Tooltip } from 'recharts';

interface DashboardStats {
  totalUsers: number;
  totalRequests: number;
  approvedRequests: number;
  rejectedRequests: number;
  todayRequests: number;
}

export function DashboardHome() {
  const [stats, setStats] = useState<DashboardStats>({
    totalUsers: 0,
    totalRequests: 0,
    approvedRequests: 0,
    rejectedRequests: 0,
    todayRequests: 0
  });
  const [requests, setRequests] = useState<any[]>([]);
  const [users, setUsers] = useState<any[]>([]);

  useEffect(() => {
    async function load() {
      const [requestsRes, usersRes] = await Promise.all([fetch('/api/requests'), fetch('/api/users')]);
      const requestsData = await requestsRes.json();
      const usersData = await usersRes.json();
      setRequests(requestsData);
      setUsers(usersData);

      const today = new Date();
      const todayStr = today.toISOString().slice(0, 10);
      const todayCount = requestsData.filter((item: any) => item.createdAt.slice(0, 10) === todayStr).length;

      setStats({
        totalUsers: usersData.length,
        totalRequests: requestsData.length,
        approvedRequests: requestsData.filter((item: any) => item.status === 'approved').length,
        rejectedRequests: requestsData.filter((item: any) => item.status === 'rejected').length,
        todayRequests: todayCount
      });
    }

    load();
  }, []);

  const chartData = useMemo(() => {
    const buckets = Array.from({ length: 7 }, (_, index) => {
      const date = new Date();
      date.setDate(date.getDate() - (6 - index));
      const key = date.toISOString().slice(0, 10);
      const count = requests.filter((item: any) => item.createdAt.slice(0, 10) === key).length;
      return { day: key.slice(5), requests: count };
    });
    return buckets;
  }, [requests]);

  return (
    <main className="min-h-screen bg-background px-4 py-8 text-white sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl space-y-6">
        <header className="rounded-2xl border border-white/10 bg-surface/70 p-6 shadow-glow backdrop-blur">
          <p className="text-sm uppercase tracking-[0.3em] text-accent">Admin Dashboard</p>
          <h1 className="mt-2 text-3xl font-semibold">Telegram Gmail Service Bot</h1>
          <p className="mt-2 text-sm text-white/60">Monitor requests, manage users, and track admin activity in real time.</p>
        </header>

        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
          {[
            { label: 'Total Users', value: stats.totalUsers },
            { label: 'Total Requests', value: stats.totalRequests },
            { label: 'Approved Requests', value: stats.approvedRequests },
            { label: 'Rejected Requests', value: stats.rejectedRequests },
            { label: "Today's Requests", value: stats.todayRequests }
          ].map((item) => (
            <div key={item.label} className="rounded-2xl border border-white/10 bg-surface/80 p-5 shadow-glow">
              <p className="text-sm text-white/60">{item.label}</p>
              <p className="mt-3 text-3xl font-semibold">{item.value}</p>
            </div>
          ))}
        </section>

        <section className="grid gap-6 lg:grid-cols-[2fr_1fr]">
          <div className="rounded-2xl border border-white/10 bg-surface/80 p-6 shadow-glow">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold">Daily Activity</h2>
              <p className="text-sm text-white/60">Last 7 days</p>
            </div>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData}>
                  <XAxis dataKey="day" stroke="#9CA3AF" />
                  <YAxis stroke="#9CA3AF" />
                  <Tooltip />
                  <Area type="monotone" dataKey="requests" stroke="#4F46E5" fill="#4F46E5" fillOpacity={0.24} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="rounded-2xl border border-white/10 bg-surface/80 p-6 shadow-glow">
            <h2 className="text-lg font-semibold">Overview</h2>
            <div className="mt-6 space-y-3">
              <div className="rounded-xl border border-white/10 bg-background/60 p-4">
                <p className="text-sm text-white/60">Pending</p>
                <p className="mt-2 text-2xl font-semibold">{requests.filter((item: any) => item.status === 'pending').length}</p>
              </div>
              <div className="rounded-xl border border-white/10 bg-background/60 p-4">
                <p className="text-sm text-white/60">Banned Users</p>
                <p className="mt-2 text-2xl font-semibold">{users.filter((item: any) => item.isBanned).length}</p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
