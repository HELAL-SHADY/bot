import { NextResponse } from 'next/server';
import { prisma } from '@/lib/db';
import { z } from 'zod';

const actionSchema = z.object({
  action: z.enum(['approve', 'reject']),
  rejectReason: z.string().optional()
});

export async function PATCH(request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const json = await request.json();
  const parsed = actionSchema.safeParse(json);

  if (!parsed.success) {
    return NextResponse.json({ error: 'Validation failed' }, { status: 400 });
  }

  const requestRecord = await prisma.request.findUnique({ where: { id } });
  if (!requestRecord) {
    return NextResponse.json({ error: 'Request not found' }, { status: 404 });
  }

  const updated = await prisma.request.update({
    where: { id },
    data: {
      status: parsed.data.action === 'approve' ? 'approved' : 'rejected',
      rejectReason: parsed.data.action === 'reject' ? parsed.data.rejectReason ?? 'No reason provided' : null
    }
  });

  await prisma.logEntry.create({
    data: {
      action: parsed.data.action === 'approve' ? 'approve_request' : 'reject_request',
      details: `Request ${id} ${parsed.data.action === 'approve' ? 'approved' : 'rejected'}`
    }
  });

  return NextResponse.json(updated);
}
