# Product Requirements Document: SyncScript Frontend Foundation

## 1. Overview

### 1.1 Purpose
Establish the Next.js 14 frontend foundation for SyncScript with a Bitcoin DeFi-inspired design system, core component library, and API/state management infrastructure.

### 1.2 Success Metrics
- ✅ Next.js dev server runs without errors
- ✅ All base components render with correct Bitcoin DeFi styling
- ✅ API client successfully authenticates and auto-refreshes tokens
- ✅ Auth state persists across browser sessions
- ✅ ESLint/Prettier enforce consistent code style
- ✅ TypeScript compiles with zero errors

---

## 2. User Stories

### Story 1: Project Scaffold & TypeScript Setup
**As a** developer  
**I want** a Next.js 14 App Router project with TypeScript  
**So that** I have type safety and modern React patterns

**Acceptance Criteria:**
- [ ] Next.js 14 initialized with App Router (`npx create-next-app@latest`)
- [ ] TypeScript configured with strict mode enabled
- [ ] Folder structure matches CLAUDE.md specification:
  ```
  frontend/
  ├── src/
  │   ├── app/                 # Next.js App Router
  │   ├── components/
  │   │   ├── ui/              # Base components
  │   │   └── features/        # Feature components (empty)
  │   ├── lib/                 # API client, utils
  │   ├── hooks/               # Custom hooks (empty)
  │   └── styles/              # globals.css
  ├── public/
  ├── package.json
  ├── tsconfig.json
  └── next.config.ts
  ```
- [ ] `.gitignore` excludes `node_modules/`, `.next/`, `.env.local`

### Story 2: Design System Configuration
**As a** frontend developer  
**I want** Tailwind CSS configured with Bitcoin DeFi design tokens  
**So that** all components follow the brand aesthetic consistently

**Acceptance Criteria:**
- [ ] Tailwind CSS 4.1+ installed and configured
- [ ] `tailwind.config.ts` extends theme with:
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
- [ ] Google Fonts loaded in `app/layout.tsx`:
  - Space Grotesk (weights: 400, 700)
  - Inter (weights: 400, 500, 600)
  - JetBrains Mono (weights: 400, 500)
- [ ] `src/styles/globals.css` includes:
  - Tailwind directives (`@tailwind base/components/utilities`)
  - Grid pattern background utility (`.bg-grid-pattern`)
  - Glass morphism utilities (`.glass-card`, `.glass-input`, `.glass-surface`)
  - Float animation keyframes
  - Base body styles (`bg-background text-foreground font-body`)

### Story 3: ShadCN UI Integration
**As a** developer  
**I want** ShadCN UI installed and customized  
**So that** I can use accessible, headless components with our design system

**Acceptance Criteria:**
- [ ] ShadCN UI initialized (`npx shadcn@latest init`)
- [ ] `components.json` configured with:
  - Style: `default`
  - Tailwind CSS path: `tailwind.config.ts`
  - Component path: `src/components/ui`
  - Utilities path: `src/lib/utils.ts`
- [ ] Radix UI dependencies installed:
  - `@radix-ui/react-dialog`
  - `@radix-ui/react-dropdown-menu`
  - `@radix-ui/react-tabs`
  - `@radix-ui/react-toast`
- [ ] `src/lib/utils.ts` exports `cn()` function (clsx + tailwind-merge)

### Story 4: Base Component Library
**As a** UI developer  
**I want** core interactive components styled with Bitcoin DeFi aesthetic  
**So that** I can build consistent interfaces quickly

**Acceptance Criteria:**
- [ ] **Button** (`src/components/ui/button.tsx`):
  - Uses CVA (class-variance-authority) for variants
  - Variants: `primary`, `outline`, `ghost`
  - Sizes: `sm`, `md`, `lg`
  - Primary: `bg-gradient-to-r from-[#EA580C] to-[#F7931A] rounded-full shadow-glow-orange hover:scale-105`
  - Outline: `border-2 border-[#F7931A] text-[#F7931A] rounded-full hover:bg-[#F7931A]/10`
  - Ghost: `text-muted hover:text-foreground hover:bg-white/5`
  - TypeScript props extend `React.ButtonHTMLAttributes<HTMLButtonElement>`

- [ ] **Card** (`src/components/ui/card.tsx`):
  - Base: `bg-surface border border-white/10 rounded-2xl p-8`
  - Hover lift effect: `hover:-translate-y-1 hover:border-primary/50 transition-all duration-300`
  - Exports: `Card`, `CardHeader`, `CardTitle`, `CardDescription`, `CardContent`, `CardFooter`

- [ ] **Input** (`src/components/ui/input.tsx`):
  - Base: `bg-black/50 border-b-2 border-white/20 h-12 px-4 text-foreground`
  - Focus: `focus:border-primary focus:outline-none transition-colors`
  - Supports `type`, `placeholder`, `disabled` props

- [ ] **Badge** (`src/components/ui/badge.tsx`):
  - Variants: `default`, `success`, `warning`, `error`
  - Default: `bg-primary/20 text-primary border border-primary/30 rounded-full px-3 py-1 text-xs font-mono uppercase`
  - Success: `bg-green-500/20 text-green-400 border-green-500/30`
  - Warning: `bg-accent/20 text-accent border-accent/30`
  - Error: `bg-red-500/20 text-red-400 border-red-500/30`

### Story 5: Layout & Theme Infrastructure
**As a** developer  
**I want** a responsive layout component and theme provider  
**So that** pages have consistent structure and dark mode enforced

**Acceptance Criteria:**
- [ ] **Layout** (`src/components/layout.tsx`):
  - Exports `Container` component: `max-w-7xl mx-auto px-4 sm:px-6 lg:px-8`
  - Exports `Section` component: `py-24`
  - Exports `PageLayout` wrapper with optional header/footer slots

- [ ] **Theme Provider** (`src/components/theme-provider.tsx`):
  - Forces dark mode (no toggle)
  - Sets `<html>` class to `dark` on mount
  - Uses `next-themes` or custom context (dark-only mode)

- [ ] **Root Layout** (`src/app/layout.tsx`):
  - Wraps children in `<ThemeProvider>`
  - Applies font classes: `className={`${inter.variable} ${spaceGrotesk.variable} ${jetbrainsMono.variable}`}`
  - Sets metadata: title, description

### Story 6: API Client with JWT Auto-Refresh
**As a** developer  
**I want** an Axios client that automatically refreshes expired tokens  
**So that** API requests never fail due to auth expiry

**Acceptance Criteria:**
- [ ] **API Client** (`src/lib/api.ts`):
  - Axios instance with `baseURL: process.env.NEXT_PUBLIC_API_URL`
  - Request interceptor: Attach `Authorization: Bearer {accessToken}` from auth store
  - Response interceptor:
    - On 401 error, attempt token refresh via `/api/v1/auth/refresh/`
    - Retry original request with new token
    - On refresh failure, clear auth state and redirect to `/login`
  - Exports: `api` instance, `ApiError` type

- [ ] **Environment Variables** (`.env.local.example`):
  ```
  NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
  NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
  ```

### Story 7: State Management Setup
**As a** developer  
**I want** Zustand store for auth with localStorage persistence  
**So that** users stay logged in across sessions

**Acceptance Criteria:**
- [ ] **Auth Store** (`src/lib/stores/auth.ts`):
  - State:
    ```typescript
    {
      user: User | null,
      accessToken: string | null,
      refreshToken: string | null,
      isAuthenticated: boolean,
    }
    ```
  - Actions:
    - `login(accessToken, refreshToken, user)`
    - `logout()`
    - `setAccessToken(token)`
  - Persisted to `localStorage` via Zustand persist middleware
  - Exports: `useAuthStore` hook

- [ ] **React Query Provider** (`src/lib/providers/query-provider.tsx`):
  - Wraps `QueryClientProvider` with default config:
    ```typescript
    {
      defaultOptions: {
        queries: { retry: 1, staleTime: 5 * 60 * 1000 },
      },
    }
    ```
  - Imported in `app/layout.tsx`

### Story 8: Code Quality Tooling
**As a** developer  
**I want** ESLint and Prettier configured  
**So that** code style is consistent across the team

**Acceptance Criteria:**
- [ ] **ESLint** (`.eslintrc.json`):
  - Extends: `next/core-web-vitals`, `next/typescript`
  - Rules:
    - `"@typescript-eslint/no-unused-vars": "warn"`
    - `"@typescript-eslint/no-explicit-any": "warn"`
    - `"react/no-unescaped-entities": "off"`

- [ ] **Prettier** (`.prettierrc`):
  ```json
  {
    "semi": true,
    "singleQuote": true,
    "tabWidth": 2,
    "trailingComma": "es5",
    "printWidth": 100
  }
  ```

- [ ] **Package Scripts**:
  ```json
  {
    "lint": "next lint",
    "format": "prettier --write \"src/**/*.{ts,tsx,css}\"",
    "type-check": "tsc --noEmit"
  }
  ```

---

## 3. Technical Specifications

### 3.1 Dependencies
```json
{
  "dependencies": {
    "next": "^14.2.0",
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "tailwindcss": "^4.1.0",
    "@tanstack/react-query": "^5.90.0",
    "axios": "^1.7.0",
    "zustand": "^5.0.0",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.0",
    "tailwind-merge": "^3.0.0",
    "lucide-react": "^0.563.0",
    "@radix-ui/react-dialog": "^1.1.0",
    "@radix-ui/react-dropdown-menu": "^2.1.0",
    "@radix-ui/react-tabs": "^1.1.0",
    "@radix-ui/react-toast": "^1.2.0"
  },
  "devDependencies": {
    "@types/node": "^22.0.0",
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "typescript": "^5.6.0",
    "eslint": "^9.0.0",
    "eslint-config-next": "^14.2.0",
    "prettier": "^3.4.0",
    "autoprefixer": "^10.4.20",
    "postcss": "^8.4.0"
  }
}
```

### 3.2 TypeScript Configuration
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
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx"],
  "exclude": ["node_modules"]
}
```

### 3.3 File Structure
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
│   │   └── providers/
│   │       └── query-provider.tsx
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

## 4. Testing & Validation

### Manual Verification Tasks
Append to `.planning/MANUAL_VERIFICATION.md`:

```markdown
## Frontend Foundation - 2026-02-14

### Design System
- [ ] Run `npm run dev`, visit http://localhost:3000
- [ ] Verify background is true black (#030304) with grid pattern
- [ ] Check Google Fonts load correctly (Space Grotesk headings, Inter body)

### Components
- [ ] Create test page with all Button variants (primary/outline/ghost)
- [ ] Verify primary button has orange gradient + glow shadow
- [ ] Test Card hover lift effect
- [ ] Verify Input bottom border turns orange on focus
- [ ] Test Badge variants render with correct colors

### API Client
- [ ] Mock 401 response, verify token refresh triggers
- [ ] Check auth store persists to localStorage after login
- [ ] Clear localStorage, verify app redirects to login

### Code Quality
- [ ] Run `npm run lint` (should pass)
- [ ] Run `npm run type-check` (should pass)
- [ ] Run `npm run format` (should format all files)
```

### User Setup Tasks
Append to `.planning/USER_SETUP.md`:

```markdown
## Frontend Development Environment

### Required For: Next.js Frontend
### Steps:
1. Install Node.js 18+ (LTS recommended)
2. Install npm or pnpm
3. Navigate to `frontend/` directory
4. Copy `.env.local.example` to `.env.local`
5. Run `npm install`
6. Run `npm run dev`

### Environment Variables:
- `NEXT_PUBLIC_API_URL`: Backend API URL (default: http://localhost:8000/api/v1)
- `NEXT_PUBLIC_WS_URL`: WebSocket URL (default: ws://localhost:8000/ws)

### Verify Installation:
- Visit http://localhost:3000
- Check browser console for errors
- Verify fonts load (Network tab → Filter "fonts")
```

---

## 5. Dependencies & Constraints

### Dependencies
- Backend API must be running on `NEXT_PUBLIC_API_URL`
- JWT endpoints (`/api/v1/auth/login/`, `/api/v1/auth/refresh/`) must exist

### Constraints
- Dark mode only (no light theme toggle)
- Must support latest Chrome, Firefox, Safari
- All components must be keyboard accessible (Radix UI handles this)

---

## 6. Out of Scope

- Authentication pages (login/register forms) → Separate PRD
- Data display components (Table, Avatar, Tooltip) → Separate PRD
- Storybook setup → Not needed for this phase
- E2E tests → Separate PRD
- Performance optimization (code splitting, image optimization) → Future iteration

---

## 7. Success Criteria Summary

- [ ] `npm run dev` starts without errors
- [ ] All base components render with Bitcoin DeFi styling
- [ ] API client auto-refreshes tokens on 401
- [ ] Auth state persists across browser reloads
- [ ] `npm run lint` and `npm run type-check` pass
- [ ] Manual verification tasks completed
- [ ] User setup documentation verified

---

## 8. Notes

- Reference `DESIGN_RULES.md` for all color/typography decisions
- Use `.glass-card`, `.glass-input`, `.glass-surface` utilities instead of inline `backdrop-blur` classes
- All animations should use `transition-all duration-300` for consistency
- Components should export TypeScript types for props (e.g., `ButtonProps`, `CardProps`)