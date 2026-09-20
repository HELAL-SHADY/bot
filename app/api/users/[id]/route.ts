import { NextResponse } from 'next/server';
import { prisma } from '@/lib/db';

export async function PATCH(request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const json = await request.json();
  const parsed = json as { isBanned?: boolean };

  const user = await prisma.user.update({
    where: { id },
    data: { isBanned: parsed.isBanned ?? false }
  });

  await prisma.logEntry.create({
    data: {
      action: parsed.isBanned ? 'ban_user' : 'unban_user',
      details: `User ${id} ${parsed.isBanned ? 'banned' : 'unbanned'}`
    }
  });

  return NextResponse.json(user);
}
