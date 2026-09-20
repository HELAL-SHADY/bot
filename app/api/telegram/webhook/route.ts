import { NextResponse } from 'next/server';
import { prisma } from '@/lib/db';

export async function POST(request: Request) {
  const body = await request.json();
  const message = body.message?.text;
  const chatId = body.message?.chat?.id;

  if (typeof message === 'string' && chatId) {
    await prisma.logEntry.create({
      data: {
        action: 'telegram_webhook',
        details: `Received message from ${chatId}: ${message}`
      }
    });
  }

  return NextResponse.json({ ok: true });
}
