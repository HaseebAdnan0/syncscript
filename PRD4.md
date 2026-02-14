# PRD: SyncScript Frontend Foundation

## Introduction

Establish the Next.js 16 frontend foundation for SyncScript with a Bitcoin DeFi-inspired design system, core component library, and API/state management infrastructure. This PRD scaffolds a modern React application with TypeScript, Tailwind CSS v4, and a suite of accessible UI primitives.

**Version Note:** All dependency versions were verified against npm registry on 2026-02-14. Before installation, verify latest stable versions at [npmjs.com](https://www.npmjs.com/) as packages update frequently.

---

## Goals

- Initialize Next.js 16 App Router project with TypeScript strict mode
- Configure Tailwind CSS v4 with Bitcoin DeFi design tokens
- Integrate ShadCN UI with Radix primitives for accessible components
- Build core component library (Button, Card, Input, Badge)
- Set up layout components and dark-mode-only theme provider
- Implement Axios API client with JWT auto-refresh
- Configure Zustand auth store with localStorage persistence
- Set up React Query provider with sensible defaults
- Enforce code quality via ESLint 10 and Prettier

---

## Verified Package Versions (2026-02-14)

| Package | Version | Source |
|---------|---------|--------|
| next | ^16.1.6 | [npm](https://www.npmjs.com/package/next) |
| react | ^19.2.4 | [npm](https://www.npmjs.com/package/react) |
| react-dom | ^19.2.4 | [npm](https://www.npmjs.com/package/react-dom) |
| tailwindcss | ^4.1.0 | [npm](https://www.npmjs.com/package/tailwindcss) |
| @tanstack/react-query | ^5.90.21 | [npm](https://www.npmjs.com/package/@tanstack/react-query) |
| axios | ^1.13.5 | [npm](https://www.npmjs.com/package/axios) |
| zustand | ^5.0.11 | [npm](https://www.npmjs.com/package/zustand) |
| class-variance-authority | ^0.7.1 | [npm](https://www.npmjs.com/package/class-variance-authority) |
| clsx | ^2.1.1 | [npm](https://www.npmjs.com/package/clsx) |
| tailwind-merge | ^3.4.0 | [npm](https://www.npmjs.com/package/tailwind-merge) |
| lucide-react | ^0.563.0 | [npm](https://www.npmjs.com/package/lucide-react) |
| @radix-ui/react-dialog | ^1.1.15 | [npm](https://www.npmjs.com/package/@radix-ui/react-dialog) |
| @radix-ui/react-dropdown-menu | ^2.1.15 | [npm](https://www.npmjs.com/package/@radix-ui/react-dropdown-menu) |
| @radix-ui/react-tabs | ^1.1.15 | [npm](https://www.npmjs.com/package/@radix-ui/react-tabs) |
| @radix-ui/react-toast | ^1.2.15 | [npm](https://www.npmjs.com/package/@radix-ui/react-toast) |
| next-themes | ^0.4.6 | [npm](https://www.npmjs.com/package/next-themes) |
| typescript | ^5.9.3 | [npm](https://www.npmjs.com/package/typescript) |
| eslint | ^10.0.0 | [npm](https://www.npmjs.com/package/eslint) |
| prettier | ^3.8.1 | [npm](https://www.npmjs.com/package/prettier) |
| autoprefixer | ^10.4.24 | [npm](https://www.npmjs.com/package/autoprefixer) |

---

## User Stories

### US-001: Project Initialization & Core Dependencies
**Description:** As a developer, I want a Next.js 16 App Router project initialized with TypeScript and core dependencies so that I have a working foundation.

**Acceptance Criteria:**
- [x] Run `npx create-next-app@latest frontend --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"`
- [x] Navigate to `frontend/` directory
- [x] Install core dependencies: `npm install axios zustand @tanstack/react-query class-variance-authority clsx tailwind-merge lucide-react next-themes`
- [x] Install Radix UI: `npm install @radix-ui/react-dialog @radix-ui/react-dropdown-menu @radix-ui/react-tabs @radix-ui/react-toast`
- [x] Install dev dependencies: `npm install -D prettier`
- [x] Folder structure exists:
  ```
  frontend/
  ├── src/
  │   ├── app/
  │   ├── components/
  │   │   ├── ui/          (create empty)
  │   │   └── features/    (create empty)
  │   ├── lib/             (create empty)
  │   ├── hooks/           (create empty)
  │   └── styles/          (create empty)
  ```
- [x] `.gitignore` includes `node_modules/`, `.next/`, `.env.local`
- [x] Create `.env.local.example` with:
  ```
  NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
  NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
  ```
- [x] `npm run dev` starts without errors
- [x] Typecheck passes

---

### US-002: TypeScript Strict Configuration
**Description:** As a developer, I want TypeScript configured with strict mode and path aliases so that I have maximum type safety.

**Acceptance Criteria:**
- [x] Update `tsconfig.json` with strict compiler options:
  ```json
  {
    "compilerOptions": {
      "target": "ES2020",
      "lib": ["dom", "dom.iterable", "esnext"],
      "jsx": "preserve",
      "module": "esnext",
      "moduleResolution": "bundler",
      "resolveJsonModule": true,
      "isolatedModules": true,
      "strict": true,
      "noUnusedLocals": true,
      "noUnusedParameters": true,
      "noImplicitReturns": true,
      "skipLibCheck": true,
      "esModuleInterop": true,
      "allowSyntheticDefaultImports": true,
      "forceConsistentCasingInFileNames": true,
      "incremental": true,
      "paths": {
        "@/*": ["./src/*"]
      }
    }
  }
  ```
- [x] `npm run type-check` (add script if missing: `"type-check": "tsc --noEmit"`) passes
- [x] Typecheck passes

---

### US-003: Tailwind CSS Design System Configuration
**Description:** As a frontend developer, I want Tailwind CSS configured with Bitcoin DeFi design tokens so that all components follow the brand aesthetic.

**Acceptance Criteria:**
- [x] Tailwind CSS v4 is installed (comes with create-next-app)
- [x] Update `tailwind.config.ts` to extend theme with:
  ```typescript
  colors: {
    background: '#030304',
    surface: '#0F1115',
    foreground: '#FFFFFF',
    muted: '#94A3B8',
    border: '#1E293B',
    primary: '#F7931A',
    secondary: '#EA580C',
    accent: '#FFD600',
  },
  fontFamily: {
    heading: ['Space Grotesk', 'sans-serif'],
    body: ['Inter', 'sans-serif'],
    mono: ['JetBrains Mono', 'monospace'],
  },
  boxShadow: {
    'glow-orange': '0 0 20px -5px rgba(234, 88, 12, 0.5)',
    'glow-gold': '0 0 30px -10px rgba(255, 214, 0, 0.4)',
  }
  ```
- [x] Load Google Fonts in `app/layout.tsx` via `next/font/google`:
  - Space Grotesk (weights: 400, 700)
  - Inter (weights: 400, 500, 600)
  - JetBrains Mono (weights: 400, 500)
- [x] Update `src/styles/globals.css` (or `src/app/globals.css`) with:
  - Tailwind directives (`@tailwind base; @tailwind components; @tailwind utilities;`)
  - Grid pattern background: `.bg-grid-pattern`
  - Glass morphism utilities: `.glass-card`, `.glass-input`, `.glass-surface`
  - Float animation keyframes
  - Base body styles: `bg-background text-foreground font-body`
- [x] Typecheck passes

---

### US-004: ShadCN UI Initialization
**Description:** As a developer, I want ShadCN UI initialized and configured so that I can use accessible headless components.

**Acceptance Criteria:**
- [x] Run `npx shadcn@latest init` with options:
  - Style: `default`
  - Base color: `neutral`
  - CSS variables: `yes`
- [x] `components.json` exists with:
  - `"style": "default"`
  - `"tailwind.config": "tailwind.config.ts"`
  - `"aliases.components": "@/components"`
  - `"aliases.utils": "@/lib/utils"`
- [x] Create `src/lib/utils.ts` with `cn()` function:
  ```typescript
  import { type ClassValue, clsx } from 'clsx';
  import { twMerge } from 'tailwind-merge';

  export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
  }
  ```
- [x] Typecheck passes

---

### US-005: Base Component Library (Button, Card, Input, Badge)
**Description:** As a UI developer, I want core interactive components styled with Bitcoin DeFi aesthetic so that I can build consistent interfaces.

**Acceptance Criteria:**
- [x] **Button** (`src/components/ui/button.tsx`):
  - Uses CVA for variants: `primary`, `outline`, `ghost`
  - Sizes: `sm`, `md`, `lg`
  - Primary: `bg-gradient-to-r from-secondary to-primary rounded-full shadow-glow-orange hover:scale-105 transition-all`
  - Outline: `border-2 border-primary text-primary rounded-full hover:bg-primary/10`
  - Ghost: `text-muted hover:text-foreground hover:bg-white/5`
  - Exports `Button` component and `ButtonProps` type
- [x] **Card** (`src/components/ui/card.tsx`):
  - Base: `bg-surface border border-white/10 rounded-2xl p-8`
  - Hover: `hover:-translate-y-1 hover:border-primary/50 transition-all duration-300`
  - Exports: `Card`, `CardHeader`, `CardTitle`, `CardDescription`, `CardContent`, `CardFooter`
- [x] **Input** (`src/components/ui/input.tsx`):
  - Base: `bg-black/50 border-b-2 border-white/20 h-12 px-4 text-foreground`
  - Focus: `focus:border-primary focus:outline-none transition-colors`
  - Exports `Input` component and `InputProps` type
- [x] **Badge** (`src/components/ui/badge.tsx`):
  - Variants: `default`, `success`, `warning`, `error`
  - Default: `bg-primary/20 text-primary border border-primary/30 rounded-full px-3 py-1 text-xs font-mono uppercase`
  - Success: `bg-green-500/20 text-green-400 border-green-500/30`
  - Warning: `bg-accent/20 text-accent border-accent/30`
  - Error: `bg-red-500/20 text-red-400 border-red-500/30`
  - Exports `Badge` component and `BadgeProps` type
- [x] All components use `cn()` from `@/lib/utils`
- [x] Typecheck passes

---

### US-006: Layout & Theme Infrastructure
**Description:** As a developer, I want layout components and a theme provider so that pages have consistent structure with dark mode enforced.

**Acceptance Criteria:**
- [x] **Layout Components** (`src/components/layout.tsx`):
  - `Container`: `max-w-7xl mx-auto px-4 sm:px-6 lg:px-8`
  - `Section`: `py-24`
  - `PageLayout`: wrapper with optional header/footer slots
  - Export types: `ContainerProps`, `SectionProps`, `PageLayoutProps`
- [x] **Theme Provider** (`src/components/theme-provider.tsx`):
  - Uses `next-themes` ThemeProvider
  - Forces dark mode (`forcedTheme="dark"`)
  - Sets `attribute="class"` for Tailwind dark mode
  - Exports `ThemeProvider` component
- [x] **Root Layout** (`src/app/layout.tsx`):
  - Wraps children in `<ThemeProvider>`
  - Applies font CSS variables from next/font
  - Sets metadata: title "SyncScript", description
  - Body has class: `font-body bg-background text-foreground`
- [x] Typecheck passes
- [x] Verify changes work in browser

---

### US-007: API Client with JWT Auto-Refresh
**Description:** As a developer, I want an Axios client that automatically refreshes expired tokens so that API requests never fail due to auth expiry.

**Acceptance Criteria:**
- [x] Create `src/lib/api.ts` with:
  - Axios instance with `baseURL` from `process.env.NEXT_PUBLIC_API_URL`
  - Request interceptor: attach `Authorization: Bearer {accessToken}` from auth store
  - Response interceptor:
    - On 401, attempt refresh via `/api/v1/auth/refresh/`
    - Retry original request with new token
    - On refresh failure, clear auth state and redirect to `/login`
  - Export `api` instance
  - Export `ApiError` type for error handling
- [x] Create `src/lib/types/api.ts` with common API response types
- [x] Typecheck passes

---

### US-008: Auth Store with Zustand
**Description:** As a developer, I want a Zustand store for auth with localStorage persistence so that users stay logged in across sessions.

**Acceptance Criteria:**
- [x] Create `src/lib/stores/auth.ts` with:
  - State interface:
    ```typescript
    interface AuthState {
      user: User | null;
      accessToken: string | null;
      refreshToken: string | null;
      isAuthenticated: boolean;
    }
    ```
  - Actions:
    - `login(accessToken, refreshToken, user)`
    - `logout()`
    - `setAccessToken(token)`
  - Use Zustand persist middleware with `localStorage`
  - Handle SSR hydration (avoid mismatch)
- [x] Create `src/lib/types/user.ts` with `User` type
- [x] Export `useAuthStore` hook
- [x] Typecheck passes

---

### US-009: React Query Provider
**Description:** As a developer, I want React Query configured with sensible defaults so that I have consistent data fetching behavior.

**Acceptance Criteria:**
- [x] Create `src/lib/providers/query-provider.tsx` with:
  - QueryClient with default options:
    ```typescript
    {
      defaultOptions: {
        queries: {
          retry: 1,
          staleTime: 5 * 60 * 1000, // 5 minutes
          refetchOnWindowFocus: false,
        },
      },
    }
    ```
  - Wrap children in `QueryClientProvider`
  - Handle client-side only rendering (`'use client'`)
- [x] Import provider in `src/app/layout.tsx`
- [x] Typecheck passes

---

### US-010: ESLint & Prettier Configuration
**Description:** As a developer, I want ESLint and Prettier configured so that code style is consistent.

**Acceptance Criteria:**
- [x] Update ESLint config (`.eslintrc.json` or `eslint.config.mjs` for flat config):
  - Extends: `next/core-web-vitals`, `next/typescript`
  - Rules:
    - `"@typescript-eslint/no-unused-vars": "warn"`
    - `"@typescript-eslint/no-explicit-any": "warn"`
    - `"react/no-unescaped-entities": "off"`
- [x] Create `.prettierrc`:
  ```json
  {
    "semi": true,
    "singleQuote": true,
    "tabWidth": 2,
    "trailingComma": "es5",
    "printWidth": 100
  }
  ```
- [x] Add package.json scripts:
  ```json
  {
    "lint": "next lint",
    "format": "prettier --write \"src/**/*.{ts,tsx,css}\"",
    "type-check": "tsc --noEmit"
  }
  ```
- [x] `npm run lint` passes
- [x] `npm run type-check` passes
- [x] Typecheck passes

---

## Non-Goals

- Authentication pages (login/register forms) — separate PRD
- Data display components (Table, Avatar, Tooltip) — separate PRD
- Storybook setup — not needed for this phase
- E2E tests — separate PRD
- Performance optimization (code splitting, image optimization) — future iteration
- Light mode theme toggle — dark mode only

---

## Technical Considerations

### Tailwind v4 Changes
Tailwind CSS v4 has breaking changes from v3. Key differences:
- New CSS-first configuration approach
- `@theme` directive for design tokens
- JIT is now the only mode
- Some utility names changed

Verify Tailwind v4 syntax when implementing design tokens.

### SSR Hydration
- Zustand persist middleware needs careful handling for SSR
- Use `skipHydration` or conditional rendering to avoid hydration mismatches
- React Query provider must be client-side only

### File Structure
```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   └── globals.css
│   ├── components/
│   │   ├── ui/
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── input.tsx
│   │   │   └── badge.tsx
│   │   ├── layout.tsx
│   │   └── theme-provider.tsx
│   ├── lib/
│   │   ├── api.ts
│   │   ├── utils.ts
│   │   ├── stores/
│   │   │   └── auth.ts
│   │   ├── providers/
│   │   │   └── query-provider.tsx
│   │   └── types/
│   │       ├── api.ts
│   │       └── user.ts
│   ├── hooks/
│   └── styles/
│       └── globals.css
├── public/
├── .env.local.example
├── .eslintrc.json
├── .prettierrc
├── components.json
├── next.config.ts
├── package.json
├── postcss.config.mjs
├── tailwind.config.ts
└── tsconfig.json
```

---

## Success Criteria Summary

- [x] `npm run dev` starts without errors
- [x] All base components render with Bitcoin DeFi styling
- [x] API client auto-refreshes tokens on 401
- [x] Auth state persists across browser reloads
- [x] `npm run lint` passes
- [x] `npm run type-check` passes

---

## Sources

- [Next.js Releases](https://github.com/vercel/next.js/releases) - v16.1.6
- [React npm](https://www.npmjs.com/package/react) - v19.2.4
- [Tailwind CSS v4](https://tailwindcss.com/blog/tailwindcss-v4) - v4.1.x
- [TanStack React Query](https://www.npmjs.com/package/@tanstack/react-query) - v5.90.21
- [Zustand npm](https://www.npmjs.com/package/zustand) - v5.0.11
- [Axios npm](https://www.npmjs.com/package/axios) - v1.13.5
- [ESLint v10](https://eslint.org/blog/2026/02/eslint-v10.0.0-released/) - v10.0.0
- [Prettier npm](https://www.npmjs.com/package/prettier) - v3.8.1
- [TypeScript npm](https://www.npmjs.com/package/typescript) - v5.9.3
