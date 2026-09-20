import { NextResponse } from 'next/server';
import { prisma } from '@/lib/db';

export async function GET() {
  const users = await prisma.user.findMany({
    include: { requests: true },
    orderBy: { createdAt: 'desc' }
  });

  return NextResponse.json(users);
}
