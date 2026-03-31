# Frontend Prompt 01 — Foundation: Project Setup, Auth, Routing

## Context

You are building the frontend for **UniPaith**, an AI-powered admissions platform. The backend is a FastAPI app already running at `http://localhost:8000/api/v1`. A basic Vite+React+TS+Tailwind project already exists at `frontend/`. You need to rip out the existing test shell and replace it with the real application foundation.

This prompt sets up: routing, authentication, API client, state management, and the two role-based layout shells. Every subsequent prompt builds on this.

## Existing Frontend

The `frontend/` folder has Vite+React+TS+Tailwind already configured. The following files exist and should be **kept as-is**:

- `package.json`, `tsconfig.json`, `tsconfig.app.json`, `tsconfig.node.json`
- `vite.config.ts`, `tailwind.config.js`, `postcss.config.js`
- `index.html`
- `src/main.tsx`
- `src/index.css`
- `src/vite-env.d.ts`
- `src/api.ts` (will be replaced by the new `api/client.ts`)

**Delete** these files (they are the old test shell):
- `src/App.tsx` (replace with new version)
- `src/panels/` (entire directory)

## Step 1: Install Dependencies

```bash
cd frontend
npm install react-router-dom@^7 zustand @tanstack/react-query axios react-hook-form @hookform/resolvers zod lucide-react date-fns
npm install -D @types/react-router-dom
```

## Step 2: API Client — `src/api/client.ts`

Create an Axios instance that:

1. Base URL: reads from `import.meta.env.VITE_API_URL` or defaults to `http://localhost:8000/api/v1`
2. **Request interceptor:** reads access token from the auth store (Zustand) and attaches `Authorization: Bearer <token>` header
3. **Response interceptor (401 handling):**
   - On 401 response, attempt to refresh the token using the stored refresh token
   - Call `POST /auth/refresh` with `{ refresh_token }`
   - If refresh succeeds, update the auth store with the new access token and retry the original request
   - If refresh fails, clear the auth store and redirect to `/login`
   - Queue concurrent requests during refresh (prevent multiple refresh calls)
4. **Response interceptor (error formatting):** Extract error messages from FastAPI's `{detail: ...}` format

```typescript
// Public interface
import axios from 'axios'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

export default apiClient
```

## Step 3: Auth Store — `src/stores/auth-store.ts`

Zustand store for authentication state:

```typescript
interface AuthState {
  user: { id: string; email: string; role: 'student' | 'institution_admin' | 'admin' } | null
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  isLoading: boolean

  login: (email: string, password: string) => Promise<void>
  signup: (email: string, password: string, role: string) => Promise<void>
  logout: () => void
  refreshAccessToken: () => Promise<string>
  loadSession: () => Promise<void>
}
```

Key behaviors:
- `login()` → `POST /auth/login` → store tokens + call `GET /auth/me` to get user → store user
- `signup()` → `POST /auth/signup` → auto-login after successful signup
- `logout()` → clear all state + remove refresh token from localStorage + redirect to `/`
- `loadSession()` → check localStorage for refresh token → if exists, call `refreshAccessToken()` then `GET /auth/me` → restore session
- `refreshToken` persisted to `localStorage` (key: `unipaith_refresh_token`)
- `accessToken` stored in memory only (Zustand), not localStorage

## Step 4: Auth API functions — `src/api/auth.ts`

```typescript
import apiClient from './client'

export async function loginApi(email: string, password: string) {
  const { data } = await apiClient.post('/auth/login', { email, password })
  return data  // { access_token, refresh_token, expires_in, token_type }
}

export async function signupApi(email: string, password: string, role: string) {
  const { data } = await apiClient.post('/auth/signup', { email, password, role })
  return data  // { user_id, email, role }
}

export async function refreshTokenApi(refreshToken: string) {
  const { data } = await apiClient.post('/auth/refresh', { refresh_token: refreshToken })
  return data  // { access_token, expires_in }
}

export async function getMeApi() {
  const { data } = await apiClient.get('/auth/me')
  return data  // { user_id, email, role, created_at }
}
```

## Step 5: UI Store — `src/stores/ui-store.ts`

```typescript
interface UIState {
  sidebarCollapsed: boolean
  toggleSidebar: () => void
}
```

Simple for now — will grow later.

## Step 6: Routing — `src/App.tsx`

Use `createBrowserRouter` from React Router v7.

```
/                       → LandingPage
/login                  → LoginPage (AuthLayout)
/signup                 → SignupPage (AuthLayout)

/s/*                    → RequireAuth(role='student') → StudentLayout
  /s/chat               → placeholder "Chat coming soon"
  /s/profile            → placeholder "Profile coming soon"
  /s/discover           → placeholder
  /s/applications       → placeholder
  /s/saved              → placeholder
  /s/messages           → placeholder
  /s/calendar           → placeholder
  /s/settings           → placeholder

/i/*                    → RequireAuth(role='institution_admin') → InstitutionLayout
  /i/dashboard          → placeholder "Dashboard coming soon"
  /i/setup              → placeholder
  /i/programs           → placeholder
  /i/pipeline           → placeholder
  /i/reviews            → placeholder
  /i/interviews         → placeholder
  /i/messages           → placeholder
  /i/segments           → placeholder
  /i/campaigns          → placeholder
  /i/events             → placeholder
  /i/analytics          → placeholder
  /i/settings           → placeholder
```

### Route Guard: `RequireAuth`

A wrapper component that:
1. Checks `isAuthenticated` from auth store
2. If not authenticated + still loading → show spinner
3. If not authenticated + done loading → redirect to `/login`
4. If authenticated but wrong role → redirect to correct section root (`/s/chat` or `/i/dashboard`)
5. If authenticated + correct role → render children

## Step 7: Layouts

### `AuthLayout`
Centered card on a clean background. Logo at top. Contains the login/signup form.

### `StudentLayout`
- **Left nav rail:** Narrow (64px) icon-only sidebar. Icons for: Chat, Profile, Discover, Applications, Saved, Messages, Calendar. Bottom: Settings.
- Hover on rail → shows label tooltip
- Active route highlighted
- **Top bar:** "UniPaith" logo/text, notification bell (placeholder), user avatar/dropdown
- **Main area:** Outlet for page content

### `InstitutionLayout`
- **Left sidebar:** Full sidebar (240px), collapsible to 64px icon-only. Sections:
  - Core: Dashboard, Programs, Pipeline, Reviews, Interviews, Messages
  - Outreach: Segments, Campaigns, Events
  - Admin: Analytics, Settings
- **Top bar:** "UniPaith" text, search bar (placeholder), notification bell (placeholder), admin dropdown
- **Main area:** Outlet for page content

## Step 8: Auth Pages

### `LoginPage`
- Email + password form
- "Log in" button
- Link to signup
- Error display (wrong credentials)
- On success: redirect to `/s/chat` (student) or `/i/dashboard` (institution)

### `SignupPage`
- Email + password + confirm password form
- Role selection: "I'm a student" / "I represent an institution" (radio buttons or cards)
- Password requirements shown
- "Create account" button
- Link to login
- On success: auto-login → redirect to correct section

### `LandingPage`
Simple page with:
- Hero: "UniPaith — AI-powered admissions" headline
- Two CTA cards: "I'm a Student" → signup?role=student, "I'm an Institution" → signup?role=institution
- "Already have an account? Log in" link

## Step 9: Placeholder Pages

For every route defined above, create a simple placeholder component:

```typescript
export default function ChatPage() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-semibold">Chat</h1>
      <p className="text-gray-500 mt-2">Coming in Prompt 02</p>
    </div>
  )
}
```

This ensures all routes resolve and navigation works end-to-end.

## Step 10: TanStack Query Provider

Wrap the app in `QueryClientProvider` in `main.tsx`:

```typescript
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 5 * 60 * 1000, retry: 1 },
  },
})

// In render:
<QueryClientProvider client={queryClient}>
  <RouterProvider router={router} />
</QueryClientProvider>
```

## Verification Checklist

After building, verify:

- [ ] `npm run build` succeeds with no TypeScript errors
- [ ] Landing page renders at `/`
- [ ] Signup form submits to backend (or shows connection error if backend not running)
- [ ] Login form submits to backend
- [ ] After login as student → redirects to `/s/chat`, sees StudentLayout with nav rail
- [ ] After login as institution → redirects to `/i/dashboard`, sees InstitutionLayout with sidebar
- [ ] Clicking nav items navigates to correct placeholder pages
- [ ] Visiting `/s/*` without auth → redirects to `/login`
- [ ] Visiting `/i/*` as student → redirects to `/s/chat`
- [ ] Browser refresh maintains session (loadSession restores from refresh token)
- [ ] Logout clears state and redirects to `/`

## File Summary

New/modified files:
```
src/
├── App.tsx                         (rewrite)
├── api/
│   ├── client.ts                   (new)
│   └── auth.ts                     (new)
├── stores/
│   ├── auth-store.ts               (new)
│   └── ui-store.ts                 (new)
├── components/
│   └── layout/
│       ├── AuthLayout.tsx          (new)
│       ├── StudentLayout.tsx       (new)
│       ├── InstitutionLayout.tsx   (new)
│       └── RequireAuth.tsx         (new)
├── pages/
│   ├── auth/
│   │   ├── LoginPage.tsx           (new)
│   │   ├── SignupPage.tsx          (new)
│   │   └── LandingPage.tsx         (new)
│   ├── student/
│   │   ├── ChatPage.tsx            (new, placeholder)
│   │   ├── ProfilePage.tsx         (new, placeholder)
│   │   ├── DiscoverPage.tsx        (new, placeholder)
│   │   ├── ApplicationsPage.tsx    (new, placeholder)
│   │   ├── SavedListPage.tsx       (new, placeholder)
│   │   ├── MessagesPage.tsx        (new, placeholder)
│   │   ├── CalendarPage.tsx        (new, placeholder)
│   │   └── SettingsPage.tsx        (new, placeholder)
│   └── institution/
│       ├── DashboardPage.tsx       (new, placeholder)
│       ├── SetupPage.tsx           (new, placeholder)
│       ├── ProgramsPage.tsx        (new, placeholder)
│       ├── ProgramEditorPage.tsx   (new, placeholder)
│       ├── PipelinePage.tsx        (new, placeholder)
│       ├── StudentDetailPage.tsx   (new, placeholder)
│       ├── ReviewQueuePage.tsx     (new, placeholder)
│       ├── InterviewsPage.tsx      (new, placeholder)
│       ├── MessagingPage.tsx       (new, placeholder)
│       ├── SegmentsPage.tsx        (new, placeholder)
│       ├── CampaignsPage.tsx       (new, placeholder)
│       ├── EventsPage.tsx          (new, placeholder)
│       ├── AnalyticsPage.tsx       (new, placeholder)
│       └── SettingsPage.tsx        (new, placeholder)
```

Delete:
```
src/panels/                         (entire directory)
src/api.ts                          (replaced by api/client.ts)
```
