import { NextResponse } from 'next/server';
import { prisma } from '@/lib/db';

export async function GET() {
  const logs = await prisma.logEntry.findMany({
    orderBy: { createdAt: 'desc' }
  });

  return NextResponse.json(logs);
}
