# UniPaith Frontend — COMPLETE BUILD INSTRUCTIONS (Part 1: Foundation + Student Side)

> **What this file is:** A comprehensive prompt for a coding tool (Cursor / Claude Code) to build the entire UniPaith frontend. Part 1 covers project setup, auth, routing, the API client, and ALL student-facing pages. Part 2 (separate file) covers ALL institution-facing pages.
>
> **Backend status:** The FastAPI backend is running at `http://localhost:8000/api/v1` with full auth, student CRUD, institution CRUD, programs, applications, documents, messaging, events, interviews, reviews, notifications, ML admin, and crawler admin endpoints.

---

## TABLE OF CONTENTS

1. [Tech Stack & Dependencies](#1-tech-stack--dependencies)
2. [Project Structure](#2-project-structure)
3. [API Client & Auth](#3-api-client--auth)
4. [Routing & Layouts](#4-routing--layouts)
5. [TypeScript Types](#5-typescript-types)
6. [UI Primitives](#6-ui-primitives)
7. [Auth Pages](#7-auth-pages)
8. [Public Pages](#8-public-pages)
9. [Student Layout](#9-student-layout)
10. [Student Chat Page](#10-student-chat-page)
11. [Student Profile Page](#11-student-profile-page)
12. [Student Discover Page](#12-student-discover-page)
13. [Student School Detail Page](#13-student-school-detail-page)
14. [Student Applications Pages](#14-student-applications-pages)
15. [Student Saved List Page](#15-student-saved-list-page)
16. [Student Messages Page](#16-student-messages-page)
17. [Student Calendar Page](#17-student-calendar-page)
18. [Student Settings Page](#18-student-settings-page)
19. [Student API Modules](#19-student-api-modules)
20. [Shared Components](#20-shared-components)

---

## 1. Tech Stack & Dependencies

### Existing setup to keep
The `frontend/` folder already has Vite + React 19 + TypeScript + Tailwind CSS 3 configured. Keep all config files as-is.

### Delete these files (old test shell)
```
src/panels/           (entire directory)
src/api.ts            (replaced by api/client.ts)
src/App.tsx           (will be rewritten)
```

### Install new dependencies
```bash
cd frontend
npm install react-router-dom@^7 zustand @tanstack/react-query axios react-hook-form @hookform/resolvers zod lucide-react date-fns clsx
npm install -D @types/react-router-dom
```

### Add to `.env` (create if not exists)
```
VITE_API_URL=http://localhost:8000/api/v1
```

---

## 2. Project Structure

```
frontend/src/
├── main.tsx
├── App.tsx
├── index.css
├── vite-env.d.ts
├── api/
│   ├── client.ts              # Axios instance + interceptors
│   ├── auth.ts                # Auth endpoints
│   ├── students.ts            # Student profile, academics, scores, activities, preferences
│   ├── programs.ts            # Public program search
│   ├── matching.ts            # Matches + engagement signals
│   ├── applications.ts        # Application CRUD + submit + offer response
│   ├── documents.ts           # Upload flow + CRUD
│   ├── essays.ts              # Essay CRUD + feedback
│   ├── resumes.ts             # Resume generation + CRUD
│   ├── saved-lists.ts         # Save/unsave/compare programs
│   ├── messaging.ts           # Conversations + messages
│   ├── events.ts              # Events + RSVPs
│   ├── interviews.ts          # Student interview endpoints
│   ├── notifications.ts       # Notification feed + preferences
│   ├── institutions.ts        # Institution admin endpoints (Part 2)
│   ├── reviews.ts             # Review/scoring endpoints (Part 2)
│   └── admin.ts               # ML admin + crawler admin (Part 2)
├── stores/
│   ├── auth-store.ts
│   └── ui-store.ts
├── hooks/
│   ├── use-auth.ts
│   └── use-query-hooks.ts     # TanStack Query wrappers
├── types/
│   └── index.ts               # All TypeScript interfaces
├── utils/
│   ├── format.ts              # Formatters
│   └── constants.ts           # Enums, labels
├── components/
│   ├── ui/                    # Button, Input, Modal, Card, Badge, Toast, etc.
│   ├── layout/
│   │   ├── AuthLayout.tsx
│   │   ├── StudentLayout.tsx
│   │   ├── InstitutionLayout.tsx
│   │   └── RequireAuth.tsx
│   └── shared/
│       ├── ChatBubble.tsx
│       ├── MatchCard.tsx
│       ├── ProgramCard.tsx
│       ├── FileUploader.tsx
│       ├── StatusBadge.tsx
│       └── EmptyState.tsx
├── pages/
│   ├── auth/
│   │   ├── LoginPage.tsx
│   │   ├── SignupPage.tsx
│   │   └── LandingPage.tsx
│   ├── public/
│   │   └── ProgramBrowsePage.tsx
│   ├── student/
│   │   ├── ChatPage.tsx
│   │   ├── ProfilePage.tsx
│   │   ├── DiscoverPage.tsx
│   │   ├── SchoolDetailPage.tsx
│   │   ├── ApplicationsPage.tsx
│   │   ├── ApplicationDetailPage.tsx
│   │   ├── SavedListPage.tsx
│   │   ├── MessagesPage.tsx
│   │   ├── CalendarPage.tsx
│   │   └── SettingsPage.tsx
│   └── institution/
│       ├── ... (covered in Part 2)
```

---

## 3. API Client & Auth

### `src/api/client.ts`

```typescript
import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

// Track refresh state to prevent concurrent refresh calls
let isRefreshing = false
let refreshSubscribers: ((token: string) => void)[] = []

function subscribeTokenRefresh(cb: (token: string) => void) {
  refreshSubscribers.push(cb)
}

function onTokenRefreshed(token: string) {
  refreshSubscribers.forEach(cb => cb(token))
  refreshSubscribers = []
}

// Request interceptor: attach access token
apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  // Import dynamically to avoid circular deps
  const { useAuthStore } = require('../stores/auth-store')
  const token = useAuthStore.getState().accessToken
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor: handle 401 + refresh
apiClient.interceptors.response.use(
  response => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      if (isRefreshing) {
        // Wait for the refresh to complete
        return new Promise(resolve => {
          subscribeTokenRefresh((token: string) => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`
            }
            resolve(apiClient(originalRequest))
          })
        })
      }

      isRefreshing = true

      try {
        const { useAuthStore } = require('../stores/auth-store')
        const newToken = await useAuthStore.getState().refreshAccessToken()
        isRefreshing = false
        onTokenRefreshed(newToken)
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${newToken}`
        }
        return apiClient(originalRequest)
      } catch {
        isRefreshing = false
        const { useAuthStore } = require('../stores/auth-store')
        useAuthStore.getState().logout()
        window.location.href = '/login'
        return Promise.reject(error)
      }
    }

    // Format error message from FastAPI's {detail: ...}
    const message = (error.response?.data as any)?.detail || error.message
    return Promise.reject(new Error(message))
  }
)

export default apiClient
```

**NOTE:** The `require()` for auth store is intentional to break circular dependency. Alternatively, use a lazy import pattern or pass the token getter as a config option.

### `src/stores/auth-store.ts`

```typescript
import { create } from 'zustand'
import apiClient from '../api/client'

interface User {
  id: string
  email: string
  role: 'student' | 'institution_admin' | 'admin'
  created_at: string
}

interface AuthState {
  user: User | null
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

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  accessToken: null,
  refreshToken: localStorage.getItem('unipaith_refresh_token'),
  isAuthenticated: false,
  isLoading: true,

  login: async (email, password) => {
    const { data } = await apiClient.post('/auth/login', { email, password })
    set({ accessToken: data.access_token, refreshToken: data.refresh_token })
    localStorage.setItem('unipaith_refresh_token', data.refresh_token)

    // Fetch user info
    const { data: user } = await apiClient.get('/auth/me', {
      headers: { Authorization: `Bearer ${data.access_token}` }
    })
    set({ user: { id: user.user_id, email: user.email, role: user.role, created_at: user.created_at }, isAuthenticated: true })
  },

  signup: async (email, password, role) => {
    await apiClient.post('/auth/signup', { email, password, role })
    // Auto-login after signup
    await get().login(email, password)
  },

  logout: () => {
    localStorage.removeItem('unipaith_refresh_token')
    set({ user: null, accessToken: null, refreshToken: null, isAuthenticated: false, isLoading: false })
  },

  refreshAccessToken: async () => {
    const rt = get().refreshToken
    if (!rt) throw new Error('No refresh token')
    const { data } = await apiClient.post('/auth/refresh', { refresh_token: rt })
    set({ accessToken: data.access_token })
    return data.access_token
  },

  loadSession: async () => {
    const rt = get().refreshToken
    if (!rt) {
      set({ isLoading: false })
      return
    }
    try {
      const token = await get().refreshAccessToken()
      const { data: user } = await apiClient.get('/auth/me', {
        headers: { Authorization: `Bearer ${token}` }
      })
      set({
        user: { id: user.user_id, email: user.email, role: user.role, created_at: user.created_at },
        isAuthenticated: true,
        isLoading: false,
      })
    } catch {
      get().logout()
      set({ isLoading: false })
    }
  },
}))
```

### `src/stores/ui-store.ts`

```typescript
import { create } from 'zustand'

interface UIState {
  sidebarCollapsed: boolean
  toggleSidebar: () => void
  activeModal: string | null
  openModal: (id: string) => void
  closeModal: () => void
}

export const useUIStore = create<UIState>((set) => ({
  sidebarCollapsed: false,
  toggleSidebar: () => set(s => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  activeModal: null,
  openModal: (id) => set({ activeModal: id }),
  closeModal: () => set({ activeModal: null }),
}))
```

---

## 4. Routing & Layouts

### `src/App.tsx`

```typescript
import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useEffect } from 'react'
import { useAuthStore } from './stores/auth-store'

// Layouts
import AuthLayout from './components/layout/AuthLayout'
import StudentLayout from './components/layout/StudentLayout'
import InstitutionLayout from './components/layout/InstitutionLayout'
import RequireAuth from './components/layout/RequireAuth'

// Auth pages
import LandingPage from './pages/auth/LandingPage'
import LoginPage from './pages/auth/LoginPage'
import SignupPage from './pages/auth/SignupPage'

// Public pages
import ProgramBrowsePage from './pages/public/ProgramBrowsePage'

// Student pages
import ChatPage from './pages/student/ChatPage'
import ProfilePage from './pages/student/ProfilePage'
import DiscoverPage from './pages/student/DiscoverPage'
import SchoolDetailPage from './pages/student/SchoolDetailPage'
import ApplicationsPage from './pages/student/ApplicationsPage'
import ApplicationDetailPage from './pages/student/ApplicationDetailPage'
import SavedListPage from './pages/student/SavedListPage'
import MessagesPage from './pages/student/MessagesPage'
import CalendarPage from './pages/student/CalendarPage'
import StudentSettingsPage from './pages/student/SettingsPage'

// Institution pages
import DashboardPage from './pages/institution/DashboardPage'
import SetupPage from './pages/institution/SetupPage'
import ProgramsPage from './pages/institution/ProgramsPage'
import ProgramEditorPage from './pages/institution/ProgramEditorPage'
import PipelinePage from './pages/institution/PipelinePage'
import StudentDetailPage from './pages/institution/StudentDetailPage'
import ReviewQueuePage from './pages/institution/ReviewQueuePage'
import InterviewsPage from './pages/institution/InterviewsPage'
import InstitutionMessagingPage from './pages/institution/MessagingPage'
import SegmentsPage from './pages/institution/SegmentsPage'
import CampaignsPage from './pages/institution/CampaignsPage'
import EventsPage from './pages/institution/EventsPage'
import AnalyticsPage from './pages/institution/AnalyticsPage'
import InstitutionSettingsPage from './pages/institution/SettingsPage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 5 * 60 * 1000, retry: 1, refetchOnWindowFocus: false },
  },
})

const router = createBrowserRouter([
  // Public routes
  { path: '/', element: <LandingPage /> },
  { path: '/browse', element: <ProgramBrowsePage /> },
  { path: '/login', element: <AuthLayout><LoginPage /></AuthLayout> },
  { path: '/signup', element: <AuthLayout><SignupPage /></AuthLayout> },

  // Student routes
  {
    path: '/s',
    element: <RequireAuth role="student"><StudentLayout /></RequireAuth>,
    children: [
      { index: true, element: <Navigate to="/s/chat" replace /> },
      { path: 'chat', element: <ChatPage /> },
      { path: 'profile', element: <ProfilePage /> },
      { path: 'discover', element: <DiscoverPage /> },
      { path: 'schools/:programId', element: <SchoolDetailPage /> },
      { path: 'applications', element: <ApplicationsPage /> },
      { path: 'applications/:appId', element: <ApplicationDetailPage /> },
      { path: 'saved', element: <SavedListPage /> },
      { path: 'messages', element: <MessagesPage /> },
      { path: 'messages/:convId', element: <MessagesPage /> },
      { path: 'calendar', element: <CalendarPage /> },
      { path: 'settings', element: <StudentSettingsPage /> },
    ],
  },

  // Institution routes
  {
    path: '/i',
    element: <RequireAuth role="institution_admin"><InstitutionLayout /></RequireAuth>,
    children: [
      { index: true, element: <Navigate to="/i/dashboard" replace /> },
      { path: 'dashboard', element: <DashboardPage /> },
      { path: 'setup', element: <SetupPage /> },
      { path: 'programs', element: <ProgramsPage /> },
      { path: 'programs/new', element: <ProgramEditorPage /> },
      { path: 'programs/:id/edit', element: <ProgramEditorPage /> },
      { path: 'pipeline', element: <PipelinePage /> },
      { path: 'pipeline/:studentId', element: <StudentDetailPage /> },
      { path: 'reviews', element: <ReviewQueuePage /> },
      { path: 'interviews', element: <InterviewsPage /> },
      { path: 'messages', element: <InstitutionMessagingPage /> },
      { path: 'segments', element: <SegmentsPage /> },
      { path: 'campaigns', element: <CampaignsPage /> },
      { path: 'events', element: <EventsPage /> },
      { path: 'analytics', element: <AnalyticsPage /> },
      { path: 'settings', element: <InstitutionSettingsPage /> },
    ],
  },

  // Catch-all
  { path: '*', element: <Navigate to="/" replace /> },
])

export default function App() {
  const loadSession = useAuthStore(s => s.loadSession)

  useEffect(() => {
    loadSession()
  }, [loadSession])

  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  )
}
```

### `src/components/layout/RequireAuth.tsx`

```typescript
import { Navigate } from 'react-router-dom'
import { useAuthStore } from '../../stores/auth-store'

interface Props {
  role: 'student' | 'institution_admin'
  children: React.ReactNode
}

export default function RequireAuth({ role, children }: Props) {
  const { isAuthenticated, isLoading, user } = useAuthStore()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900" />
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (user?.role !== role) {
    // Redirect to correct section
    const target = user?.role === 'student' ? '/s/chat' : '/i/dashboard'
    return <Navigate to={target} replace />
  }

  return <>{children}</>
}
```

### `src/components/layout/AuthLayout.tsx`

Centered card on a clean white/light-gray background:

```typescript
interface Props { children: React.ReactNode }

export default function AuthLayout({ children }: Props) {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold">UniPaith</h1>
          <p className="text-gray-500 text-sm mt-1">AI-Powered Admissions</p>
        </div>
        <div className="bg-white rounded-lg shadow-sm border p-6">
          {children}
        </div>
      </div>
    </div>
  )
}
```

---

## 5. TypeScript Types

### `src/types/index.ts`

Define ALL interfaces matching the backend Pydantic schemas. Every field name must match exactly.

```typescript
// ============ AUTH ============
export interface User {
  id: string          // user_id from backend
  email: string
  role: 'student' | 'institution_admin' | 'admin'
  created_at: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string | null
  expires_in: number
  token_type: string
}

// ============ STUDENT PROFILE ============
export interface StudentProfile {
  id: string
  user_id: string
  first_name: string | null
  last_name: string | null
  date_of_birth: string | null  // ISO date
  nationality: string | null
  country_of_residence: string | null
  bio_text: string | null
  goals_text: string | null
  created_at: string
  updated_at: string
  academic_records: AcademicRecord[]
  test_scores: TestScore[]
  activities: Activity[]
  preferences: StudentPreference | null
  onboarding: OnboardingStatus | null
}

export interface AcademicRecord {
  id: string
  student_id: string
  institution_name: string
  degree_type: 'high_school' | 'bachelors' | 'masters' | 'phd' | 'associate' | 'diploma'
  field_of_study: string | null
  gpa: number | null
  gpa_scale: string | null
  start_date: string
  end_date: string | null
  is_current: boolean
  honors: string | null
  thesis_title: string | null
  country: string | null
  created_at: string
  updated_at: string
}

export interface TestScore {
  id: string
  student_id: string
  test_type: 'SAT' | 'GRE' | 'GMAT' | 'TOEFL' | 'IELTS' | 'AP' | 'IB' | 'ACT' | 'LSAT' | 'MCAT' | 'DUOLINGO'
  total_score: number | null
  section_scores: Record<string, number> | null
  test_date: string | null
  is_official: boolean
  created_at: string
  updated_at: string
}

export interface Activity {
  id: string
  student_id: string
  activity_type: 'work_experience' | 'research' | 'volunteering' | 'extracurricular' | 'leadership' | 'awards' | 'publications'
  title: string
  organization: string | null
  description: string | null
  start_date: string | null
  end_date: string | null
  is_current: boolean
  hours_per_week: number | null
  impact_description: string | null
  created_at: string
  updated_at: string
}

export interface StudentPreference {
  id: string
  student_id: string
  preferred_countries: string[]
  preferred_regions: string[]
  preferred_city_size: string | null
  preferred_climate: string | null
  budget_min: number | null
  budget_max: number | null
  funding_requirement: string | null
  program_size_preference: string | null
  career_goals: string[] | null
  values_priorities: Record<string, number> | null
  dealbreakers: string[] | null
  goals_text: string | null
  created_at: string
  updated_at: string
}

export interface OnboardingStatus {
  completion_percentage: number
  steps_completed: string[]
  next_step: { section: string; fields: string[]; guidance_text: string } | null
}

// ============ PROGRAMS ============
export interface Program {
  id: string
  institution_id: string
  program_name: string
  degree_type: 'bachelors' | 'masters' | 'phd' | 'certificate' | 'diploma'
  department: string | null
  duration_months: number | null
  tuition: number | null
  acceptance_rate: number | null
  requirements: Record<string, any> | null
  description_text: string | null
  current_preferences_text: string | null
  is_published: boolean
  application_deadline: string | null
  program_start_date: string | null
  highlights: string[] | null
  page_header_image_url: string | null
  faculty_contacts: Record<string, any>[] | null
  created_at: string
  updated_at: string
}

export interface ProgramSummary {
  id: string
  program_name: string
  degree_type: string
  department: string | null
  tuition: number | null
  application_deadline: string | null
  institution_name: string
  institution_country: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

// ============ MATCHING ============
export interface MatchResult {
  id: string
  student_id: string
  program_id: string
  match_score: number
  match_tier: number           // 1=reach, 2=match, 3=safety
  score_breakdown: Record<string, number> | null
  reasoning_text: string | null
  model_version: string | null
  computed_at: string
  is_stale: boolean
  program?: Program            // May be nested
}

export interface EngagementSignal {
  id: string
  student_id: string
  program_id: string
  signal_type: string
  signal_value: number
  created_at: string
}

// ============ APPLICATIONS ============
export interface Application {
  id: string
  student_id: string
  program_id: string
  status: 'draft' | 'submitted' | 'under_review' | 'interview' | 'decision_made'
  match_score: number | null
  match_reasoning_text: string | null
  submitted_at: string | null
  decision: 'admitted' | 'rejected' | 'waitlisted' | 'deferred' | null
  decision_at: string | null
  decision_notes: string | null
  completeness_status: string | null
  missing_items: string[] | null
  created_at: string
  updated_at: string
  program?: Program
}

export interface ApplicationChecklist {
  id: string
  student_id: string
  program_id: string
  items: { name: string; status: string; required: boolean }[]
  completion_percentage: number
  auto_generated_at: string | null
}

export interface ReadinessCheck {
  ready: boolean
  completion_percentage: number
  missing_items: string[]
  warnings: string[]
}

export interface OfferLetter {
  id: string
  application_id: string
  offer_type: string
  tuition_amount: number | null
  scholarship_amount: number
  financial_package_total: number | null
  conditions: Record<string, any> | null
  response_deadline: string | null
  status: string
  student_response: string | null
  response_at: string | null
}

// ============ DOCUMENTS ============
export interface StudentDocument {
  id: string
  student_id: string
  document_type: 'transcript' | 'essay' | 'resume' | 'recommendation' | 'portfolio' | 'certificate'
  file_name: string
  file_size_bytes: number | null
  mime_type: string | null
  uploaded_at: string
  download_url?: string | null
}

export interface UploadResponse {
  upload_url: string
  document_id: string
  expires_in: number
}

// ============ ESSAYS & RESUMES ============
export interface Essay {
  id: string
  student_id: string
  program_id: string
  prompt_text: string | null
  essay_version: number
  content: string
  word_count: number | null
  ai_feedback: Record<string, any> | null
  status: 'draft' | 'reviewed' | 'revised' | 'finalized'
  created_at: string
  updated_at: string
}

export interface Resume {
  id: string
  student_id: string
  resume_version: number
  content: Record<string, any> | null
  rendered_pdf_url: string | null
  ai_suggestions: Record<string, any> | null
  target_program_id: string | null
  status: 'draft' | 'reviewed' | 'finalized'
  created_at: string
  updated_at: string
}

// ============ SAVED LISTS ============
export interface SavedProgram {
  id: string
  student_id: string
  program_id: string
  notes: string | null
  added_at: string
  program?: ProgramSummary
}

export interface ComparisonResponse {
  programs: ProgramSummary[]
  comparison: Record<string, any>
}

// ============ MESSAGING ============
export interface Conversation {
  id: string
  student_id: string
  institution_id: string
  program_id: string | null
  subject: string | null
  status: 'open' | 'awaiting_response' | 'resolved' | 'closed'
  started_at: string
  last_message_at: string | null
}

export interface Message {
  id: string
  conversation_id: string
  sender_type: 'student' | 'institution'
  sender_id: string
  message_body: string
  sent_at: string
  read_at: string | null
}

// ============ EVENTS ============
export interface EventItem {
  id: string
  institution_id: string
  program_id: string | null
  event_name: string
  event_type: 'webinar' | 'campus_visit' | 'info_session' | 'workshop'
  description: string | null
  location: string | null
  start_time: string
  end_time: string
  capacity: number | null
  rsvp_count: number
  status: string
}

export interface RSVP {
  id: string
  event_id: string
  student_id: string
  rsvp_status: string
  registered_at: string
  attended_at: string | null
}

// ============ INTERVIEWS ============
export interface Interview {
  id: string
  application_id: string
  interviewer_id: string
  interview_type: 'video' | 'in_person' | 'phone' | 'group'
  proposed_times: string[]
  confirmed_time: string | null
  location_or_link: string | null
  status: 'invited' | 'scheduling' | 'confirmed' | 'completed' | 'cancelled' | 'no_show'
  duration_minutes: number
  created_at: string
  updated_at: string
}

// ============ NOTIFICATIONS ============
export interface Notification {
  id: string
  title: string
  body: string
  notification_type: string
  is_read: boolean
  reference_type: string | null
  reference_id: string | null
  created_at: string
}

export interface NotificationPreference {
  email_enabled: boolean
  preferences: Record<string, boolean>
}

// ============ INSTITUTION (used in Part 2) ============
export interface Institution {
  id: string
  admin_user_id: string
  name: string
  type: string
  country: string
  region: string | null
  city: string | null
  ranking_data: Record<string, number> | null
  description_text: string | null
  logo_url: string | null
  website_url: string | null
  is_verified: boolean
  created_at: string
  updated_at: string
  program_count?: number
}
```

---

## 6. UI Primitives

### `src/components/ui/Button.tsx`

```typescript
import { forwardRef } from 'react'
import clsx from 'clsx'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'primary', size = 'md', loading, className, children, disabled, ...props }, ref) => {
    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        className={clsx(
          'inline-flex items-center justify-center rounded font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed',
          {
            'bg-gray-900 text-white hover:bg-gray-800': variant === 'primary',
            'border border-gray-300 bg-white text-gray-700 hover:bg-gray-50': variant === 'secondary',
            'text-gray-700 hover:bg-gray-100': variant === 'ghost',
            'bg-red-600 text-white hover:bg-red-700': variant === 'danger',
            'px-2.5 py-1 text-xs': size === 'sm',
            'px-3.5 py-2 text-sm': size === 'md',
            'px-5 py-2.5 text-base': size === 'lg',
          },
          className
        )}
        {...props}
      >
        {loading && (
          <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        )}
        {children}
      </button>
    )
  }
)

Button.displayName = 'Button'
export default Button
```

Create the following additional primitives in `src/components/ui/` using similar patterns — each as its own file:

- **Input.tsx** — `<label>` wrapper with label text, input element, optional error message, helper text. Props: `label`, `error`, `helperText`, plus all native input props. Tailwind: `border rounded px-3 py-2 text-sm w-full focus:ring-2 focus:ring-gray-900 focus:border-transparent`. Error state: `border-red-500`.

- **Textarea.tsx** — Same pattern as Input but `<textarea>`. Add optional `maxLength` with character count display.

- **Select.tsx** — A `<select>` wrapper with label + error. Props: `label`, `error`, `options: { value: string; label: string }[]`, plus native select props.

- **Modal.tsx** — Fixed overlay (`bg-black/50`), centered card. Props: `isOpen`, `onClose`, `title`, `children`, `size?: 'sm' | 'md' | 'lg'`. Close on backdrop click and Escape key. Sizes: sm=`max-w-sm`, md=`max-w-lg`, lg=`max-w-2xl`.

- **Card.tsx** — A `div` with `bg-white rounded-lg border shadow-sm`. Props: `children`, `className`, optional `onClick` (adds hover effect).

- **Badge.tsx** — Inline span. Props: `variant: 'success' | 'warning' | 'danger' | 'info' | 'neutral'`, `size?: 'sm' | 'md'`, `children`. Colors: success=green, warning=yellow, danger=red, info=blue, neutral=gray. Use Tailwind bg + text colors.

- **Toast.tsx** — Create a simple toast system using a Zustand store (`src/stores/toast-store.ts`). Functions: `showToast(message, type)`. Renders fixed-position stack in top-right corner. Auto-dismiss after 4 seconds. Types: success, error, warning, info.

- **Tabs.tsx** — Horizontal tab bar. Props: `tabs: { id: string; label: string }[]`, `activeTab`, `onChange`. Renders a row of buttons with active indicator (bottom border or background).

- **Table.tsx** — Simple HTML table with Tailwind styling. Props: `columns: { key: string; label: string; sortable?: boolean }[]`, `data: any[]`, `onSort?`, `onRowClick?`. Striped rows, hover effect, loading skeleton.

- **Skeleton.tsx** — Animated placeholder. Props: `className` for sizing. Default: `h-4 w-full rounded bg-gray-200 animate-pulse`. Export also `SkeletonCard`, `SkeletonTable`.

- **EmptyState.tsx** — Centered message. Props: `icon?: React.ReactNode`, `title: string`, `description?: string`, `action?: { label: string; onClick: () => void }`.

- **ProgressBar.tsx** — Horizontal progress bar. Props: `value: number` (0-100), `label?: string`. Shows percentage.

- **Avatar.tsx** — Circular avatar with initials fallback. Props: `name: string`, `src?: string`, `size?: 'sm' | 'md' | 'lg'`. Generate initials from name, random pastel background color based on name hash.

- **Dropdown.tsx** — Trigger button + positioned menu. Props: `trigger: React.ReactNode`, `items: { label: string; onClick: () => void; icon?: React.ReactNode }[]`. Close on outside click.

---

## 7. Auth Pages

### `src/pages/auth/LandingPage.tsx`

```
Layout:
- Full viewport height, centered content
- "UniPaith" heading large
- Subtitle: "AI-Powered Admissions"
- Two CTA cards side by side:
  - Left card: "I'm a Student" — "Get matched with your ideal programs" — Link to /signup?role=student
  - Right card: "I'm an Institution" — "Find your best-fit students" — Link to /signup?role=institution
- Bottom: "Already have an account? Log in" link to /login
```

### `src/pages/auth/LoginPage.tsx`

```
Form (use react-hook-form + zod validation):
- Email input (required, email format)
- Password input (required, min 8 chars)
- "Log in" button (loading state during API call)
- Error display for wrong credentials
- "Don't have an account? Sign up" link to /signup

On submit:
1. Call authStore.login(email, password)
2. On success, navigate to /s/chat (student) or /i/dashboard (institution) based on user.role
3. On error, show error message below form
```

### `src/pages/auth/SignupPage.tsx`

```
Form (react-hook-form + zod):
- Role selection (read from URL param ?role= or show toggle):
  Two card-style radio buttons:
  - "Student" — "I'm looking for programs"
  - "Institution" — "I'm recruiting students"
- Email input
- Password input (with requirements hint: 8+ chars, uppercase, lowercase, number)
- Confirm password input (must match)
- "Create Account" button (loading state)
- Error display
- "Already have an account? Log in" link

On submit:
1. Call authStore.signup(email, password, role)
2. Signup auto-logs-in, so same redirect logic as login
```

---

## 8. Public Pages

### `src/pages/public/ProgramBrowsePage.tsx`

Public program search page (no auth required).

```
Layout:
- Top bar with "UniPaith" logo + "Log in" / "Sign up" links
- Search bar: text input for program search query
- Filter row: Country dropdown, Degree Type dropdown, Tuition range (min/max inputs)
- Results grid: ProgramCard components in 2-3 column grid
- Pagination: page numbers at bottom

API: GET /programs?q=...&country=...&degree_type=...&min_tuition=...&max_tuition=...&page=...&page_size=20
Response: PaginatedResponse<ProgramSummary>

Each ProgramCard shows:
- Program name (bold)
- Institution name + country
- Degree type badge
- Tuition (formatted as currency)
- Application deadline
- Click → /browse/{programId} (public detail) OR if logged in → /s/schools/{programId}
```

---

## 9. Student Layout

### `src/components/layout/StudentLayout.tsx`

```
Design: Chat-first layout — the AI chat is the primary experience.

┌──────────────────────────────────────────────┐
│  UniPaith                    [🔔 3] [Avatar▾]│
├────────┬─────────────────────────────────────┤
│        │                                     │
│  💬    │        <Outlet />                   │
│  👤    │                                     │
│  🔍    │                                     │
│  📄    │                                     │
│  💾    │                                     │
│  ✉️    │                                     │
│  📅    │                                     │
│        │                                     │
│  ──    │                                     │
│  ⚙️    │                                     │
│        │                                     │
├────────┴─────────────────────────────────────┤
│ Profile 67% complete ████████░░░░ [Complete] │ (only if < 100%)
└──────────────────────────────────────────────┘

Nav rail items (top to bottom):
- Chat (MessageSquare icon) → /s/chat
- Profile (User icon) → /s/profile
- Discover (Search icon) → /s/discover
- Applications (FileText icon) → /s/applications
- Saved (Heart icon) → /s/saved
- Messages (Mail icon) → /s/messages
- Calendar (Calendar icon) → /s/calendar
- [separator]
- Settings (Settings icon) → /s/settings

Nav rail behavior:
- 64px wide, icons only
- Active route icon has bg-gray-100 rounded + darker color
- Hover tooltip shows label
- Lucide icons, size 20

Top bar:
- Left: "UniPaith" text (text-lg font-semibold), links to /s/chat
- Right: Notification bell with unread count badge, Avatar dropdown (Profile, Settings, Logout)

Bottom bar (conditional):
- Only shows if onboarding completion < 100%
- Shows ProgressBar with "Profile X% complete" + "Complete" button → /s/profile
- API: GET /students/me/onboarding (cache, refetch on profile changes)

Use React Router <Outlet /> for the main content area.
```

### Notification bell component

Fetches `GET /notifications/unread-count` and shows a red badge with the count. Clicking opens a dropdown showing recent notifications from `GET /notifications?limit=10`. Each notification item has title + body + time. Click marks as read (`POST /notifications/{id}/read`) and navigates if there's a reference_type/reference_id.

---

## 10. Student Chat Page

### `src/pages/student/ChatPage.tsx`

This is the PRIMARY student view — the AI advisor chat.

```
Layout:
┌─────────────────────────────────────────┐
│  AI Advisor                             │
├─────────────────────────────────────────┤
│                                         │
│  (scrollable message area)              │
│                                         │
│  [AI bubble] Welcome to UniPaith! I'm   │
│  your AI admissions advisor. Let's      │
│  start building your profile...         │
│                                         │
│  [User bubble] I'm a senior at MIT...   │
│                                         │
│  [AI bubble] Great background! Based    │
│  on this, I've found some matches:      │
│  [Inline MatchCard components]          │
│                                         │
├─────────────────────────────────────────┤
│  [📎] [Type a message...        ] [↑]  │
│  Quick: [Update GPA] [My matches] [+]  │
└─────────────────────────────────────────┘

Implementation:
1. On mount, fetch conversations for the current user: GET /messages/conversations
2. Look for a conversation with subject "AI Advisor" or similar system conversation
   - If none exists, show a welcome state with a "Start chatting" prompt
   - For MVP, create a conversation when the user sends their first message
3. Load messages: GET /messages/conversations/{convId}?limit=50
4. Auto-scroll to bottom on new messages
5. Message input at bottom with send button
6. Send: POST /messages/conversations/{convId} with { content }
7. Poll for new messages every 5 seconds (TanStack Query refetchInterval)

Message rendering:
- AI messages: left-aligned, light gray bubble, with AI avatar
- User messages: right-aligned, dark bubble, with user avatar
- Use ChatBubble component for both

Rich content in AI messages:
- If message_body contains JSON-like patterns or special markers, render inline cards
- For MVP, just render plain text — rich content comes later

Quick actions bar (below input):
- Row of small pill buttons: "Update GPA", "My matches", "Upload document", "Help with essay"
- Clicking sends that text as a message

File attachment button (📎):
- Opens file picker → triggers document upload flow (presigned URL)
- Shows upload progress
- After upload, sends a message referencing the document

Chat is the HEART of the student experience. Make it feel fast and responsive.
```

---

## 11. Student Profile Page

### `src/pages/student/ProfilePage.tsx`

Read-only dashboard of the student's profile data with inline editing.

```
Layout:
┌─────────────────────────────────────────┐
│  My Profile                  [Edit ✏️]  │
│  ████████████████░░░░ 78% complete      │
├─────────────────────────────────────────┤
│                                         │
│  ┌── Basic Info ─────────────────────┐  │
│  │ Name: John Smith                  │  │
│  │ Nationality: American             │  │
│  │ Residence: Massachusetts, US      │  │
│  │ DOB: Jan 15, 2004                │  │
│  │                         [Edit]    │  │
│  └───────────────────────────────────┘  │
│                                         │
│  ┌── Academic Records ───────────────┐  │
│  │ MIT — B.S. Computer Science       │  │
│  │ GPA: 3.85/4.0 | 2022-Present     │  │
│  │                   [Edit] [Delete] │  │
│  │                                   │  │
│  │ [+ Add Academic Record]           │  │
│  └───────────────────────────────────┘  │
│                                         │
│  ┌── Test Scores ────────────────────┐  │
│  │ SAT: 1520 (Math: 790, Reading:730)│  │
│  │ Official | Oct 2023               │  │
│  │                   [Edit] [Delete] │  │
│  │                                   │  │
│  │ [+ Add Test Score]                │  │
│  └───────────────────────────────────┘  │
│                                         │
│  ┌── Activities ─────────────────────┐  │
│  │ Research — ML Lab at MIT          │  │
│  │ 2023-Present | 15 hrs/week        │  │
│  │                   [Edit] [Delete] │  │
│  │                                   │  │
│  │ [+ Add Activity]                  │  │
│  └───────────────────────────────────┘  │
│                                         │
│  ┌── Bio & Goals ────────────────────┐  │
│  │ Bio: "Passionate about AI and..." │  │
│  │ Goals: "PhD in ML, research..."   │  │
│  │                         [Edit]    │  │
│  └───────────────────────────────────┘  │
│                                         │
│  ┌── Preferences ────────────────────┐  │
│  │ Countries: US, UK, Canada         │  │
│  │ Budget: $30k - $60k / year        │  │
│  │ Funding: Partial scholarship      │  │
│  │ City: College town                │  │
│  │ Values: Research > Ranking > Cost │  │
│  │                         [Edit]    │  │
│  └───────────────────────────────────┘  │
│                                         │
│  ┌── Documents ──────────────────────┐  │
│  │ 📄 transcript_mit.pdf (2.3 MB)   │  │
│  │            [Download] [Delete]    │  │
│  │                                   │  │
│  │ [+ Upload Document]              │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘

API calls on mount:
- GET /students/me/profile (returns everything nested)
- GET /students/me/onboarding (completion %)
- GET /students/me/documents (document list)

Each section's [Edit] button opens a Modal with a form (react-hook-form):

Basic Info modal:
  Fields: first_name, last_name, date_of_birth (date picker), nationality, country_of_residence, bio_text (textarea), goals_text (textarea)
  Submit: PUT /students/me/profile

Academic Record add/edit modal:
  Fields: institution_name, degree_type (select), field_of_study, gpa (number), gpa_scale (select: "4.0", "percentage", "ib", "10.0"), start_date, end_date, is_current (checkbox — if checked, clear end_date), honors, thesis_title, country
  Submit: POST /students/me/academics or PUT /students/me/academics/{id}

Test Score add/edit modal:
  Fields: test_type (select from enum), total_score (number), section_scores (dynamic key-value pairs: e.g. "Math: 790, Reading: 730"), test_date, is_official (checkbox)
  Submit: POST /students/me/test-scores or PUT /students/me/test-scores/{id}

Activity add/edit modal:
  Fields: activity_type (select from enum), title, organization, description (textarea), start_date, end_date, is_current, hours_per_week, impact_description (textarea)
  Submit: POST /students/me/activities or PUT /students/me/activities/{id}

Preferences modal:
  Fields: preferred_countries (multi-text input / tags), preferred_regions (tags), preferred_city_size (select: big_city, college_town, suburban, rural, no_preference), preferred_climate, budget_min, budget_max (number inputs), funding_requirement (select: full_scholarship, partial, self_funded, flexible), program_size_preference (select), career_goals (tags), values_priorities (rating sliders 1-5 for: ranking, location, cost, research, diversity, etc.), dealbreakers (tags), goals_text (textarea)
  Submit: PUT /students/me/preferences

Document upload:
  Use FileUploader component (see shared components section)
  1. POST /students/me/documents/request-upload { document_type, file_name, content_type, file_size_bytes }
  2. PUT to the returned upload_url (direct S3 upload with progress)
  3. POST /students/me/documents/{id}/confirm

Delete handlers: DELETE endpoints, then refetch profile.

After ANY edit, invalidate the profile and onboarding TanStack Query caches so the progress bar updates.
```

---

## 12. Student Discover Page

### `src/pages/student/DiscoverPage.tsx`

```
Layout:
┌─────────────────────────────────────────┐
│  Discover Programs                      │
│  Profile 78% complete — complete for    │
│  better matches  [Complete profile →]   │
├─────────────────────────────────────────┤
│                                         │
│  ── Your AI Matches ──────────────────  │
│  (only if onboarding >= 80%)            │
│                                         │
│  🟢 SAFETY (4 programs)                 │
│  [MatchCard] [MatchCard] [MatchCard]... │
│                                         │
│  🟡 MATCH (6 programs)                  │
│  [MatchCard] [MatchCard] [MatchCard]... │
│                                         │
│  🔴 REACH (2 programs)                  │
│  [MatchCard] [MatchCard] [MatchCard]... │
│                                         │
│  ── Browse All Programs ──────────────  │
│  [Search...] [Country▾] [Degree▾] [$$] │
│  [ProgramCard grid]                     │
│  [Pagination]                           │
└─────────────────────────────────────────┘

AI Matches section:
- Fetch: GET /students/me/matches
- Group results by match_tier: tier 3 = safety (green), tier 2 = match (yellow), tier 1 = reach (red)
- Sort within each tier by match_score descending
- Show as horizontal scrollable row of MatchCard components per tier
- If onboarding < 80%, show a banner instead: "Complete your profile to see AI matches" with link to /s/profile
- If no matches yet (first load), show a loading/generating state

Browse section:
- Same as ProgramBrowsePage but embedded — uses GET /programs with search + filters
- Results as ProgramCard grid
- Pagination

MatchCard component (see shared components):
- Program name, institution name
- Match score as percentage (e.g. "92% fit")
- Tier badge (reach/match/safety with color)
- Key stat: tuition or acceptance rate
- Heart icon to save/unsave (POST/DELETE /students/me/saved)
- Click → navigate to /s/schools/{programId}

On card view, fire engagement signal:
POST /students/me/engagement { program_id, signal_type: "viewed_program", signal_value: 1 }
```

---

## 13. Student School Detail Page

### `src/pages/student/SchoolDetailPage.tsx`

```
Route: /s/schools/:programId

Layout:
┌─────────────────────────────────────────┐
│  [← Back to Discover]                   │
├─────────────────────────────────────────┤
│                                         │
│  MIT — Master of Science in CS          │
│  Cambridge, MA, United States           │
│  🟡 Match — 87% fit                     │
│                        [❤ Save] [Apply] │
│                                         │
├─────────────────────────────────────────┤
│  Overview | Requirements | Match Analysis│
├─────────────────────────────────────────┤
│                                         │
│  [Tab: Overview]                        │
│  Description: ...                        │
│  Degree: Masters | Duration: 24 months  │
│  Tuition: $58,000/year                  │
│  Acceptance rate: 8.2%                  │
│  Deadline: Jan 15, 2027                 │
│  Start: Sep 2027                        │
│                                         │
│  Highlights:                            │
│  • Top 5 CS program globally            │
│  • Strong AI/ML research group          │
│  • Industry partnerships                │
│                                         │
│  [Tab: Requirements]                    │
│  GRE: Required (min 320)               │
│  TOEFL: Required (min 100)             │
│  Min GPA: 3.5                           │
│  Letters of Rec: 3                      │
│                                         │
│  [Tab: Match Analysis]                  │
│  Score breakdown:                       │
│  Academic fit: ████████░░ 85%           │
│  Preference align: ███████░░░ 72%       │
│  Activity match: █████████░ 91%         │
│                                         │
│  AI Explanation:                        │
│  "Your strong research background in    │
│  ML and 3.85 GPA make you competitive   │
│  for this program. Your publications    │
│  align well with the department's       │
│  focus areas..."                        │
│                                         │
│  ── Upcoming Events ───────────────     │
│  🗓 Info Session — Apr 5 [RSVP]         │
│  🗓 Webinar — Apr 12 [RSVP]            │
│                                         │
│  ── Application Status ────────────     │
│  (if applied) Status: Under Review      │
│  (if not) [Start Application →]         │
└─────────────────────────────────────────┘

API calls:
- GET /programs/{programId} — full program details
- GET /students/me/matches/{programId} — match result + explanation (if available)
- GET /events?program_id={programId}&limit=5 — upcoming events for this program
- Check if application exists: from applications list cache or GET /applications/me filtered

On page load, fire engagement:
POST /students/me/engagement { program_id, signal_type: "viewed_program", signal_value: 1 }

Track time spent: fire signal_type "time_spent" with seconds when user leaves page (useEffect cleanup).

Save button: POST /students/me/saved { program_id } or DELETE /students/me/saved/{programId}
Apply button: POST /applications { program_id } → navigate to /s/applications/{appId}
RSVP button: POST /events/{eventId}/rsvp
```

---

## 14. Student Applications Pages

### `src/pages/student/ApplicationsPage.tsx`

```
Layout:
┌─────────────────────────────────────────┐
│  My Applications                        │
│  [All] [Draft] [Submitted] [Under Review] [Decision]│
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────────────────────────────┐│
│  │ MIT — MS Computer Science           ││
│  │ Status: Under Review  Match: 87%    ││
│  │ Submitted: Mar 15, 2026             ││
│  │ Checklist: 100% complete            ││
│  │                        [View →]     ││
│  └─────────────────────────────────────┘│
│                                         │
│  ┌─────────────────────────────────────┐│
│  │ Stanford — PhD Machine Learning     ││
│  │ Status: Draft          Match: 92%   ││
│  │ Checklist: 60% complete             ││
│  │                        [Continue →] ││
│  └─────────────────────────────────────┘│
│                                         │
│  (Empty state if no applications)       │
│  "No applications yet. Discover         │
│   programs to get started."  [Discover→]│
└─────────────────────────────────────────┘

API: GET /applications/me
Filter tabs: filter client-side by status field
Each card: program name (from nested program data), status badge, match score, submitted date, checklist completion
Click → /s/applications/{appId}
```

### `src/pages/student/ApplicationDetailPage.tsx`

```
Route: /s/applications/:appId

Layout:
┌─────────────────────────────────────────┐
│  [← My Applications]                   │
│  MIT — MS Computer Science              │
│  Status: Draft → ● ○ ○ ○ ○  (timeline) │
│                                         │
├──────────┬──────────────────────────────┤
│ Sidebar  │  Main content               │
│          │                              │
│ Checklist│  [Active tab content]        │
│ ────────│                              │
│ ☑ Profile│                              │
│ ☑ Trans- │                              │
│   cript  │                              │
│ ☐ Essay  │                              │
│ ☐ Resume │                              │
│ ☑ Recs   │                              │
│ ────────│                              │
│ 60%      │                              │
│ complete │                              │
│          │                              │
│ [Submit] │                              │
│ (disabled│                              │
│  if <100)│                              │
├──────────┴──────────────────────────────┤
│  [Documents] [Essays] [Resume] [Offer]  │
└─────────────────────────────────────────┘

Sidebar - Checklist:
- Fetch: POST /students/me/applications/{appId}/checklist (generates if not exists)
  then GET /students/me/applications/{appId}/checklist
- Show each item with checkbox (read-only — status updates automatically as items are completed)
- Show completion percentage
- Submit button: only enabled if readiness check passes
  - Call GET /students/me/applications/{appId}/readiness before showing submit
  - If ready: POST /applications/me/{appId}/submit
  - If not: show missing items list

Tab: Documents
- List documents associated with this application (from profile documents)
- Upload new document specific to this application
- Uses the same upload flow as profile documents

Tab: Essays
- List essays for this program: GET /students/me/essays?program_id={programId}
- Each essay shows: prompt text, content preview, word count, status badge, AI feedback
- [+ New Essay] button → modal/form:
  - essay_type: select (personal_statement, diversity, why_school, etc.)
  - prompt_text: textarea (the essay question)
  - content: textarea (the essay itself)
  - POST /students/me/essays { program_id, essay_type, content, prompt_text }
- Edit essay: PUT /students/me/essays/{essayId} { content }
- Request AI feedback: POST /students/me/essays/{essayId}/feedback { feedback_type: "general" }
  - Shows loading state, then displays ai_feedback JSON in a formatted card
- Finalize essay: POST /students/me/essays/{essayId}/finalize

Tab: Resume
- Show resumes targeting this program: GET /students/me/resume?target_program_id={programId}
- If none: [Generate Resume] button → POST /students/me/resume/generate { format_type: "standard", target_program_id }
- Edit resume content: PUT /students/me/resume/{resumeId} { content }
- Request feedback: POST /students/me/resume/{resumeId}/feedback { feedback_type: "general" }
- Finalize: POST /students/me/resume/{resumeId}/finalize

Tab: Offer (only visible if decision === 'admitted')
- Show offer details from the application response
- Accept/Decline buttons: POST /applications/me/{appId}/offer/respond { response: "accepted" | "declined", decline_reason }
- If declined, show textarea for decline reason

Status timeline at top:
- Draft → Submitted → Under Review → Interview → Decision
- Highlight current status, show dates where available
```

---

## 15. Student Saved List Page

### `src/pages/student/SavedListPage.tsx`

```
Layout:
┌─────────────────────────────────────────┐
│  Saved Programs           [Compare (3)] │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────────────────────────────┐│
│  │ ☐ MIT — MS Computer Science         ││
│  │    Tuition: $58k | Deadline: Jan 15 ││
│  │    Notes: "Top choice, need GRE"    ││
│  │    [Edit notes] [Remove] [View →]   ││
│  └─────────────────────────────────────┘│
│                                         │
│  ┌─────────────────────────────────────┐│
│  │ ☐ Stanford — PhD Machine Learning   ││
│  │    Tuition: $55k | Deadline: Dec 1  ││
│  │    Notes: ""                         ││
│  │    [Edit notes] [Remove] [View →]   ││
│  └─────────────────────────────────────┘│
│                                         │
│  (Empty state: "Save programs from      │
│   Discover to compare them here")       │
└─────────────────────────────────────────┘

API:
- List: GET /students/me/saved
- Remove: DELETE /students/me/saved/{programId}
- Edit notes: PUT /students/me/saved/{programId}/notes { notes }

Comparison feature:
- Checkboxes on each card to select (2-5 programs)
- "Compare" button in header (shows count of selected)
- Click → POST /students/me/saved/compare { program_ids: [...] }
- Opens a modal/page showing side-by-side comparison table:
  Columns = selected programs
  Rows = tuition, acceptance rate, deadline, degree type, department, location, match score
```

---

## 16. Student Messages Page

### `src/pages/student/MessagesPage.tsx`

```
Route: /s/messages or /s/messages/:convId

Layout (two-panel):
┌───────────────────┬─────────────────────┐
│  Conversations    │  Messages           │
│                   │                     │
│  [+ New Message]  │  MIT Admissions     │
│                   │  Subject: Question  │
│  ┌─────────────┐ │                     │
│  │ MIT Admiss  │ │  [inst] Thank you   │
│  │ "Thank you  │ │  for your inquiry..  │
│  │ Mar 28"     │ │                     │
│  └─────────────┘ │  [you] I wanted to  │
│                   │  ask about the...   │
│  ┌─────────────┐ │                     │
│  │ Stanford    │ │                     │
│  │ "We received│ │                     │
│  │ Mar 25"     │ │                     │
│  └─────────────┘ │  ────────────────── │
│                   │  [Type message...][↑]│
└───────────────────┴─────────────────────┘

API:
- List conversations: GET /messages/conversations
- Load messages: GET /messages/conversations/{convId}?limit=50
- Send message: POST /messages/conversations/{convId} { content }
- Create conversation: POST /messages/conversations { institution_id, subject, program_id }

Left panel:
- List of conversations sorted by last_message_at desc
- Each shows: institution name, last message preview, date
- Unread indicator (if last message sender_type is "institution" and read_at is null)
- Click selects conversation and loads messages in right panel
- URL updates to /s/messages/{convId}

Right panel:
- Message thread, scrolled to bottom
- Messages grouped: institution messages left-aligned, student messages right-aligned
- Timestamps between message groups
- Input bar at bottom to send new message

New message modal:
- Select institution (from conversations or from a search)
- Subject input
- Optional program_id selection
- First message content
- POST /messages/conversations to create, then load the new conversation

Poll for new messages: refetchInterval 5000ms on the messages query
```

---

## 17. Student Calendar Page

### `src/pages/student/CalendarPage.tsx`

```
Layout:
┌─────────────────────────────────────────┐
│  Calendar            [Month ▾] [← →]   │
├─────────────────────────────────────────┤
│  Mon  Tue  Wed  Thu  Fri  Sat  Sun      │
│  ...  ...  ...  ...  ...  ...  ...      │
│              3         5                 │
│           📅App     🎤Info              │
│           deadline   session             │
│                                         │
│       12                                │
│    🎤Interview                          │
│    w/ MIT                               │
│                                         │
│  ... ... ... ... ... ... ...             │
├─────────────────────────────────────────┤
│  Upcoming:                              │
│  • Apr 3 — Info Session: MIT CS Webinar │
│  • Apr 5 — Deadline: Stanford PhD App   │
│  • Apr 12 — Interview: MIT (video)      │
└─────────────────────────────────────────┘

Data sources:
- Events RSVPs: GET /events/me/rsvps → for each RSVP, get event details
- Application deadlines: from GET /applications/me → extract application_deadline from program
- Interviews: GET /interviews/me

Calendar implementation:
- Simple monthly grid calendar built with date-fns
- Each day cell shows event dots/badges
- Clicking a day shows events for that day in a detail panel below
- Below the calendar: "Upcoming" list showing next 10 events sorted by date

Each event type has an icon:
- 📅 Deadlines (from applications)
- 🎤 Events (from RSVPs)
- 🎙 Interviews
- Download ICS: GET /events/{eventId}/calendar → triggers file download
```

---

## 18. Student Settings Page

### `src/pages/student/SettingsPage.tsx`

```
Layout:
┌─────────────────────────────────────────┐
│  Settings                               │
├─────────────────────────────────────────┤
│                                         │
│  Account                                │
│  Email: john@example.com                │
│  Role: Student                          │
│  Member since: Jan 2026                 │
│                                         │
│  Notifications                          │
│  ☑ Email notifications enabled          │
│  ☑ Application updates                  │
│  ☑ New matches                          │
│  ☑ Messages                             │
│  ☐ Marketing & events                   │
│  [Save preferences]                     │
│                                         │
│  Danger zone                            │
│  [Log out]                              │
│  [Delete account]                       │
└─────────────────────────────────────────┘

API:
- Account info: from auth store (user object)
- Notification prefs: GET /notifications/preferences
- Update prefs: PUT /notifications/preferences { email_enabled, preferences: {...} }
- Logout: authStore.logout() → redirect to /
```

---

## 19. Student API Modules

Create these files in `src/api/`, each exporting functions that call apiClient:

### `src/api/auth.ts`
```typescript
import apiClient from './client'

export const loginApi = (email: string, password: string) =>
  apiClient.post('/auth/login', { email, password }).then(r => r.data)

export const signupApi = (email: string, password: string, role: string) =>
  apiClient.post('/auth/signup', { email, password, role }).then(r => r.data)

export const refreshTokenApi = (refreshToken: string) =>
  apiClient.post('/auth/refresh', { refresh_token: refreshToken }).then(r => r.data)

export const getMeApi = () =>
  apiClient.get('/auth/me').then(r => r.data)
```

### `src/api/students.ts`
```typescript
import apiClient from './client'

// Profile
export const getProfile = () => apiClient.get('/students/me/profile').then(r => r.data)
export const updateProfile = (data: any) => apiClient.put('/students/me/profile', data).then(r => r.data)

// Onboarding
export const getOnboarding = () => apiClient.get('/students/me/onboarding').then(r => r.data)
export const getNextStep = () => apiClient.get('/students/me/onboarding/next-step').then(r => r.data)

// Academics
export const listAcademics = () => apiClient.get('/students/me/academics').then(r => r.data)
export const createAcademic = (data: any) => apiClient.post('/students/me/academics', data).then(r => r.data)
export const updateAcademic = (id: string, data: any) => apiClient.put(`/students/me/academics/${id}`, data).then(r => r.data)
export const deleteAcademic = (id: string) => apiClient.delete(`/students/me/academics/${id}`)

// Test Scores
export const listTestScores = () => apiClient.get('/students/me/test-scores').then(r => r.data)
export const createTestScore = (data: any) => apiClient.post('/students/me/test-scores', data).then(r => r.data)
export const updateTestScore = (id: string, data: any) => apiClient.put(`/students/me/test-scores/${id}`, data).then(r => r.data)
export const deleteTestScore = (id: string) => apiClient.delete(`/students/me/test-scores/${id}`)

// Activities
export const listActivities = () => apiClient.get('/students/me/activities').then(r => r.data)
export const createActivity = (data: any) => apiClient.post('/students/me/activities', data).then(r => r.data)
export const updateActivity = (id: string, data: any) => apiClient.put(`/students/me/activities/${id}`, data).then(r => r.data)
export const deleteActivity = (id: string) => apiClient.delete(`/students/me/activities/${id}`)

// Preferences
export const getPreferences = () => apiClient.get('/students/me/preferences').then(r => r.data)
export const upsertPreferences = (data: any) => apiClient.put('/students/me/preferences', data).then(r => r.data)
```

### `src/api/matching.ts`
```typescript
import apiClient from './client'

export const getMatches = (forceRefresh = false) =>
  apiClient.get('/students/me/matches', { params: { force_refresh: forceRefresh } }).then(r => r.data)

export const getMatchDetail = (programId: string) =>
  apiClient.get(`/students/me/matches/${programId}`).then(r => r.data)

export const logEngagement = (programId: string, signalType: string, signalValue: number) =>
  apiClient.post('/students/me/engagement', { program_id: programId, signal_type: signalType, signal_value: signalValue }).then(r => r.data)
```

### `src/api/programs.ts`
```typescript
import apiClient from './client'

export const searchPrograms = (params: {
  q?: string; country?: string; degree_type?: string;
  min_tuition?: number; max_tuition?: number; page?: number; page_size?: number
}) => apiClient.get('/programs', { params }).then(r => r.data)

export const getProgram = (id: string) =>
  apiClient.get(`/programs/${id}`).then(r => r.data)

export const semanticSearch = (q: string, limit = 10) =>
  apiClient.get('/programs/search/semantic', { params: { q, limit } }).then(r => r.data)
```

### `src/api/applications.ts`
```typescript
import apiClient from './client'

export const createApplication = (programId: string) =>
  apiClient.post('/applications', { program_id: programId }).then(r => r.data)

export const listMyApplications = () =>
  apiClient.get('/applications/me').then(r => r.data)

export const getMyApplication = (appId: string) =>
  apiClient.get(`/applications/me/${appId}`).then(r => r.data)

export const submitApplication = (appId: string) =>
  apiClient.post(`/applications/me/${appId}/submit`).then(r => r.data)

export const withdrawApplication = (appId: string) =>
  apiClient.delete(`/applications/me/${appId}`)

export const respondToOffer = (appId: string, response: string, declineReason?: string) =>
  apiClient.post(`/applications/me/${appId}/offer/respond`, { response, decline_reason: declineReason }).then(r => r.data)
```

### `src/api/documents.ts`
```typescript
import apiClient from './client'
import axios from 'axios'

export const requestUpload = (data: { document_type: string; file_name: string; content_type: string; file_size_bytes: number }) =>
  apiClient.post('/students/me/documents/request-upload', data).then(r => r.data)

export const confirmUpload = (docId: string) =>
  apiClient.post(`/students/me/documents/${docId}/confirm`).then(r => r.data)

export const listDocuments = () =>
  apiClient.get('/students/me/documents').then(r => r.data)

export const getDocument = (docId: string) =>
  apiClient.get(`/students/me/documents/${docId}`).then(r => r.data)

export const deleteDocument = (docId: string) =>
  apiClient.delete(`/students/me/documents/${docId}`)

// Direct upload to S3 presigned URL (not through apiClient)
export const uploadToS3 = (url: string, file: File, onProgress?: (pct: number) => void) =>
  axios.put(url, file, {
    headers: { 'Content-Type': file.type },
    onUploadProgress: (e) => {
      if (onProgress && e.total) onProgress(Math.round((e.loaded / e.total) * 100))
    },
  })
```

### `src/api/essays.ts`
```typescript
import apiClient from './client'

export const createEssay = (data: { program_id: string; essay_type: string; content: string; prompt_text?: string }) =>
  apiClient.post('/students/me/essays', data).then(r => r.data)

export const listEssays = (programId?: string) =>
  apiClient.get('/students/me/essays', { params: { program_id: programId } }).then(r => r.data)

export const getEssay = (essayId: string) =>
  apiClient.get(`/students/me/essays/${essayId}`).then(r => r.data)

export const updateEssay = (essayId: string, data: { content?: string; prompt_text?: string }) =>
  apiClient.put(`/students/me/essays/${essayId}`, data).then(r => r.data)

export const finalizeEssay = (essayId: string) =>
  apiClient.post(`/students/me/essays/${essayId}/finalize`).then(r => r.data)

export const requestEssayFeedback = (essayId: string, feedbackType = 'general') =>
  apiClient.post(`/students/me/essays/${essayId}/feedback`, { feedback_type: feedbackType }).then(r => r.data)
```

### `src/api/resumes.ts`
```typescript
import apiClient from './client'

export const generateResume = (data: { format_type: string; target_program_id?: string }) =>
  apiClient.post('/students/me/resume/generate', data).then(r => r.data)

export const listResumes = (targetProgramId?: string) =>
  apiClient.get('/students/me/resume', { params: { target_program_id: targetProgramId } }).then(r => r.data)

export const updateResume = (resumeId: string, content: any) =>
  apiClient.put(`/students/me/resume/${resumeId}`, { content }).then(r => r.data)

export const finalizeResume = (resumeId: string) =>
  apiClient.post(`/students/me/resume/${resumeId}/finalize`).then(r => r.data)

export const requestResumeFeedback = (resumeId: string, feedbackType = 'general') =>
  apiClient.post(`/students/me/resume/${resumeId}/feedback`, { feedback_type: feedbackType }).then(r => r.data)
```

### `src/api/saved-lists.ts`
```typescript
import apiClient from './client'

export const listSaved = () =>
  apiClient.get('/students/me/saved').then(r => r.data)

export const saveProgram = (programId: string, notes?: string) =>
  apiClient.post('/students/me/saved', { program_id: programId, notes }).then(r => r.data)

export const unsaveProgram = (programId: string) =>
  apiClient.delete(`/students/me/saved/${programId}`)

export const updateSavedNotes = (programId: string, notes: string) =>
  apiClient.put(`/students/me/saved/${programId}/notes`, { notes }).then(r => r.data)

export const comparePrograms = (programIds: string[]) =>
  apiClient.post('/students/me/saved/compare', { program_ids: programIds }).then(r => r.data)
```

### `src/api/messaging.ts`
```typescript
import apiClient from './client'

export const listConversations = () =>
  apiClient.get('/messages/conversations').then(r => r.data)

export const createConversation = (data: { institution_id: string; subject?: string; program_id?: string; student_id?: string }) =>
  apiClient.post('/messages/conversations', data).then(r => r.data)

export const getMessages = (convId: string, limit = 50, before?: string) =>
  apiClient.get(`/messages/conversations/${convId}`, { params: { limit, before } }).then(r => r.data)

export const sendMessage = (convId: string, content: string) =>
  apiClient.post(`/messages/conversations/${convId}`, { content }).then(r => r.data)
```

### `src/api/events.ts`
```typescript
import apiClient from './client'

export const listEvents = (params?: { program_id?: string; institution_id?: string; event_type?: string; limit?: number }) =>
  apiClient.get('/events', { params }).then(r => r.data)

export const rsvpEvent = (eventId: string) =>
  apiClient.post(`/events/${eventId}/rsvp`).then(r => r.data)

export const cancelRsvp = (eventId: string) =>
  apiClient.delete(`/events/${eventId}/rsvp`)

export const downloadIcs = (eventId: string) =>
  apiClient.get(`/events/${eventId}/calendar`, { responseType: 'blob' }).then(r => r.data)

export const getMyRsvps = () =>
  apiClient.get('/events/me/rsvps').then(r => r.data)
```

### `src/api/interviews.ts`
```typescript
import apiClient from './client'

export const getMyInterviews = () =>
  apiClient.get('/interviews/me').then(r => r.data)

export const confirmInterview = (interviewId: string, confirmedTime: string) =>
  apiClient.post(`/interviews/${interviewId}/confirm`, { confirmed_time: confirmedTime }).then(r => r.data)
```

### `src/api/notifications.ts`
```typescript
import apiClient from './client'

export const listNotifications = (params?: { unread_only?: boolean; limit?: number; offset?: number }) =>
  apiClient.get('/notifications', { params }).then(r => r.data)

export const getUnreadCount = () =>
  apiClient.get('/notifications/unread-count').then(r => r.data)

export const markRead = (notificationId: string) =>
  apiClient.post(`/notifications/${notificationId}/read`).then(r => r.data)

export const markAllRead = () =>
  apiClient.post('/notifications/read-all').then(r => r.data)

export const getNotificationPrefs = () =>
  apiClient.get('/notifications/preferences').then(r => r.data)

export const updateNotificationPrefs = (data: { email_enabled: boolean; preferences: Record<string, boolean> }) =>
  apiClient.put('/notifications/preferences', data).then(r => r.data)
```

---

## 20. Shared Components

### `src/components/shared/ChatBubble.tsx`

```typescript
Props:
- message: Message
- isOwn: boolean (student's own message vs AI/institution)
- avatar?: { name: string; src?: string }

Renders:
- Left-aligned gray bubble (if !isOwn) or right-aligned dark bubble (if isOwn)
- Avatar circle on the outside edge
- Message text with whitespace-pre-wrap
- Timestamp below in small gray text
- Max width 80% of container
```

### `src/components/shared/MatchCard.tsx`

```typescript
Props:
- match: MatchResult & { program?: Program }
- onSave?: (programId: string) => void
- onUnsave?: (programId: string) => void
- isSaved?: boolean

Renders:
- Card with:
  - Program name (bold, truncated)
  - Institution name (from program)
  - Match score as percentage (large, colored by tier)
  - Tier badge: Reach (red), Match (yellow), Safety (green)
  - One key stat: tuition or acceptance rate
  - Heart icon (toggles save/unsave)
- Click navigates to /s/schools/{programId}
```

### `src/components/shared/ProgramCard.tsx`

```typescript
Props:
- program: ProgramSummary
- onClick?: () => void

Renders:
- Card with:
  - Program name (bold)
  - Institution name + country
  - Degree type badge
  - Tuition (formatted)
  - Deadline (if set)
  - Click → onClick or navigate
```

### `src/components/shared/FileUploader.tsx`

```typescript
Props:
- documentType: string
- onUploadComplete: (doc: StudentDocument) => void
- acceptedTypes?: string[] (mime types)
- maxSize?: number (bytes, default 10MB)

Behavior:
1. Drag-and-drop zone OR click to select file
2. Validate file type and size client-side
3. Call requestUpload() API
4. Upload directly to S3 presigned URL with progress bar
5. Call confirmUpload() API
6. Call onUploadComplete with the confirmed document

Renders:
- Dashed border drop zone with upload icon
- "Drop file here or click to browse"
- During upload: progress bar with percentage
- After upload: success checkmark + filename
- On error: red error message
```

### `src/components/shared/StatusBadge.tsx`

```typescript
Props:
- status: string

Auto-maps status strings to colors:
- draft → gray
- submitted → blue
- under_review → yellow
- interview → purple
- decision_made → orange
- admitted → green
- rejected → red
- waitlisted → yellow
- published → green
- completed → green
- cancelled → gray
```

### `src/components/shared/EmptyState.tsx`

```typescript
Props:
- icon?: React.ReactNode (Lucide icon)
- title: string
- description?: string
- action?: { label: string; onClick: () => void }

Renders:
- Centered vertically and horizontally within parent
- Large icon (48px, gray-400)
- Title (text-lg, font-medium)
- Description (text-sm, gray-500)
- Optional action Button
```

---

## VERIFICATION CHECKLIST

After building Part 1, verify:

- [ ] `npm run build` succeeds with zero TypeScript errors
- [ ] `/` shows landing page with Student/Institution CTAs
- [ ] `/signup` allows creating a student account
- [ ] `/login` authenticates and redirects to `/s/chat`
- [ ] Student nav rail shows all icons and navigates correctly
- [ ] `/s/profile` loads and displays profile data (or empty state)
- [ ] Profile edit modals work (create academic record, test score, etc.)
- [ ] `/s/discover` shows program search (and matches if profile >= 80%)
- [ ] `/s/schools/:id` shows program detail with match analysis
- [ ] `/s/applications` lists applications
- [ ] `/s/applications/:id` shows checklist, essays, resume tabs
- [ ] `/s/saved` shows saved programs with compare feature
- [ ] `/s/messages` shows conversations with send capability
- [ ] `/s/calendar` renders monthly calendar with events
- [ ] `/s/chat` shows message interface with send + polling
- [ ] Notification bell shows unread count
- [ ] Token refresh works (access token expires → auto-refresh)
- [ ] Wrong role redirects (institution trying to access /s/ → redirected)
- [ ] All API errors show user-friendly toast messages

---

## IMPORTANT NOTES FOR CODING TOOL

1. **Do NOT install a component library** (no shadcn, no Material UI, no Ant Design). Build all UI primitives from scratch with Tailwind. Keep it simple.

2. **Every API call must have error handling.** Use TanStack Query's `onError` or try/catch with the toast system.

3. **Invalidate related queries after mutations.** E.g., after `createAcademic`, invalidate `['profile']` and `['onboarding']` query keys.

4. **All forms use react-hook-form + zod schemas.** Define the zod schema next to the form component.

5. **Responsive is NOT a priority for MVP.** Desktop-first, minimum 1024px viewport assumed.

6. **Loading states everywhere.** Use Skeleton components while data fetches. Never show a blank white page.

7. **The `api.ts` file in src root should be deleted.** It's the old test shell's API file, replaced by `api/client.ts`.

8. **main.tsx should render App directly** — the existing main.tsx might have StrictMode wrapper, that's fine, keep it.
