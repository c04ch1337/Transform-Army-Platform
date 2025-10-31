# Transform Army AI - Web Console

Next.js application providing the operator dashboard and client portal for Transform Army AI platform.

## Features

- **Operator Dashboard**: Real-time monitoring of agent activities
- **Tenant Management**: Configure and manage client tenants
- **Analytics**: Usage metrics and cost attribution
- **Approval Queue**: Review and approve agent actions
- **Template Editor**: Create and modify agent workflows

## Getting Started

### Prerequisites

- Node.js 18+
- pnpm

### Installation

```bash
# Install dependencies
pnpm install

# Copy environment variables
cp .env.example .env

# Start development server
pnpm dev
```

The application will be available at `http://localhost:3000`.

## Project Structure

```
src/
├── app/              # Next.js app directory (routes)
├── components/       # React components
│   ├── ui/          # Base UI components
│   ├── dashboard/   # Dashboard-specific components
│   ├── tenants/     # Tenant management components
│   └── analytics/   # Analytics components
├── lib/             # Utility functions
│   ├── api/         # API client
│   ├── hooks/       # Custom React hooks
│   └── utils/       # Helper functions
└── config/          # Configuration files
```

## Available Scripts

- `pnpm dev` - Start development server
- `pnpm build` - Build for production
- `pnpm start` - Start production server
- `pnpm lint` - Run ESLint
- `pnpm type-check` - Run TypeScript type checking
- `pnpm test` - Run tests

## Environment Variables

See [`.env.example`](.env.example) for required environment variables.

## Tech Stack

- **Framework**: Next.js 14 with App Router
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **Data Fetching**: TanStack Query (React Query)
- **Forms**: React Hook Form + Zod
- **Charts**: Recharts
- **Authentication**: NextAuth.js

## Development Guidelines

### Component Structure

```tsx
// Use functional components with TypeScript
export function ComponentName({ prop }: ComponentProps) {
  return <div>Content</div>;
}
```

### API Integration

```typescript
// Use the API client from lib/api
import { api } from '@/lib/api';

const data = await api.get('/endpoint');
```

### Styling

```tsx
// Use Tailwind CSS classes
<div className="flex items-center gap-4 p-4 bg-white rounded-lg shadow">
  Content
</div>
```

## Deployment

The application can be deployed to:

- Vercel (recommended for Next.js)
- Docker container
- Any Node.js hosting platform

See the [Deployment Guide](../../docs/deployment-guide.md) for details.