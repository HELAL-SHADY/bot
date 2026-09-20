import { NextResponse } from 'next/server';
import { prisma } from '@/lib/db';
import { z } from 'zod';

const bodySchema = z.object({
  telegramId: z.string().min(1),
  username: z.string().optional(),
  firstName: z.string().optional(),
  gmail: z.string().email()
});

export async function GET() {
  const requests = await prisma.request.findMany({
    include: { user: true },
    orderBy: { createdAt: 'desc' }
  });

  return NextResponse.json(requests);
}

export async function POST(request: Request) {
  const json = await request.json();
  const parsed = bodySchema.safeParse(json);

  if (!parsed.success) {
    return NextResponse.json({ error: 'Validation failed' }, { status: 400 });
  }

  let user = await prisma.user.findUnique({ where: { telegramId: parsed.data.telegramId } });

  if (!user) {
    user = await prisma.user.create({
      data: {
        telegramId: parsed.data.telegramId,
        username: parsed.data.username ?? null,
        firstName: parsed.data.firstName ?? null
      }
    });
  }

  const created = await prisma.request.create({
    data: {
      userId: user.id,
      gmail: parsed.data.gmail,
      status: 'pending'
    }
  });

  return NextResponse.json(created, { status: 201 });
}
