# Frontend Setup Guide

## Installation

1. **Install dependencies:**
   ```bash
   cd apps/web
   npm install
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env.local
   # Edit .env.local with your settings
   ```

3. **Run development server:**
   ```bash
   npm run dev
   ```

   Open [http://localhost:3000](http://localhost:3000)

## Technologies

- **Next.js 14** - App Router with React Server Components
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first styling
- **shadcn/ui** - Component library (based on Radix UI)
- **React Flow** - Workflow visualization
- **Zustand** - State management
- **SWR** - Data fetching and caching
- **React Hook Form** - Form handling

## Project Structure

```
apps/web/
├── src/
│   ├── app/           # Next.js app router pages
│   ├── components/    # React components
│   │   └── ui/        # shadcn/ui components
│   ├── lib/           # Utilities and API client
│   ├── hooks/         # Custom React hooks
│   ├── store/         # Zustand stores
│   └── types/         # TypeScript type definitions
├── public/            # Static assets
└── package.json
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm start` - Start production server
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript checks

## Component Library

shadcn/ui components are installed in `components/ui/`:

- button, card, input, badge

Add more components manually by creating files in `src/components/ui/` or use:
```bash
npx shadcn@latest add [component-name]
```

Note: The shadcn CLI is configured for pnpm. If using npm, you may need to add components manually.

## Styling

Tailwind CSS with design tokens defined in `globals.css`.

Theme colors are CSS variables that support dark mode.

## API Integration

Use the `AdapterClient` class from `lib/api-client.ts`:

```typescript
import { apiClient } from '@/lib/api-client'

// Set API key
apiClient.setApiKey('your-api-key')

// Fetch data
const tenant = await apiClient.getCurrentTenant()
const logs = await apiClient.getActionLogs()
```

## State Management

Use Zustand for global state:

```typescript
import { create } from 'zustand'

interface AppState {
  apiKey: string | null
  setApiKey: (key: string) => void
}

export const useAppStore = create<AppState>((set) => ({
  apiKey: null,
  setApiKey: (apiKey) => set({ apiKey }),
}))
```

## Type Safety

Import types from `@/types`:

```typescript
import type { Tenant, ActionLog } from '@/types'
```

Types are synchronized with backend schema.

## Environment Variables

Create `.env.local` file:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Development Workflow

1. Start the backend adapter: `cd ../adapter && uvicorn src.main:app --reload`
2. Start the frontend: `npm run dev`
3. Open http://localhost:3000

## Troubleshooting

### TypeScript Errors

Run type check:
```bash
npm run type-check
```

### Component Imports Not Working

Verify path aliases in `tsconfig.json`:
```json
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

### Tailwind Not Working

1. Verify `tailwind.config.ts` exists
2. Check `postcss.config.js` is present
3. Ensure `globals.css` is imported in `layout.tsx`

### Package Installation Issues

If you see pnpm errors, use npm with `--legacy-peer-deps`:
```bash
npm install --legacy-peer-deps