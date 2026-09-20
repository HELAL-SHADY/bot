"use client";

import { useMemo, useState } from 'react';
import { Search } from 'lucide-react';

interface RequestRecord {
  id: string;
  gmail: string;
  status: string;
  createdAt: string;
  rejectReason?: string | null;
  user: {
    telegramId: string;
    username?: string | null;
  };
}

export function RequestTable({ initialRequests }: { initialRequests: RequestRecord[] }) {
  const [requests, setRequests] = useState(initialRequests);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [rejectReason, setRejectReason] = useState('');

  const filtered = useMemo(() => {
    return requests.filter((request) => {
      const matchesSearch = [request.id, request.gmail, request.user.telegramId, request.user.username]
        .join(' ')
        .toLowerCase()
        .includes(search.toLowerCase());
      const matchesStatus = statusFilter === 'all' || request.status === statusFilter;
      return matchesSearch && matchesStatus;
    });
  }, [requests, search, statusFilter]);

  async function updateStatus(id: string, action: 'approve' | 'reject') {
    const payload = action === 'reject' ? { action, rejectReason } : { action };
    const response = await fetch(`/api/requests/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (response.ok) {
      const updated = await response.json();
      setRequests((current) => current.map((item) => (item.id === id ? { ...item, ...updated } : item)));
      setSelectedId(null);
      setRejectReason('');
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div className="relative w-full md:max-w-md">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/40" />
          <input
            className="w-full rounded-xl border border-white/10 bg-background/60 py-3 pl-9 pr-3 text-sm outline-none"
            placeholder="Search requests"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <select
          className="rounded-xl border border-white/10 bg-background/60 px-4 py-3 text-sm outline-none"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          <option value="all">All statuses</option>
          <option value="pending">Pending</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
        </select>
      </div>

      <div className="overflow-hidden rounded-2xl border border-white/10 bg-surface/80">
        <table className="min-w-full divide-y divide-white/10 text-sm">
          <thead className="bg-white/5 text-left text-white/60">
            <tr>
              <th className="px-4 py-3">Request ID</th>
              <th className="px-4 py-3">Telegram ID</th>
              <th className="px-4 py-3">Username</th>
              <th className="px-4 py-3">Gmail</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Date</th>
              <th className="px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/10">
            {filtered.map((request) => (
              <tr key={request.id} className="bg-background/20">
                <td className="px-4 py-3">{request.id.slice(0, 8)}</td>
                <td className="px-4 py-3">{request.user.telegramId}</td>
                <td className="px-4 py-3">{request.user.username ?? '—'}</td>
                <td className="px-4 py-3">{request.gmail}</td>
                <td className="px-4 py-3">
                  <span className={`rounded-full px-2.5 py-1 text-xs ${request.status === 'approved' ? 'bg-emerald-500/20 text-emerald-300' : request.status === 'rejected' ? 'bg-rose-500/20 text-rose-300' : 'bg-amber-500/20 text-amber-300'}`}>
                    {request.status}
                  </span>
                </td>
                <td className="px-4 py-3">{new Date(request.createdAt).toLocaleDateString()}</td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-2">
                    <button className="rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-medium text-white" onClick={() => updateStatus(request.id, 'approve')}>
                      Approve
                    </button>
                    <button className="rounded-lg bg-rose-600 px-3 py-1.5 text-xs font-medium text-white" onClick={() => { setSelectedId(request.id); setRejectReason(''); }}>
                      Reject
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {selectedId ? (
        <div className="rounded-2xl border border-white/10 bg-surface/80 p-5">
          <h3 className="font-semibold">Reject reason</h3>
          <textarea
            className="mt-3 w-full rounded-xl border border-white/10 bg-background/60 px-4 py-3 text-sm outline-none"
            rows={4}
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
            placeholder="Add a rejection reason"
          />
          <div className="mt-4 flex gap-3">
            <button className="rounded-xl bg-rose-600 px-4 py-2 text-sm font-medium text-white" onClick={() => updateStatus(selectedId, 'reject')}>
              Submit rejection
            </button>
            <button className="rounded-xl border border-white/10 px-4 py-2 text-sm text-white/70" onClick={() => setSelectedId(null)}>
              Cancel
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
