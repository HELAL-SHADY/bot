# Telegram Gmail Bot Admin Dashboard

A production-ready admin dashboard for a Telegram Gmail service bot built with Next.js 15, TypeScript, Tailwind, Prisma, PostgreSQL, NextAuth, Recharts, and Socket.IO.

## Features

- Secure admin login and protected routes
- Dashboard summary with real-time style cards and charts
- Requests management with search, filters, approve/reject actions
- Users management and profile view
- Admin logs system
- Settings page for bot token and templates
- Prisma-based persistence and REST APIs

## Quick start

1. Copy .env.example to .env and configure the database and auth values.
2. Install dependencies: npm install
3. Generate Prisma client: npx prisma generate
4. Run database migration: npx prisma migrate dev --name init
5. Start the app: npm run dev

## Deployment on Hostinger VPS

1. Install Node.js 20+, PostgreSQL, and Nginx.
2. Clone the repository and install dependencies.
3. Build the app: npm run build
4. Start with PM2: pm2 start npm --name gmail-bot-admin -- start
5. Configure Nginx as a reverse proxy to localhost:3000.
6. Set environment variables in the server environment.
