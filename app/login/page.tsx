"use client";

import { signIn } from 'next-auth/react';
import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const router = useRouter();

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const result = await signIn('credentials', { redirect: false, email, password });
    if (result?.ok) {
      router.push('/');
      router.refresh();
    } else {
      setError('Invalid email or password');
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-6">
      <div className="w-full max-w-md rounded-2xl border border-white/10 bg-surface/80 p-8 shadow-glow backdrop-blur">
        <h1 className="text-2xl font-semibold">Admin Login</h1>
        <p className="mt-2 text-sm text-white/60">Secure access to the Telegram Gmail Bot control panel.</p>
        <form className="mt-8 space-y-4" onSubmit={onSubmit}>
          <input
            className="w-full rounded-xl border border-white/10 bg-background/60 px-4 py-3 outline-none ring-0"
            placeholder="Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <input
            className="w-full rounded-xl border border-white/10 bg-background/60 px-4 py-3 outline-none ring-0"
            placeholder="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          {error ? <p className="text-sm text-red-400">{error}</p> : null}
          <button className="w-full rounded-xl bg-accent px-4 py-3 font-medium text-white transition hover:opacity-90" type="submit">
            Sign in
          </button>
        </form>
      </div>
    </main>
  );
}
