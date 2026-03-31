# UniPaith Frontend — COMPLETE BUILD INSTRUCTIONS (Part 2: Institution Side)

> **What this file is:** Part 2 of the comprehensive frontend build prompt. Part 1 (BUILD_FRONTEND_PART1.md) covers Foundation, Auth, API Client, TypeScript types, shared components, and ALL student pages. This file covers ALL institution-facing pages and institution API modules.
>
> **Prerequisites:** Part 1 must be fully built first. This file assumes all shared infrastructure (routing, auth, types, UI primitives, api/client.ts) already exists.
>
> **Product vision:** The institution side is **"An AI-powered student admissions operating system."** This is a pipeline-centric Kanban workspace. The PipelinePage is THE primary view — everything else feeds into or supports it.

---

## TABLE OF CONTENTS

1. [Install Additional Dependencies](#1-install-additional-dependencies)
2. [Institution Layout](#2-institution-layout)
3. [Institution TypeScript Types (additions)](#3-institution-typescript-types-additions)
4. [Dashboard Page](#4-dashboard-page)
5. [Setup Page (First-Run Wizard)](#5-setup-page-first-run-wizard)
6. [Programs Page](#6-programs-page)
7. [Program Editor Page](#7-program-editor-page)
8. [Pipeline Page (THE Primary View)](#8-pipeline-page-the-primary-view)
9. [Student Detail Page (Institution View)](#9-student-detail-page-institution-view)
10. [Review Queue Page](#10-review-queue-page)
11. [Interviews Page](#11-interviews-page)
12. [Messaging Page (Institution)](#12-messaging-page-institution)
13. [Segments Page](#13-segments-page)
14. [Campaigns Page](#14-campaigns-page)
15. [Events Page](#15-events-page)
16. [Analytics Page](#16-analytics-page)
17. [Institution Settings Page](#17-institution-settings-page)
18. [Institution API Modules](#18-institution-api-modules)
19. [Institution-Specific Shared Components](#19-institution-specific-shared-components)
20. [Verification Checklist](#20-verification-checklist)

---

## 1. Install Additional Dependencies

```bash
cd frontend
npm install @dnd-kit/core @dnd-kit/sortable @dnd-kit/utilities
```

This adds drag-and-drop support for the Pipeline Kanban board. All other deps were installed in Part 1.

---

## 2. Institution Layout

### `src/components/layout/InstitutionLayout.tsx`

```typescript
import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../stores/auth-store'
import { useUIStore } from '../../stores/ui-store'
import {
  LayoutDashboard, GraduationCap, Kanban, FileCheck, Video,
  MessageSquare, Users, Megaphone, CalendarDays, BarChart3,
  Settings, ChevronLeft, ChevronRight, Bell, Search, LogOut
} from 'lucide-react'

const NAV_SECTIONS = [
  {
    label: 'Core',
    items: [
      { to: '/i/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
      { to: '/i/programs', icon: GraduationCap, label: 'Programs' },
      { to: '/i/pipeline', icon: Kanban, label: 'Pipeline' },
      { to: '/i/reviews', icon: FileCheck, label: 'Reviews' },
      { to: '/i/interviews', icon: Video, label: 'Interviews' },
      { to: '/i/messages', icon: MessageSquare, label: 'Messages' },
    ],
  },
  {
    label: 'Outreach',
    items: [
      { to: '/i/segments', icon: Users, label: 'Segments' },
      { to: '/i/campaigns', icon: Megaphone, label: 'Campaigns' },
      { to: '/i/events', icon: CalendarDays, label: 'Events' },
    ],
  },
  {
    label: 'Admin',
    items: [
      { to: '/i/analytics', icon: BarChart3, label: 'Analytics' },
      { to: '/i/settings', icon: Settings, label: 'Settings' },
    ],
  },
]

export default function InstitutionLayout() {
  const { user, logout } = useAuthStore()
  const { sidebarCollapsed, toggleSidebar } = useUIStore()
  const navigate = useNavigate()
  const sidebarWidth = sidebarCollapsed ? 'w-16' : 'w-60'

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className={`${sidebarWidth} flex flex-col border-r border-gray-200 bg-white transition-all duration-200`}>
        {/* Logo area */}
        <div className="flex items-center justify-between h-14 px-4 border-b border-gray-100">
          {!sidebarCollapsed && (
            <span className="text-lg font-bold text-indigo-600">UniPaith</span>
          )}
          <button onClick={toggleSidebar} className="p-1 rounded hover:bg-gray-100">
            {sidebarCollapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
          </button>
        </div>

        {/* Nav sections */}
        <nav className="flex-1 overflow-y-auto py-4">
          {NAV_SECTIONS.map(section => (
            <div key={section.label} className="mb-4">
              {!sidebarCollapsed && (
                <div className="px-4 mb-1 text-[11px] font-semibold uppercase tracking-wider text-gray-400">
                  {section.label}
                </div>
              )}
              {section.items.map(item => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-4 py-2 mx-2 rounded-md text-sm transition-colors ${
                      isActive
                        ? 'bg-indigo-50 text-indigo-700 font-medium'
                        : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                    }`
                  }
                >
                  <item.icon size={18} />
                  {!sidebarCollapsed && <span>{item.label}</span>}
                </NavLink>
              ))}
            </div>
          ))}
        </nav>
      </aside>

      {/* Main content area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top bar */}
        <header className="flex items-center justify-between h-14 px-6 border-b border-gray-200 bg-white">
          <div className="flex items-center gap-4">
            {/* Search bar placeholder */}
            <div className="relative">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Search students, programs..."
                className="w-72 pl-9 pr-4 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              />
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* Notification bell — uses same useNotifications hook from Part 1 */}
            <button className="relative p-2 rounded-lg hover:bg-gray-100">
              <Bell size={18} className="text-gray-600" />
              {/* Unread badge — wire up from useQuery(['unread-count']) */}
            </button>

            {/* User dropdown */}
            <div className="relative group">
              <button className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-gray-100">
                <div className="w-7 h-7 rounded-full bg-indigo-100 flex items-center justify-center text-xs font-medium text-indigo-700">
                  {user?.email?.charAt(0).toUpperCase()}
                </div>
                {!sidebarCollapsed && (
                  <span className="text-sm text-gray-700">{user?.email}</span>
                )}
              </button>
              {/* Dropdown menu */}
              <div className="hidden group-hover:block absolute right-0 top-full mt-1 w-48 bg-white border border-gray-200 rounded-lg shadow-lg py-1 z-50">
                <button
                  onClick={() => navigate('/i/settings')}
                  className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                >
                  Settings
                </button>
                <button
                  onClick={logout}
                  className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
                >
                  <LogOut size={14} /> Sign out
                </button>
              </div>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
```

---

## 3. Institution TypeScript Types (additions)

Add these to `src/types/index.ts` (the file from Part 1). These types are used only on the institution side.

```typescript
// ============ INSTITUTION TYPES (Part 2 additions) ============

// Already defined in Part 1: Institution, Program, ProgramSummary, PaginatedResponse,
// Application, OfferLetter, Conversation, Message, EventItem, RSVP,
// Interview, Notification, NotificationPreference

// --- Review / Scoring ---
export interface Rubric {
  id: string
  institution_id: string
  program_id: string | null
  rubric_name: string
  criteria: RubricCriterion[] | null
  is_active: boolean
  created_at: string
}

export interface RubricCriterion {
  name: string
  weight: number
  description?: string
  scale_min?: number
  scale_max?: number
}

export interface ApplicationScore {
  id: string
  application_id: string
  reviewer_id: string
  rubric_id: string
  criterion_scores: Record<string, number> | null
  total_weighted_score: number | null
  reviewer_notes: string | null
  scored_by_type: 'human' | 'ai' | null
  scored_at: string
}

export interface ReviewAssignment {
  id: string
  application_id: string
  reviewer_id: string
  assigned_at: string
  due_date: string | null
  status: 'pending' | 'in_progress' | 'completed' | null
}

export interface AIReviewSummary {
  summary: string
  strengths: string[]
  concerns: string[]
  recommended_score_range: { min: number; max: number } | null
}

export interface PipelineData {
  total: number
  program_id: string | null
  // Pipeline columns with application arrays — dynamic shape from backend
  [column: string]: any
}

// --- Segments ---
export interface Segment {
  id: string
  institution_id: string
  program_id: string | null
  segment_name: string
  criteria: Record<string, any> | null
  is_active: boolean
  created_at: string
  updated_at: string
}

// --- Interview Scoring ---
export interface InterviewScore {
  id: string
  interview_id: string
  interviewer_id: string
  criterion_scores: Record<string, number> | null
  total_weighted_score: number | null
  interviewer_notes: string | null
  recommendation: 'strong_admit' | 'admit' | 'borderline' | 'reject' | null
}

// --- Kanban types for Pipeline ---
export type PipelineColumn =
  | 'discovered'
  | 'applied'
  | 'under_review'
  | 'interview'
  | 'decision_made'
  | 'enrolled'

export interface PipelineCard {
  application: Application
  student_name: string
  match_score: number | null
  last_activity: string | null
  scores: ApplicationScore[]
}
```

---

## 4. Dashboard Page

### `src/pages/institution/DashboardPage.tsx`

The dashboard is the landing page after login. It shows key metrics, recent activity, and quick-action buttons.

**API endpoints used:**
- `GET /institutions/me` → institution profile (check if setup complete)
- `GET /institutions/me/programs` → program count
- `GET /applications/programs/{programId}` → applications per program (aggregate)
- `GET /notifications` → recent activity feed
- `GET /messages/conversations` → unread message count

**Layout:**

```
┌─────────────────────────────────────────────────────────┐
│  Welcome back, {institution.name}         [Setup Guide] │
├─────────────┬──────────────┬──────────────┬─────────────┤
│  📋 Programs │ 📥 Applications │ 📨 Messages  │ 📅 Events  │
│     {count}  │    {count}      │  {unread}    │  {upcoming}│
├─────────────┴──────────────┴──────────────┴─────────────┤
│                                                         │
│  ┌─ Quick Actions ──────────────────────────────────┐   │
│  │ [+ New Program]  [View Pipeline]  [Review Queue] │   │
│  └──────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─ Recent Activity ───────────────────────────────┐    │
│  │ • New application from Jane D. for CS Masters    │    │
│  │ • Interview completed: John S. scored 4.2/5.0    │    │
│  │ • Message from student: "Thank you for..."       │    │
│  │ • Event RSVP: 12 new for Virtual Open House      │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  ┌─ Programs Overview ─────────────────────────────┐    │
│  │ Program Name     │ Apps │ Published │ Deadline   │    │
│  │ CS Masters       │  42  │ ✅        │ Mar 15     │    │
│  │ Data Science PhD │  18  │ ✅        │ Jan 30     │    │
│  │ MBA              │   0  │ Draft     │ —          │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

**Implementation:**

```typescript
// File: src/pages/institution/DashboardPage.tsx

import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { getInstitution, getInstitutionPrograms } from '../../api/institutions'
import { getConversations } from '../../api/messaging'
import { getNotifications } from '../../api/notifications'

export default function DashboardPage() {
  const navigate = useNavigate()

  // Fetch institution profile
  const { data: institution } = useQuery({
    queryKey: ['institution', 'me'],
    queryFn: getInstitution,
  })

  // Fetch programs
  const { data: programs } = useQuery({
    queryKey: ['institution', 'programs'],
    queryFn: getInstitutionPrograms,
  })

  // Fetch conversations for unread count
  const { data: conversations } = useQuery({
    queryKey: ['conversations'],
    queryFn: getConversations,
  })

  // Fetch recent notifications as activity feed
  const { data: notifications } = useQuery({
    queryKey: ['notifications', { limit: 10 }],
    queryFn: () => getNotifications({ limit: 10 }),
  })

  // If no institution profile exists yet, redirect to setup
  // Check: if institution query returns 404 or institution is null
  // Show a banner: "Complete your institution setup to get started" → link to /i/setup

  // KPI cards
  const kpis = [
    { label: 'Programs', value: programs?.length ?? 0, icon: '📋', onClick: () => navigate('/i/programs') },
    { label: 'Applications', value: '—', icon: '📥', onClick: () => navigate('/i/pipeline') },
    { label: 'Unread Messages', value: conversations?.filter(c => c.unread_count > 0).length ?? 0, icon: '📨', onClick: () => navigate('/i/messages') },
    { label: 'Upcoming Events', value: '—', icon: '📅', onClick: () => navigate('/i/events') },
  ]

  // Render:
  // 1. Welcome header with institution name
  // 2. Setup incomplete banner (if institution is null) with CTA to /i/setup
  // 3. Grid of 4 KPI cards (clickable, navigate to relevant page)
  // 4. Quick Actions row: 3 buttons → /i/programs/new, /i/pipeline, /i/reviews
  // 5. Recent Activity list from notifications (show last 10, each with icon + text + timestamp)
  // 6. Programs Overview table: name, application count, published status, deadline
  //    - Each row clickable → /i/programs/{id}/edit
  //    - If no programs: EmptyState with "Create your first program" CTA
}
```

---

## 5. Setup Page (First-Run Wizard)

### `src/pages/institution/SetupPage.tsx`

A multi-step wizard that guides institutions through initial setup. Shows only when institution profile doesn't exist yet (or can be revisited from settings).

**API endpoints used:**
- `POST /institutions/me` → create institution profile
- `POST /institutions/me/programs` → create first program
- `POST /reviews/rubrics` → create initial rubric

**Steps:**

```
Step 1: Institution Profile
  - Name* (text)
  - Type* (select: university, college, technical_institute, community_college)
  - Country* (text)
  - Region (text)
  - City (text)
  - Website URL (text)
  - Description (textarea)
  - Logo URL (text — future: file upload)

Step 2: First Program
  - Program name* (text)
  - Degree type* (select: bachelors, masters, phd, certificate, diploma)
  - Department (text)
  - Duration (number, months)
  - Tuition (number, USD)
  - Application deadline (date picker)
  - Program start date (date picker)
  - Description (textarea)
  - Requirements (JSON or structured key-value)

Step 3: Review Rubric (Optional)
  - Rubric name (text, e.g. "Default Admissions Rubric")
  - Add criteria: name, weight (0-100), description
  - Must sum to 100%
  - Can skip this step

Step 4: Done!
  - Summary of what was created
  - CTA: "Go to Dashboard" or "Add Another Program"
```

**Implementation:**

```typescript
// File: src/pages/institution/SetupPage.tsx

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { createInstitution } from '../../api/institutions'
import { createProgram } from '../../api/institutions'
import { createRubric } from '../../api/reviews'

// Step indicator at top: circles with lines connecting them
// Step 1/2/3/4 with labels below each
// Active step = indigo filled, completed = green check, upcoming = gray outline

// Each step is a separate form rendered conditionally based on currentStep state
// Use react-hook-form per step with zod validation

// Step 1 schema:
const institutionSchema = z.object({
  name: z.string().min(1, 'Institution name is required').max(255),
  type: z.enum(['university', 'college', 'technical_institute', 'community_college']),
  country: z.string().min(1, 'Country is required').max(100),
  region: z.string().optional(),
  city: z.string().optional(),
  website_url: z.string().url().optional().or(z.literal('')),
  description_text: z.string().optional(),
  logo_url: z.string().optional(),
})

// Step 2 schema:
const programSchema = z.object({
  program_name: z.string().min(1).max(255),
  degree_type: z.enum(['bachelors', 'masters', 'phd', 'certificate', 'diploma']),
  department: z.string().optional(),
  duration_months: z.number().int().min(1).max(120).optional(),
  tuition: z.number().int().min(0).optional(),
  application_deadline: z.string().optional(),
  program_start_date: z.string().optional(),
  description_text: z.string().optional(),
})

// Step 3: rubric form with dynamic criteria list
// criteria: [{ name: string, weight: number, description: string }]
// "Add criterion" button appends to array
// Validate: all weights sum to 100

// Navigation buttons at bottom: "Back" (not on step 1) | "Next" / "Skip" / "Finish"
// After step 1 submit → POST /institutions/me → store response
// After step 2 submit → POST /institutions/me/programs → store program id for rubric
// After step 3 submit → POST /reviews/rubrics with program_id from step 2
// Step 4 → success screen → navigate to /i/dashboard
```

---

## 6. Programs Page

### `src/pages/institution/ProgramsPage.tsx`

Lists all programs for this institution with actions to create, edit, publish/unpublish, and delete.

**API endpoints used:**
- `GET /institutions/me/programs` → list
- `POST /institutions/me/programs/{id}/publish` → publish
- `POST /institutions/me/programs/{id}/unpublish` → unpublish
- `DELETE /institutions/me/programs/{id}` → delete

**Layout:**

```
┌────────────────────────────────────────────────────────────┐
│  Programs                                  [+ New Program] │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌────────────────────────────────────────────────────────┐│
│  │ Program Name      │ Degree │ Status    │ Deadline │ ⋯  ││
│  ├───────────────────┼────────┼───────────┼──────────┼────┤│
│  │ CS Masters        │ M.S.   │ Published │ Mar 15   │ ⋮  ││
│  │ Data Science PhD  │ Ph.D.  │ Published │ Jan 30   │ ⋮  ││
│  │ MBA               │ M.B.A. │ Draft     │ —        │ ⋮  ││
│  └────────────────────────────────────────────────────────┘│
│                                                            │
│  Showing 3 programs                                        │
└────────────────────────────────────────────────────────────┘
```

**Implementation:**

```typescript
// File: src/pages/institution/ProgramsPage.tsx

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { getInstitutionPrograms, publishProgram, unpublishProgram, deleteProgram } from '../../api/institutions'
import { Program } from '../../types'

export default function ProgramsPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data: programs, isLoading } = useQuery({
    queryKey: ['institution', 'programs'],
    queryFn: getInstitutionPrograms,
  })

  const publishMut = useMutation({
    mutationFn: publishProgram,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['institution', 'programs'] }),
  })

  const unpublishMut = useMutation({
    mutationFn: unpublishProgram,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['institution', 'programs'] }),
  })

  const deleteMut = useMutation({
    mutationFn: deleteProgram,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['institution', 'programs'] }),
  })

  // Render:
  // 1. Page header: "Programs" + "New Program" button → /i/programs/new
  // 2. If loading: skeleton rows
  // 3. If no programs: EmptyState "No programs yet" with "Create Program" CTA
  // 4. Table with columns:
  //    - Program Name (clickable → /i/programs/{id}/edit)
  //    - Degree Type (badge)
  //    - Status: Published (green badge) or Draft (gray badge)
  //    - Application Deadline (formatted date or "—")
  //    - Tuition (formatted currency or "—")
  //    - Actions menu (⋮ dropdown):
  //      - Edit → /i/programs/{id}/edit
  //      - Publish / Unpublish (toggle)
  //      - Delete (with confirmation modal: "Delete {name}? This cannot be undone.")
  // 5. Row click → /i/programs/{id}/edit
}
```

---

## 7. Program Editor Page

### `src/pages/institution/ProgramEditorPage.tsx`

Create new or edit existing program. Uses `useParams()` to determine mode: if `:id` is present → edit mode, otherwise → create mode.

**API endpoints used:**
- `GET /institutions/me/programs/{id}` → load for editing
- `POST /institutions/me/programs` → create
- `PUT /institutions/me/programs/{id}` → update
- `POST /institutions/me/programs/{id}/publish` → publish after save

**Form fields (single page, scrollable sections):**

```
┌─ Program Details ────────────────────────────────┐
│ Program Name*        [________________________]  │
│ Degree Type*         [Select: bachelors ▾     ]  │
│ Department           [________________________]  │
│ Duration (months)    [____]                      │
│ Tuition (USD)        [________]                  │
│ Acceptance Rate      [____] (0.00 - 1.00)        │
└──────────────────────────────────────────────────┘

┌─ Dates ──────────────────────────────────────────┐
│ Application Deadline [📅 ____-____-____]         │
│ Program Start Date   [📅 ____-____-____]         │
└──────────────────────────────────────────────────┘

┌─ Description ────────────────────────────────────┐
│ [                                                ]│
│ [     Textarea, supports markdown preview        ]│
│ [                                                ]│
└──────────────────────────────────────────────────┘

┌─ Highlights ─────────────────────────────────────┐
│ • Top-ranked program in the region     [✕]       │
│ • Industry partnerships with Fortune 500 [✕]     │
│ [+ Add highlight]                                │
└──────────────────────────────────────────────────┘

┌─ Requirements (JSON key-value) ──────────────────┐
│ GPA Minimum:     3.5                       [✕]   │
│ GRE Required:    Yes                       [✕]   │
│ [+ Add requirement]                              │
└──────────────────────────────────────────────────┘

┌─ Faculty Contacts ───────────────────────────────┐
│ Name: Dr. Smith   Email: smith@uni.edu     [✕]   │
│ [+ Add faculty contact]                          │
└──────────────────────────────────────────────────┘

           [Cancel]  [Save as Draft]  [Save & Publish]
```

**Implementation:**

```typescript
// File: src/pages/institution/ProgramEditorPage.tsx

import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm, useFieldArray } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import {
  getInstitutionProgram, createProgram, updateProgram, publishProgram
} from '../../api/institutions'

const programSchema = z.object({
  program_name: z.string().min(1, 'Program name is required').max(255),
  degree_type: z.enum(['bachelors', 'masters', 'phd', 'certificate', 'diploma']),
  department: z.string().max(255).optional().nullable(),
  duration_months: z.number().int().min(1).max(120).optional().nullable(),
  tuition: z.number().int().min(0).optional().nullable(),
  acceptance_rate: z.number().min(0).max(1).optional().nullable(),
  application_deadline: z.string().optional().nullable(),   // ISO date string
  program_start_date: z.string().optional().nullable(),
  description_text: z.string().optional().nullable(),
  current_preferences_text: z.string().optional().nullable(),
  page_header_image_url: z.string().url().optional().or(z.literal('')).nullable(),
  highlights: z.array(z.string()).optional().nullable(),
  requirements: z.record(z.string(), z.any()).optional().nullable(),
  faculty_contacts: z.array(z.object({
    name: z.string(),
    email: z.string().email().optional(),
    role: z.string().optional(),
  })).optional().nullable(),
})

export default function ProgramEditorPage() {
  const { id } = useParams<{ id: string }>()
  const isEdit = Boolean(id)
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  // Load existing program in edit mode
  const { data: existingProgram } = useQuery({
    queryKey: ['institution', 'program', id],
    queryFn: () => getInstitutionProgram(id!),
    enabled: isEdit,
  })

  // Form with react-hook-form
  // Default values populated from existingProgram when in edit mode
  // useFieldArray for highlights and faculty_contacts

  // Mutations:
  // createMut → POST /institutions/me/programs → on success: navigate to /i/programs
  // updateMut → PUT /institutions/me/programs/{id} → on success: invalidate and stay
  // publishMut → POST /institutions/me/programs/{id}/publish

  // "Save as Draft" → create/update without publishing
  // "Save & Publish" → create/update, then call publish endpoint
  // "Cancel" → navigate back to /i/programs

  // Highlights: dynamic list with "Add highlight" button, each item has text input + remove button
  // Requirements: dynamic key-value pairs with "Add requirement" button
  // Faculty contacts: dynamic list with name/email/role fields + remove button
}
```

---

## 8. Pipeline Page (THE Primary View)

### `src/pages/institution/PipelinePage.tsx`

**This is the MOST IMPORTANT page for the institution side.** It's a Kanban board showing all applications flowing through the admissions pipeline. Uses `@dnd-kit` for drag-and-drop between columns.

**API endpoints used:**
- `GET /reviews/pipeline/{programId}` → pipeline data (applications grouped by status)
- `GET /institutions/me/programs` → program selector dropdown
- `GET /applications/programs/{programId}` → detailed application list (fallback/supplementary)
- `POST /applications/review/{appId}/decision` → move to decision (on drop into Decision column)

**Pipeline columns (left → right):**

| Column | Status | Color | Description |
|--------|--------|-------|-------------|
| Applied | `submitted` | Blue | New applications |
| Under Review | `under_review` | Yellow | Being evaluated |
| Interview | `interview` | Purple | Interview stage |
| Decision | `decision_made` | Orange | Awaiting final call |
| Enrolled | `enrolled` | Green | Admitted + accepted |

**Layout:**

```
┌───────────────────────────────────────────────────────────────────────┐
│  Pipeline                    Program: [All Programs ▾] [🔍 Filter]   │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─ Applied ──┐  ┌─ Review ───┐  ┌─ Interview ┐  ┌─ Decision ─┐  ┌─ Enrolled ─┐
│  │    (12)     │  │    (8)     │  │    (3)     │  │    (5)     │  │    (2)     │
│  ├────────────┤  ├────────────┤  ├────────────┤  ├────────────┤  ├────────────┤
│  │┌──────────┐│  │┌──────────┐│  │┌──────────┐│  │┌──────────┐│  │┌──────────┐│
│  ││ Jane D.  ││  ││ Mike R.  ││  ││ Sara L.  ││  ││ Tom K.   ││  ││ Amy C.   ││
│  ││ CS M.S.  ││  ││ CS M.S.  ││  ││ DS Ph.D. ││  ││ CS M.S.  ││  ││ MBA      ││
│  ││ Score:87%││  ││ Score:92%││  ││ Score:88%││  ││ Admitted  ││  ││ Enrolled ││
│  ││ 2d ago   ││  ││ 5d ago   ││  ││ 1w ago   ││  ││ 3d ago   ││  ││ Today    ││
│  │└──────────┘│  │└──────────┘│  │└──────────┘│  │└──────────┘│  │└──────────┘│
│  │┌──────────┐│  │┌──────────┐│  │            │  │            │  │            │
│  ││ Alex T.  ││  ││ Lisa M.  ││  │            │  │            │  │            │
│  ││ DS Ph.D. ││  ││ MBA      ││  │            │  │            │  │            │
│  ││ Score:79%││  ││ Score:85%││  │            │  │            │  │            │
│  ││ 1d ago   ││  ││ 3d ago   ││  │            │  │            │  │            │
│  │└──────────┘│  │└──────────┘│  │            │  │            │  │            │
│  │   ...      │  │   ...      │  │            │  │            │  │            │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘  └────────────┘
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

**Implementation:**

```typescript
// File: src/pages/institution/PipelinePage.tsx

import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import {
  DndContext, closestCorners, DragEndEvent, DragOverlay, DragStartEvent,
  PointerSensor, useSensor, useSensors,
} from '@dnd-kit/core'
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable'
import { getInstitutionPrograms } from '../../api/institutions'
import { getPipeline } from '../../api/reviews'
import { getApplicationsByProgram, makeDecision } from '../../api/applications-admin'
import type { Application, Program } from '../../types'

// Column definitions
const PIPELINE_COLUMNS = [
  { id: 'submitted', label: 'Applied', color: 'blue' },
  { id: 'under_review', label: 'Under Review', color: 'yellow' },
  { id: 'interview', label: 'Interview', color: 'purple' },
  { id: 'decision_made', label: 'Decision', color: 'orange' },
  { id: 'enrolled', label: 'Enrolled', color: 'green' },
] as const

export default function PipelinePage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [selectedProgramId, setSelectedProgramId] = useState<string | 'all'>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [activeCard, setActiveCard] = useState<Application | null>(null)

  // Fetch programs for the filter dropdown
  const { data: programs } = useQuery({
    queryKey: ['institution', 'programs'],
    queryFn: getInstitutionPrograms,
  })

  // Fetch applications for selected program (or all programs)
  // If selectedProgramId === 'all', fetch for each program and merge
  // If a specific program, use GET /applications/programs/{programId}
  const { data: applications, isLoading } = useQuery({
    queryKey: ['pipeline', 'applications', selectedProgramId],
    queryFn: () => {
      if (selectedProgramId !== 'all') {
        return getApplicationsByProgram(selectedProgramId)
      }
      // For "all", fetch each program's applications and flatten
      // This is a simplification — in production you'd have a dedicated endpoint
      return Promise.all(
        (programs || []).map(p => getApplicationsByProgram(p.id))
      ).then(results => results.flat())
    },
    enabled: selectedProgramId === 'all' ? !!programs : true,
  })

  // Group applications into columns by status
  const columns = useMemo(() => {
    if (!applications) return {}
    const grouped: Record<string, Application[]> = {}
    PIPELINE_COLUMNS.forEach(col => { grouped[col.id] = [] })
    applications.forEach(app => {
      const status = app.status || 'submitted'
      if (grouped[status]) grouped[status].push(app)
    })
    // Filter by search query (match student name or program name)
    if (searchQuery) {
      Object.keys(grouped).forEach(key => {
        grouped[key] = grouped[key].filter(app =>
          // Placeholder: filter by application fields containing searchQuery
          JSON.stringify(app).toLowerCase().includes(searchQuery.toLowerCase())
        )
      })
    }
    return grouped
  }, [applications, searchQuery])

  // Drag-and-drop setup
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } })
  )

  // Decision mutation (when card is dropped into "Decision" or "Enrolled" column)
  const decisionMut = useMutation({
    mutationFn: ({ appId, decision }: { appId: string; decision: string }) =>
      makeDecision(appId, { decision, decision_notes: null }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['pipeline'] }),
  })

  function handleDragStart(event: DragStartEvent) {
    const app = applications?.find(a => a.id === event.active.id)
    setActiveCard(app || null)
  }

  function handleDragEnd(event: DragEndEvent) {
    setActiveCard(null)
    const { active, over } = event
    if (!over) return

    const appId = active.id as string
    const targetColumn = over.id as string

    // Find current status of this application
    const app = applications?.find(a => a.id === appId)
    if (!app || app.status === targetColumn) return

    // When dropping into decision_made, trigger the decision endpoint
    // For other columns, this would need a status update endpoint
    // For MVP, only decision_made column triggers an API call
    if (targetColumn === 'decision_made') {
      // Open a modal to select: admitted / rejected / waitlisted / deferred
      // For now, we can use a simple prompt or modal
      // decisionMut.mutate({ appId, decision: 'admitted' })
    }

    // Optimistically move the card to the new column in the UI
    // (in production, you'd update the application status via API)
  }

  // Render:
  // 1. Page header: "Pipeline"
  // 2. Controls row:
  //    - Program filter dropdown: "All Programs" + each program name
  //    - Search input for filtering cards
  //    - Total count: "{n} applications"
  // 3. DndContext wrapping the columns
  // 4. Horizontal scroll container with 5 columns
  // 5. Each column:
  //    - Header: label + count badge (colored)
  //    - Droppable area (SortableContext)
  //    - List of PipelineCard components
  // 6. DragOverlay showing the card being dragged
  // 7. Click on any card → navigate('/i/pipeline/' + app.student_id) or open detail drawer

  // PipelineCard component (inline or separate file):
  // Shows: student name (from app or a lookup), program name,
  //        match score badge, submission date (relative: "2d ago"),
  //        status sub-label if in decision column (admitted/rejected/etc.)
  // Card is styled with left border color matching column color
}
```

### `src/components/shared/PipelineCard.tsx`

```typescript
// Draggable card for the Kanban board

import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { Application } from '../../types'
import { formatDistanceToNow } from 'date-fns'

interface Props {
  application: Application
  onClick: () => void
}

export default function PipelineCard({ application, onClick }: Props) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: application.id,
  })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  }

  // Render:
  // <div ref={setNodeRef} style={style} {...attributes} {...listeners} onClick={onClick}>
  //   Compact card:
  //   - Student ID or name (top, bold, text-sm)
  //   - Program name (text-xs, gray)
  //   - Match score: colored circle with percentage
  //   - Submitted: relative date (text-xs, gray)
  //   - If decision exists: StatusBadge showing admitted/rejected/etc.
  //   Left border: 3px solid, color based on column
  //   Background: white, rounded-lg, shadow-sm, hover:shadow-md transition
  // </div>
}
```

### Column Droppable Component

```typescript
// src/components/shared/PipelineColumn.tsx

import { useDroppable } from '@dnd-kit/core'
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable'
import PipelineCard from './PipelineCard'
import { Application } from '../../types'

interface Props {
  id: string
  label: string
  color: string
  applications: Application[]
  onCardClick: (appId: string) => void
}

export default function PipelineColumn({ id, label, color, applications, onCardClick }: Props) {
  const { setNodeRef, isOver } = useDroppable({ id })

  const colorMap: Record<string, string> = {
    blue: 'bg-blue-50 border-blue-200 text-blue-700',
    yellow: 'bg-yellow-50 border-yellow-200 text-yellow-700',
    purple: 'bg-purple-50 border-purple-200 text-purple-700',
    orange: 'bg-orange-50 border-orange-200 text-orange-700',
    green: 'bg-green-50 border-green-200 text-green-700',
  }

  // Render:
  // <div className="flex-shrink-0 w-72">
  //   Header: label + count badge (e.g., "Applied (12)")
  //   Badge uses colorMap[color] for background/text
  //
  //   <div ref={setNodeRef} className={`min-h-[200px] p-2 rounded-lg ${isOver ? 'bg-gray-100' : 'bg-gray-50'}`}>
  //     <SortableContext items={applications.map(a => a.id)} strategy={verticalListSortingStrategy}>
  //       {applications.map(app => (
  //         <PipelineCard key={app.id} application={app} onClick={() => onCardClick(app.id)} />
  //       ))}
  //     </SortableContext>
  //     {applications.length === 0 && <p className="text-xs text-gray-400 text-center py-8">No applications</p>}
  //   </div>
  // </div>
}
```

---

## 9. Student Detail Page (Institution View)

### `src/pages/institution/StudentDetailPage.tsx`

When an institution admin clicks on a pipeline card or navigates to `/i/pipeline/:studentId`, they see the full student application detail from the institution's perspective.

**API endpoints used:**
- `GET /applications/review/{applicationId}` → application detail with decision info
- `GET /reviews/applications/{applicationId}/scores` → all review scores
- `GET /reviews/applications/{applicationId}/ai-summary` → AI-generated summary
- `GET /interviews/application/{applicationId}` → interviews for this application
- `POST /applications/review/{applicationId}/decision` → make admission decision
- `POST /applications/review/{applicationId}/offer` → create offer letter
- `POST /reviews/applications/{applicationId}/assign` → assign reviewer
- `POST /reviews/applications/{applicationId}/score` → submit score

**Layout:**

```
┌─────────────────────────────────────────────────────────────────────┐
│  ← Back to Pipeline    Jane Doe — CS Masters Application           │
├──────────────────────────┬──────────────────────────────────────────┤
│                          │                                          │
│  ┌─ Student Snapshot ──┐ │  ┌─ Tabs ──────────────────────────────┐ │
│  │ Jane Doe            │ │  │ [Overview] [Scores] [Interview] [AI]│ │
│  │ jane@email.com      │ │  ├─────────────────────────────────────┤ │
│  │                     │ │  │                                     │ │
│  │ Match Score: 87%    │ │  │ Overview Tab:                       │ │
│  │ Tier: Match         │ │  │  Status: Under Review               │ │
│  │                     │ │  │  Submitted: Jan 15, 2026            │ │
│  │ GPA: 3.8/4.0       │ │  │  Completeness: 100%                 │ │
│  │ GRE: 328            │ │  │  Match Reasoning: "Strong fit..."   │ │
│  │ TOEFL: 110          │ │  │                                     │ │
│  │                     │ │  │ Scores Tab:                         │ │
│  │ Applied: Jan 15     │ │  │  Reviewer 1: 4.2/5.0               │ │
│  │ Status: Under Review│ │  │  Reviewer 2: 3.8/5.0               │ │
│  └─────────────────────┘ │  │  Average: 4.0/5.0                   │ │
│                          │  │                                     │ │
│  ┌─ Actions ───────────┐ │  │ Interview Tab:                      │ │
│  │ [Assign Reviewer]   │ │  │  (list of interviews + scores)      │ │
│  │ [Score Application] │ │  │                                     │ │
│  │ [Schedule Interview]│ │  │ AI Tab:                              │ │
│  │ [Make Decision ▾]   │ │  │  AI Summary with strengths/concerns │ │
│  │ [Create Offer]      │ │  │                                     │ │
│  └─────────────────────┘ │  └─────────────────────────────────────┘ │
└──────────────────────────┴──────────────────────────────────────────┘
```

**Implementation:**

```typescript
// File: src/pages/institution/StudentDetailPage.tsx

import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  reviewApplication, makeDecision, createOffer, getApplicationsByProgram
} from '../../api/applications-admin'
import { getScores, getAISummary, assignReviewer, scoreApplication } from '../../api/reviews'
import { getInterviewsByApplication } from '../../api/interviews-admin'

export default function StudentDetailPage() {
  const { studentId } = useParams<{ studentId: string }>()
  // Note: studentId here is actually the applicationId from the pipeline
  // In a real app, you might use applicationId in the URL instead
  const [activeTab, setActiveTab] = useState<'overview' | 'scores' | 'interview' | 'ai'>('overview')
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  // Fetch application detail
  const { data: application } = useQuery({
    queryKey: ['application', 'review', studentId],
    queryFn: () => reviewApplication(studentId!),
  })

  // Fetch scores
  const { data: scores } = useQuery({
    queryKey: ['application', 'scores', studentId],
    queryFn: () => getScores(studentId!),
    enabled: activeTab === 'scores',
  })

  // Fetch AI summary
  const { data: aiSummary } = useQuery({
    queryKey: ['application', 'ai-summary', studentId],
    queryFn: () => getAISummary(studentId!),
    enabled: activeTab === 'ai',
  })

  // Fetch interviews
  const { data: interviews } = useQuery({
    queryKey: ['application', 'interviews', studentId],
    queryFn: () => getInterviewsByApplication(studentId!),
    enabled: activeTab === 'interview',
  })

  // Mutations
  const decisionMut = useMutation({
    mutationFn: ({ decision, notes }: { decision: string; notes: string | null }) =>
      makeDecision(studentId!, { decision, decision_notes: notes }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['application', 'review', studentId] })
      queryClient.invalidateQueries({ queryKey: ['pipeline'] })
    },
  })

  const offerMut = useMutation({
    mutationFn: (data: any) => createOffer(studentId!, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['application', 'review', studentId] }),
  })

  const assignMut = useMutation({
    mutationFn: () => assignReviewer(studentId!),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['application', 'scores', studentId] }),
  })

  // Render:
  // Left column (fixed width ~280px):
  //   Student snapshot card (name, email, key stats)
  //   Match score circle (large, colored by tier)
  //   Key academic metrics (GPA, test scores) — pulled from application detail
  //   Application metadata (submitted date, status badge, completeness)
  //   Actions panel:
  //     - "Assign Reviewer" button → calls assignReviewer
  //     - "Score Application" button → opens scoring modal (form with rubric criteria)
  //     - "Schedule Interview" button → opens interview scheduling modal
  //     - "Make Decision" dropdown: Admit / Reject / Waitlist / Defer → calls makeDecision
  //     - "Create Offer" button → opens offer modal (only if decision = admitted)
  //
  // Right column (flex-1):
  //   Tab bar: Overview | Scores | Interview | AI Summary
  //   Tab content:
  //
  //   Overview:
  //     - Application status timeline
  //     - Match reasoning text
  //     - Completeness status + missing items
  //     - Decision notes (if decision made)
  //
  //   Scores:
  //     - Table of all review scores
  //     - Each row: reviewer, rubric name, criterion scores, total weighted score, notes
  //     - Average across all reviewers
  //     - "Score Application" button if no scores yet
  //
  //   Interview:
  //     - List of interviews with status badges
  //     - Each: type, proposed times, confirmed time, interviewer, score (if completed)
  //     - "Schedule Interview" button
  //
  //   AI Summary:
  //     - AI-generated text summary
  //     - Strengths (green bullet list)
  //     - Concerns (red bullet list)
  //     - Recommended score range

  // === Decision Modal ===
  // When "Make Decision" is clicked, show a modal:
  //   - Radio buttons: Admitted / Rejected / Waitlisted / Deferred
  //   - Decision notes textarea (optional)
  //   - Confirm button → calls POST /applications/review/{id}/decision

  // === Offer Modal ===
  // When "Create Offer" is clicked (only if decision = admitted):
  //   - Offer type: full_admission / conditional / waitlist_offer
  //   - Tuition amount (number)
  //   - Scholarship amount (number)
  //   - Financial package total (number)
  //   - Conditions (textarea or key-value)
  //   - Response deadline (date picker)
  //   - Submit → POST /applications/review/{id}/offer

  // === Scoring Modal ===
  // When "Score Application" is clicked:
  //   - Select rubric from dropdown (fetch rubrics via GET /reviews/rubrics)
  //   - For each criterion in the rubric: slider or number input (scale_min to scale_max)
  //   - Reviewer notes textarea
  //   - Submit → POST /reviews/applications/{id}/score
}
```

---

## 10. Review Queue Page

### `src/pages/institution/ReviewQueuePage.tsx`

Shows all applications that need review, sorted by priority. Provides a focused workflow for reviewing applications one by one.

**API endpoints used:**
- `GET /institutions/me/programs` → program filter
- `GET /applications/programs/{programId}` → applications for selected program
- `GET /reviews/rubrics` → available rubrics
- `POST /reviews/applications/{appId}/score` → submit score
- `GET /reviews/applications/{appId}/ai-summary` → AI assistance

**Layout:**

```
┌────────────────────────────────────────────────────────────┐
│  Review Queue                   Program: [All ▾]  [📊 AI] │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌─ Pending Review (8) ───────────────────────────────────┐│
│  │ ☐ Jane Doe    │ CS Masters  │ Score: 87% │ Jan 15 │ → ││
│  │ ☐ Alex Torres │ DS PhD      │ Score: 79% │ Jan 12 │ → ││
│  │ ☐ Mike Ross   │ CS Masters  │ Score: 92% │ Jan 10 │ → ││
│  └────────────────────────────────────────────────────────┘│
│                                                            │
│  ┌─ Reviewed (5) ─────────────────────────────────────────┐│
│  │ ✅ Sara Lee   │ DS PhD     │ Avg: 4.2  │ Jan 8  │ → ││
│  │ ✅ Tom Kim    │ CS Masters │ Avg: 3.8  │ Jan 5  │ → ││
│  └────────────────────────────────────────────────────────┘│
└────────────────────────────────────────────────────────────┘
```

**Implementation:**

```typescript
// File: src/pages/institution/ReviewQueuePage.tsx

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { getInstitutionPrograms } from '../../api/institutions'
import { getApplicationsByProgram } from '../../api/applications-admin'
import { getRubrics } from '../../api/reviews'

export default function ReviewQueuePage() {
  const [selectedProgram, setSelectedProgram] = useState<string>('')
  const navigate = useNavigate()

  const { data: programs } = useQuery({
    queryKey: ['institution', 'programs'],
    queryFn: getInstitutionPrograms,
  })

  // Auto-select first program if none selected
  // useEffect → if programs loaded and no selection → setSelectedProgram(programs[0].id)

  const { data: applications } = useQuery({
    queryKey: ['applications', 'program', selectedProgram],
    queryFn: () => getApplicationsByProgram(selectedProgram),
    enabled: !!selectedProgram,
  })

  // Split applications into two groups:
  // 1. "Pending Review" — status = submitted or under_review, no scores yet
  // 2. "Reviewed" — has at least one score
  // Sort pending by match_score descending (highest priority first)

  // Render:
  // 1. Header with program dropdown filter
  // 2. "Pending Review" section:
  //    - List of application rows
  //    - Each row: checkbox (for bulk actions), student name, program, match score, date
  //    - Click → navigate to /i/pipeline/{applicationId}
  //    - Inline "Quick Score" button that opens scoring modal
  // 3. "Reviewed" section:
  //    - Same row format but with average score shown
  //    - Green checkmark instead of empty checkbox
  // 4. Empty state if no applications for selected program
  // 5. Bulk actions toolbar (when checkboxes selected):
  //    - "Assign Reviewer" — assign to selected applications
  //    - "Request AI Summary" — batch AI summaries
}
```

---

## 11. Interviews Page

### `src/pages/institution/InterviewsPage.tsx`

Manage all interviews across programs. Schedule new interviews, view upcoming/past interviews, and enter scores.

**API endpoints used:**
- `POST /interviews` → propose interview
- `GET /interviews/application/{appId}` → interviews per application
- `POST /interviews/{id}/complete` → mark completed
- `POST /interviews/{id}/score` → score interview

**Layout:**

```
┌─────────────────────────────────────────────────────────────────┐
│  Interviews                      [+ Schedule Interview]         │
├─────────────────────────────────────────────────────────────────┤
│  [Upcoming]  [Completed]  [All]                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Student     │ Program    │ Type   │ Time          │ Status  ││
│  ├─────────────┼────────────┼────────┼───────────────┼─────────┤│
│  │ Jane Doe    │ CS Masters │ Video  │ Mar 5, 2pm    │ Confirmed│
│  │ Alex Torres │ DS PhD     │ Phone  │ Mar 7, 10am   │ Invited ││
│  │ Sara Lee    │ DS PhD     │ Video  │ Feb 28, 3pm   │ Completed│
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

**Implementation:**

```typescript
// File: src/pages/institution/InterviewsPage.tsx

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  proposeInterview, completeInterview, scoreInterview
} from '../../api/interviews-admin'
import { getInstitutionPrograms } from '../../api/institutions'
import { getApplicationsByProgram } from '../../api/applications-admin'

export default function InterviewsPage() {
  const [filter, setFilter] = useState<'upcoming' | 'completed' | 'all'>('upcoming')
  const [showScheduleModal, setShowScheduleModal] = useState(false)
  const queryClient = useQueryClient()

  // Since there's no "list all interviews for institution" endpoint,
  // we need to fetch applications and then interviews per application.
  // Strategy: fetch all programs → all applications → for each, fetch interviews
  // This is expensive — cache aggressively, or create a combined query

  const { data: programs } = useQuery({
    queryKey: ['institution', 'programs'],
    queryFn: getInstitutionPrograms,
  })

  // For MVP: fetch interviews for each program's applications
  // In production, you'd want a dedicated "list all interviews" endpoint

  // Complete mutation
  const completeMut = useMutation({
    mutationFn: completeInterview,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['interviews'] }),
  })

  // Score mutation
  const scoreMut = useMutation({
    mutationFn: ({ interviewId, data }: { interviewId: string; data: any }) =>
      scoreInterview(interviewId, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['interviews'] }),
  })

  // Render:
  // 1. Header: "Interviews" + "Schedule Interview" button
  // 2. Tab bar: Upcoming | Completed | All
  // 3. Table with columns: Student, Program, Type, Date/Time, Status, Actions
  //    - Upcoming: interviews with status = invited/scheduling/confirmed, sorted by date
  //    - Completed: interviews with status = completed
  // 4. Actions per row:
  //    - If confirmed: "Mark Complete" button
  //    - If completed: "Score" button (opens scoring modal)
  //    - "View Application" → /i/pipeline/{applicationId}
  // 5. Empty state per tab if no interviews

  // === Schedule Interview Modal ===
  // Fields:
  //   - Application (searchable select — list applications that are in interview stage)
  //   - Interview type (select: video, in_person, phone, group)
  //   - Proposed times (array: add multiple datetime inputs)
  //   - Duration (number, minutes, default 30)
  //   - Location/Link (text)
  //   - Interviewer ID (for MVP: use current user's ID)
  // Submit → POST /interviews

  // === Score Interview Modal ===
  // Fields:
  //   - Select rubric (optional, from GET /reviews/rubrics)
  //   - Criterion scores (if rubric selected: one input per criterion; else: single overall score)
  //   - Total weighted score (auto-calculated or manual)
  //   - Interviewer notes (textarea)
  //   - Recommendation (select: strong_admit, admit, borderline, reject)
  // Submit → POST /interviews/{id}/score
}
```

---

## 12. Messaging Page (Institution)

### `src/pages/institution/MessagingPage.tsx`

Same messaging interface as the student side, but from the institution perspective. Reuses the same API endpoints.

**API endpoints used:**
- `GET /messages/conversations` → list conversations
- `GET /messages/conversations/{id}` → get messages
- `POST /messages/conversations` → start new conversation
- `POST /messages/conversations/{id}` → send message

**Layout:**

```
┌───────────────────┬──────────────────────────────────────────────┐
│  Conversations     │  Jane Doe — CS Masters                      │
│  🔍 Search...      │                                              │
│ ──────────────────│  ┌─────────────────────────────────────────┐ │
│ Jane Doe       2m  │  │ Student: Hi, I wanted to ask about...   │ │
│ "Thanks for the.." │  │                           Jan 15, 2:30pm│ │
│ ──────────────────│  │                                         │ │
│ Alex Torres    1d  │  │ You: Thank you for reaching out! The    │ │
│ "When will I..."   │  │ program requires...                     │ │
│ ──────────────────│  │                           Jan 15, 3:00pm│ │
│ Mike Ross      3d  │  │                                         │ │
│ "I submitted my."  │  │ Student: That makes sense. One more     │ │
│                    │  │ question...                              │ │
│                    │  │                           Jan 15, 3:15pm│ │
│                    │  └─────────────────────────────────────────┘ │
│                    │  ┌──────────────────────────────┬──────────┐ │
│                    │  │ Type your message...          │  Send ➤  │ │
│                    │  └──────────────────────────────┴──────────┘ │
└───────────────────┴──────────────────────────────────────────────┘
```

**Implementation:**

```typescript
// File: src/pages/institution/MessagingPage.tsx

// This page is structurally identical to the student MessagesPage from Part 1.
// Key differences:
// 1. Institution can START conversations (student side waits for institution to reach out)
// 2. "New Conversation" button that lets admin select a student to message
// 3. Messages show "You" for institution messages and student name for student messages
// 4. Uses same API endpoints (both sides share messaging endpoints)

import { useState, useEffect, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useParams, useNavigate } from 'react-router-dom'
import {
  getConversations, getMessages, sendMessage, createConversation
} from '../../api/messaging'
import { useAuthStore } from '../../stores/auth-store'

export default function MessagingPage() {
  const { convId } = useParams<{ convId: string }>()
  const [selectedConv, setSelectedConv] = useState<string | null>(convId || null)
  const [newMessage, setNewMessage] = useState('')
  const [showNewConvModal, setShowNewConvModal] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const user = useAuthStore(s => s.user)

  // Fetch conversations
  const { data: conversations } = useQuery({
    queryKey: ['conversations'],
    queryFn: getConversations,
    refetchInterval: 30000, // Poll every 30s
  })

  // Fetch messages for selected conversation
  const { data: messages } = useQuery({
    queryKey: ['messages', selectedConv],
    queryFn: () => getMessages(selectedConv!, { limit: 50 }),
    enabled: !!selectedConv,
    refetchInterval: 10000, // Poll every 10s when conversation is open
  })

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Send message mutation
  const sendMut = useMutation({
    mutationFn: (content: string) => sendMessage(selectedConv!, content),
    onSuccess: () => {
      setNewMessage('')
      queryClient.invalidateQueries({ queryKey: ['messages', selectedConv] })
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
    },
  })

  // Create conversation mutation
  const createConvMut = useMutation({
    mutationFn: (data: { student_id: string; institution_id: string; subject?: string; program_id?: string }) =>
      createConversation(data),
    onSuccess: (conv) => {
      setSelectedConv(conv.id)
      setShowNewConvModal(false)
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
    },
  })

  // Render:
  // Two-column layout (same as student MessagesPage from Part 1)
  // Left panel (w-80): conversation list with search, sorted by last_message_at
  // Right panel (flex-1): message thread with input
  //
  // Additional institution features:
  // - "New Conversation" button in left panel header
  // - New Conversation Modal:
  //   - Student search/select (would need a student lookup — for MVP, enter student_id manually)
  //   - Subject (optional)
  //   - Program (optional, select from institution's programs)
  //   - Initial message text
  //   - Submit → createConversation then sendMessage
}
```

---

## 13. Segments Page

### `src/pages/institution/SegmentsPage.tsx`

Manage target student segments for outreach campaigns. Segments define criteria for filtering/targeting students.

**API endpoints used:**
- `GET /institutions/me/segments` → list segments
- `POST /institutions/me/segments` → create segment
- `PUT /institutions/me/segments/{id}` → update segment
- `DELETE /institutions/me/segments/{id}` → delete segment

**Layout:**

```
┌────────────────────────────────────────────────────────────┐
│  Segments                               [+ New Segment]    │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ High GPA International Students              Active  │  │
│  │ Criteria: GPA ≥ 3.7, nationality ≠ US               │  │
│  │ Program: CS Masters    Created: Jan 10               │  │
│  │                              [Edit] [Deactivate] [✕] │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │ STEM Scholars                                Active  │  │
│  │ Criteria: field = STEM, test_score ≥ 320             │  │
│  │ Program: All           Created: Jan 8                │  │
│  │                              [Edit] [Deactivate] [✕] │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

**Implementation:**

```typescript
// File: src/pages/institution/SegmentsPage.tsx

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import {
  getSegments, createSegment, updateSegment, deleteSegment
} from '../../api/institutions'
import { getInstitutionPrograms } from '../../api/institutions'

const segmentSchema = z.object({
  segment_name: z.string().min(1, 'Segment name is required').max(255),
  program_id: z.string().uuid().optional().nullable(),
  criteria: z.record(z.string(), z.any()),  // JSON object
  is_active: z.boolean().default(true),
})

export default function SegmentsPage() {
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const queryClient = useQueryClient()

  const { data: segments, isLoading } = useQuery({
    queryKey: ['segments'],
    queryFn: getSegments,
  })

  const { data: programs } = useQuery({
    queryKey: ['institution', 'programs'],
    queryFn: getInstitutionPrograms,
  })

  // Create/update/delete mutations
  const createMut = useMutation({
    mutationFn: createSegment,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['segments'] })
      setShowForm(false)
    },
  })

  const updateMut = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => updateSegment(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['segments'] })
      setEditingId(null)
    },
  })

  const deleteMut = useMutation({
    mutationFn: deleteSegment,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['segments'] }),
  })

  // Render:
  // 1. Header: "Segments" + "New Segment" button
  // 2. Segment cards (stacked):
  //    - Segment name (bold) + Active/Inactive badge
  //    - Criteria displayed as human-readable conditions
  //    - Associated program name (or "All Programs")
  //    - Created date
  //    - Actions: Edit, Deactivate/Activate toggle, Delete (with confirm)
  // 3. When "New Segment" or "Edit" clicked → show form (inline or modal):
  //    - Segment name (text input)
  //    - Program (select from institution programs, or "All Programs")
  //    - Criteria builder:
  //      For MVP: JSON textarea where admin enters criteria object
  //      Future: visual criteria builder with field dropdowns + operators + values
  //      Example criteria: { "gpa_min": 3.5, "nationality": ["US", "CA"], "test_score_min": 320 }
  //    - Active toggle (checkbox)
  //    - Save / Cancel buttons
  // 4. Empty state: "No segments defined. Create a segment to target students."
}
```

---

## 14. Campaigns Page

### `src/pages/institution/CampaignsPage.tsx`

Campaigns are outreach efforts targeting student segments. **Note:** The backend doesn't have dedicated campaign endpoints yet — this page is a frontend placeholder that stores campaigns locally and will be wired up when the backend adds campaign management.

**For MVP:** This is a placeholder page with static UI showing the concept. The actual campaign execution (sending emails, tracking opens) requires backend work in a future phase.

**Layout:**

```
┌────────────────────────────────────────────────────────────┐
│  Campaigns                              [+ New Campaign]   │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Coming in Phase 2                                         │
│                                                            │
│  Campaigns will allow you to:                              │
│  • Target student segments with personalized outreach      │
│  • Schedule email campaigns                                │
│  • Track open rates and engagement                         │
│  • A/B test messaging                                      │
│                                                            │
│  For now, use the Messages page to reach out to students   │
│  individually.                                             │
│                                                            │
│                    [Go to Messages]                         │
└────────────────────────────────────────────────────────────┘
```

**Implementation:**

```typescript
// File: src/pages/institution/CampaignsPage.tsx

import { useNavigate } from 'react-router-dom'
import { Megaphone } from 'lucide-react'

export default function CampaignsPage() {
  const navigate = useNavigate()

  // Simple placeholder page
  // EmptyState component with:
  //   icon: Megaphone
  //   title: "Campaigns — Coming Soon"
  //   description: "Campaigns will allow you to target student segments with personalized
  //                outreach, schedule email campaigns, and track engagement."
  //   action: { label: "Go to Messages", onClick: () => navigate('/i/messages') }
  //
  // Below the empty state, a feature preview section showing what's planned:
  //   - Bullet points of planned features (styled as a muted info card)

  return (
    <div className="p-6">
      <h1 className="text-2xl font-semibold mb-6">Campaigns</h1>
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <Megaphone size={48} className="text-gray-300 mb-4" />
        <h2 className="text-lg font-medium text-gray-700">Coming in Phase 2</h2>
        <p className="text-sm text-gray-500 mt-2 max-w-md">
          Campaigns will let you target student segments with personalized outreach,
          schedule email campaigns, and track engagement metrics.
        </p>
        <button
          onClick={() => navigate('/i/messages')}
          className="mt-6 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm hover:bg-indigo-700"
        >
          Go to Messages
        </button>
      </div>
    </div>
  )
}
```

---

## 15. Events Page

### `src/pages/institution/EventsPage.tsx`

Manage institution events: create, list, view attendees.

**API endpoints used:**
- `GET /events/manage` → list institution's events (with optional status filter)
- `POST /events/manage` → create event
- `GET /events/manage/{eventId}/attendees` → list RSVPs/attendees

**Layout:**

```
┌────────────────────────────────────────────────────────────┐
│  Events                          Status: [All ▾]  [+ New] │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Virtual Open House                                   │  │
│  │ 📅 Mar 15, 2026 2:00 PM - 4:00 PM                   │  │
│  │ 📍 Zoom (link provided)                              │  │
│  │ 👥 42 RSVPs / 100 capacity                           │  │
│  │ Program: CS Masters                                  │  │
│  │                          [View Attendees] [Edit]     │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │ Campus Tour — Spring 2026                            │  │
│  │ 📅 Apr 1, 2026 10:00 AM - 12:00 PM                  │  │
│  │ 📍 Main Campus, Building A                           │  │
│  │ 👥 18 RSVPs / 30 capacity                            │  │
│  │ Program: All                                         │  │
│  │                          [View Attendees] [Edit]     │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

**Implementation:**

```typescript
// File: src/pages/institution/EventsPage.tsx

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import {
  getInstitutionEvents, createEvent, getEventAttendees
} from '../../api/events-admin'
import { getInstitutionPrograms } from '../../api/institutions'
import { format } from 'date-fns'

const eventSchema = z.object({
  event_name: z.string().min(1, 'Event name is required'),
  event_type: z.string().min(1),
  start_time: z.string().min(1, 'Start time is required'),  // ISO datetime
  end_time: z.string().min(1, 'End time is required'),
  description: z.string().optional(),
  location: z.string().optional(),
  capacity: z.number().int().min(1).optional(),
  program_id: z.string().uuid().optional().nullable(),
})

export default function EventsPage() {
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [viewingAttendees, setViewingAttendees] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<string>('')
  const queryClient = useQueryClient()

  const { data: events, isLoading } = useQuery({
    queryKey: ['institution', 'events', statusFilter],
    queryFn: () => getInstitutionEvents(statusFilter || undefined),
  })

  const { data: programs } = useQuery({
    queryKey: ['institution', 'programs'],
    queryFn: getInstitutionPrograms,
  })

  const { data: attendees } = useQuery({
    queryKey: ['event', 'attendees', viewingAttendees],
    queryFn: () => getEventAttendees(viewingAttendees!),
    enabled: !!viewingAttendees,
  })

  const createMut = useMutation({
    mutationFn: createEvent,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['institution', 'events'] })
      setShowCreateModal(false)
    },
  })

  // Render:
  // 1. Header: "Events" + status filter dropdown + "New Event" button
  //    Status filter options: All, Upcoming, Past, Cancelled
  // 2. Event cards (stacked):
  //    - Event name (bold, text-lg)
  //    - Date/time range (formatted nicely)
  //    - Location
  //    - RSVP count / capacity (with progress bar if capacity set)
  //    - Associated program name (or "All Programs")
  //    - Actions: "View Attendees" (opens side panel or modal), "Edit" (future)
  // 3. Empty state: "No events yet. Create your first event."

  // === Create Event Modal ===
  // Form fields:
  //   - Event name (text)
  //   - Event type (select: webinar, campus_visit, info_session, workshop)
  //   - Start date & time (datetime input)
  //   - End date & time (datetime input)
  //   - Description (textarea)
  //   - Location (text — URL for virtual, address for in-person)
  //   - Capacity (number, optional)
  //   - Program (select from programs, or "All Programs")
  // Submit → POST /events/manage

  // === Attendees Panel/Modal ===
  // Shows when "View Attendees" is clicked:
  //   - List of RSVPs with student_id, rsvp_status, registered_at
  //   - Total count
  //   - Export to CSV button (future)
}
```

---

## 16. Analytics Page

### `src/pages/institution/AnalyticsPage.tsx`

Dashboard showing admissions analytics. **For MVP:** Computed client-side from existing data (applications, reviews, events). No dedicated analytics backend endpoint yet.

**Data sources (all client-side aggregation):**
- Applications data from pipeline
- Review scores
- Event RSVPs
- Conversation counts

**Layout:**

```
┌────────────────────────────────────────────────────────────┐
│  Analytics                              Period: [This Year ▾]│
├──────────────┬──────────────┬──────────────┬──────────────┤
│ Applications │ Acceptance   │ Avg Score    │ Yield Rate   │
│     78       │ Rate: 34%    │    3.9/5.0   │    62%       │
├──────────────┴──────────────┴──────────────┴──────────────┤
│                                                            │
│  ┌─ Applications by Status ─────────────────────────────┐  │
│  │  [Horizontal bar chart]                              │  │
│  │  Submitted: ████████████████ 42                      │  │
│  │  Under Review: █████████ 18                          │  │
│  │  Interview: ████ 8                                   │  │
│  │  Decided: ██████ 10                                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
│  ┌─ Applications by Program ────────────────────────────┐  │
│  │  CS Masters:      ████████████████████ 42            │  │
│  │  Data Science PhD: ████████████ 24                   │  │
│  │  MBA:              ██████ 12                         │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
│  ┌─ Decision Breakdown ─────────────────────────────────┐  │
│  │  [Pie/donut chart: Admitted, Rejected, Waitlisted]   │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

**Implementation:**

```typescript
// File: src/pages/institution/AnalyticsPage.tsx

import { useQuery } from '@tanstack/react-query'
import { getInstitutionPrograms } from '../../api/institutions'
import { getApplicationsByProgram } from '../../api/applications-admin'

export default function AnalyticsPage() {
  // Fetch all programs
  const { data: programs } = useQuery({
    queryKey: ['institution', 'programs'],
    queryFn: getInstitutionPrograms,
  })

  // Fetch all applications across programs
  // Aggregate data client-side for charts

  // KPI cards:
  //   - Total Applications (count all apps)
  //   - Acceptance Rate (admitted / total decided)
  //   - Average Score (mean of all total_weighted_scores)
  //   - Yield Rate (enrolled / admitted)

  // Charts (implement as simple CSS bar charts — no charting library needed for MVP):
  //   1. Applications by Status: horizontal bars with counts
  //   2. Applications by Program: horizontal bars with counts
  //   3. Decision Breakdown: simple colored segments or list

  // Each bar chart:
  //   <div className="flex items-center gap-3 mb-2">
  //     <span className="w-32 text-sm text-right">{label}</span>
  //     <div className="flex-1 bg-gray-100 rounded-full h-4">
  //       <div className="bg-indigo-500 rounded-full h-4" style={{ width: `${pct}%` }} />
  //     </div>
  //     <span className="w-8 text-sm text-right">{count}</span>
  //   </div>

  // For MVP, these are basic CSS-rendered charts. In a future iteration,
  // add recharts or chart.js for more sophisticated visualizations.
}
```

---

## 17. Institution Settings Page

### `src/pages/institution/SettingsPage.tsx`

Settings for the institution: edit profile, manage rubrics, notification preferences.

**API endpoints used:**
- `GET /institutions/me` → load current institution
- `PUT /institutions/me` → update institution
- `GET /reviews/rubrics` → list rubrics
- `POST /reviews/rubrics` → create rubric
- `GET /notifications/preferences` → notification prefs
- `PUT /notifications/preferences` → update prefs

**Layout:**

```
┌────────────────────────────────────────────────────────────┐
│  Settings                                                  │
├────────────────────────────────────────────────────────────┤
│  [Profile]  [Rubrics]  [Notifications]                     │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Profile Tab:                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Institution Name   [MIT                          ]  │   │
│  │ Type               [University ▾                 ]  │   │
│  │ Country            [United States                ]  │   │
│  │ Region             [Massachusetts                ]  │   │
│  │ City               [Cambridge                    ]  │   │
│  │ Website            [https://mit.edu              ]  │   │
│  │ Description        [                             ]  │   │
│  │                    [                             ]  │   │
│  │                              [Save Changes]         │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                            │
│  Rubrics Tab:                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Default Admissions Rubric          [Edit] [Delete]  │   │
│  │ Criteria: Academic (40%), Research (30%), ...        │   │
│  │                                                     │   │
│  │ CS-Specific Rubric                 [Edit] [Delete]  │   │
│  │ Criteria: Coding (35%), Math (25%), ...             │   │
│  │                                                     │   │
│  │                    [+ New Rubric]                    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                            │
│  Notifications Tab:                                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ☑ Email notifications enabled                       │   │
│  │ ☑ New applications                                  │   │
│  │ ☑ Interview confirmations                           │   │
│  │ ☐ Student messages                                  │   │
│  │ ☑ Event RSVPs                                       │   │
│  │                              [Save Preferences]     │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────┘
```

**Implementation:**

```typescript
// File: src/pages/institution/SettingsPage.tsx

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { getInstitution, updateInstitution } from '../../api/institutions'
import { getRubrics, createRubric } from '../../api/reviews'
import { getNotificationPreferences, updateNotificationPreferences } from '../../api/notifications'

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<'profile' | 'rubrics' | 'notifications'>('profile')
  const queryClient = useQueryClient()

  // === Profile Tab ===
  const { data: institution } = useQuery({
    queryKey: ['institution', 'me'],
    queryFn: getInstitution,
  })

  // Form with react-hook-form, pre-filled from institution data
  // Fields match UpdateInstitutionRequest:
  //   name, type (select), country, region, city, website_url, description_text, logo_url
  // Save → PUT /institutions/me → invalidate ['institution', 'me']

  // === Rubrics Tab ===
  const { data: rubrics } = useQuery({
    queryKey: ['rubrics'],
    queryFn: () => getRubrics(),
    enabled: activeTab === 'rubrics',
  })

  // List rubrics as cards
  // Each card: rubric name, criteria list (name + weight%), program association
  // Actions: Edit (inline or modal), Delete (with confirmation)
  // "New Rubric" button → form/modal:
  //   - Rubric name (text)
  //   - Program (select, optional)
  //   - Criteria list (dynamic):
  //     - Criterion name (text)
  //     - Weight (number, 0-100)
  //     - Description (text, optional)
  //   - Weights must sum to 100
  //   - Save → POST /reviews/rubrics

  // === Notifications Tab ===
  const { data: notifPrefs } = useQuery({
    queryKey: ['notification-preferences'],
    queryFn: getNotificationPreferences,
    enabled: activeTab === 'notifications',
  })

  // Checkboxes:
  //   - Email enabled (master toggle)
  //   - Individual toggles per notification type
  // Save → PUT /notifications/preferences

  // Render:
  // Tab bar at top: Profile | Rubrics | Notifications
  // Active tab content below
}
```

---

## 18. Institution API Modules

### `src/api/institutions.ts`

```typescript
import apiClient from './client'
import type {
  Institution, Program, Segment
} from '../types'

// === Institution Profile ===

export async function getInstitution(): Promise<Institution> {
  const { data } = await apiClient.get('/institutions/me')
  return data
}

export async function createInstitution(payload: {
  name: string
  type: string
  country: string
  region?: string
  city?: string
  website_url?: string
  description_text?: string
  logo_url?: string
}): Promise<Institution> {
  const { data } = await apiClient.post('/institutions/me', payload)
  return data
}

export async function updateInstitution(payload: Partial<{
  name: string
  type: string
  country: string
  region: string
  city: string
  website_url: string
  description_text: string
  logo_url: string
}>): Promise<Institution> {
  const { data } = await apiClient.put('/institutions/me', payload)
  return data
}

// === Programs ===

export async function getInstitutionPrograms(): Promise<Program[]> {
  const { data } = await apiClient.get('/institutions/me/programs')
  return data
}

export async function getInstitutionProgram(programId: string): Promise<Program> {
  const { data } = await apiClient.get(`/institutions/me/programs/${programId}`)
  return data
}

export async function createProgram(payload: {
  program_name: string
  degree_type: string
  department?: string
  duration_months?: number
  tuition?: number
  acceptance_rate?: number
  requirements?: Record<string, any>
  description_text?: string
  current_preferences_text?: string
  application_deadline?: string
  program_start_date?: string
  page_header_image_url?: string
  highlights?: string[]
  faculty_contacts?: { name: string; email?: string; role?: string }[]
}): Promise<Program> {
  const { data } = await apiClient.post('/institutions/me/programs', payload)
  return data
}

export async function updateProgram(programId: string, payload: Partial<{
  program_name: string
  degree_type: string
  department: string
  duration_months: number
  tuition: number
  acceptance_rate: number
  requirements: Record<string, any>
  description_text: string
  current_preferences_text: string
  application_deadline: string
  program_start_date: string
  page_header_image_url: string
  highlights: string[]
  faculty_contacts: { name: string; email?: string; role?: string }[]
}>): Promise<Program> {
  const { data } = await apiClient.put(`/institutions/me/programs/${programId}`, payload)
  return data
}

export async function publishProgram(programId: string): Promise<Program> {
  const { data } = await apiClient.post(`/institutions/me/programs/${programId}/publish`)
  return data
}

export async function unpublishProgram(programId: string): Promise<Program> {
  const { data } = await apiClient.post(`/institutions/me/programs/${programId}/unpublish`)
  return data
}

export async function deleteProgram(programId: string): Promise<void> {
  await apiClient.delete(`/institutions/me/programs/${programId}`)
}

// === Segments ===

export async function getSegments(): Promise<Segment[]> {
  const { data } = await apiClient.get('/institutions/me/segments')
  return data
}

export async function createSegment(payload: {
  segment_name: string
  program_id?: string | null
  criteria: Record<string, any>
  is_active?: boolean
}): Promise<Segment> {
  const { data } = await apiClient.post('/institutions/me/segments', payload)
  return data
}

export async function updateSegment(segmentId: string, payload: Partial<{
  segment_name: string
  program_id: string | null
  criteria: Record<string, any>
  is_active: boolean
}>): Promise<Segment> {
  const { data } = await apiClient.put(`/institutions/me/segments/${segmentId}`, payload)
  return data
}

export async function deleteSegment(segmentId: string): Promise<void> {
  await apiClient.delete(`/institutions/me/segments/${segmentId}`)
}
```

### `src/api/applications-admin.ts`

Institution-side application management endpoints.

```typescript
import apiClient from './client'
import type { Application, OfferLetter } from '../types'

// Note: "Application" type is shared with student side but
// ApplicationDetailResponse includes decision_notes and decision_by

export async function getApplicationsByProgram(programId: string): Promise<Application[]> {
  const { data } = await apiClient.get(`/applications/programs/${programId}`)
  return data
}

export async function reviewApplication(applicationId: string): Promise<Application> {
  const { data } = await apiClient.get(`/applications/review/${applicationId}`)
  return data
}

export async function makeDecision(applicationId: string, payload: {
  decision: 'admitted' | 'rejected' | 'waitlisted' | 'deferred'
  decision_notes?: string | null
}): Promise<Application> {
  const { data } = await apiClient.post(`/applications/review/${applicationId}/decision`, payload)
  return data
}

export async function createOffer(applicationId: string, payload: {
  offer_type: 'full_admission' | 'conditional' | 'waitlist_offer'
  tuition_amount?: number | null
  scholarship_amount?: number
  assistantship_details?: Record<string, any> | null
  financial_package_total?: number | null
  conditions?: Record<string, any> | null
  response_deadline?: string | null
}): Promise<OfferLetter> {
  const { data } = await apiClient.post(`/applications/review/${applicationId}/offer`, payload)
  return data
}
```

### `src/api/reviews.ts`

Review and scoring endpoints.

```typescript
import apiClient from './client'
import type {
  Rubric, ApplicationScore, ReviewAssignment, AIReviewSummary, PipelineData
} from '../types'

// === Rubrics ===

export async function getRubrics(programId?: string): Promise<Rubric[]> {
  const params = programId ? { program_id: programId } : {}
  const { data } = await apiClient.get('/reviews/rubrics', { params })
  return data
}

export async function createRubric(payload: {
  rubric_name: string
  criteria: { name: string; weight: number; description?: string }[]
  program_id?: string | null
}): Promise<Rubric> {
  const { data } = await apiClient.post('/reviews/rubrics', payload)
  return data
}

// === Application Review ===

export async function assignReviewer(applicationId: string): Promise<ReviewAssignment[]> {
  const { data } = await apiClient.post(`/reviews/applications/${applicationId}/assign`)
  return data
}

export async function scoreApplication(applicationId: string, payload: {
  rubric_id: string
  criterion_scores: Record<string, number>
  reviewer_notes?: string | null
}): Promise<ApplicationScore> {
  const { data } = await apiClient.post(`/reviews/applications/${applicationId}/score`, payload)
  return data
}

export async function getScores(applicationId: string): Promise<ApplicationScore[]> {
  const { data } = await apiClient.get(`/reviews/applications/${applicationId}/scores`)
  return data
}

export async function getAISummary(applicationId: string): Promise<AIReviewSummary> {
  const { data } = await apiClient.get(`/reviews/applications/${applicationId}/ai-summary`)
  return data
}

// === Pipeline ===

export async function getPipeline(programId: string): Promise<PipelineData> {
  const { data } = await apiClient.get(`/reviews/pipeline/${programId}`)
  return data
}
```

### `src/api/interviews-admin.ts`

Institution-side interview management.

```typescript
import apiClient from './client'
import type { Interview, InterviewScore } from '../types'

export async function proposeInterview(payload: {
  application_id: string
  interviewer_id: string
  interview_type: string
  proposed_times: string[]
  duration_minutes?: number
  location_or_link?: string | null
}): Promise<Interview> {
  const { data } = await apiClient.post('/interviews', payload)
  return data
}

export async function getInterviewsByApplication(applicationId: string): Promise<Interview[]> {
  const { data } = await apiClient.get(`/interviews/application/${applicationId}`)
  return data
}

export async function completeInterview(interviewId: string): Promise<Interview> {
  const { data } = await apiClient.post(`/interviews/${interviewId}/complete`)
  return data
}

export async function scoreInterview(interviewId: string, payload: {
  criterion_scores: Record<string, number>
  total_weighted_score: number
  interviewer_notes?: string | null
  recommendation?: string | null
  rubric_id?: string | null
}): Promise<InterviewScore> {
  const { data } = await apiClient.post(`/interviews/${interviewId}/score`, payload)
  return data
}
```

### `src/api/events-admin.ts`

Institution-side event management.

```typescript
import apiClient from './client'
import type { EventItem, RSVP } from '../types'

export async function getInstitutionEvents(status?: string): Promise<EventItem[]> {
  const params = status ? { status } : {}
  const { data } = await apiClient.get('/events/manage', { params })
  return data
}

export async function createEvent(payload: {
  event_name: string
  event_type: string
  start_time: string   // ISO datetime
  end_time: string
  description?: string
  location?: string
  capacity?: number
  program_id?: string | null
}): Promise<EventItem> {
  const { data } = await apiClient.post('/events/manage', payload)
  return data
}

export async function getEventAttendees(eventId: string): Promise<RSVP[]> {
  const { data } = await apiClient.get(`/events/manage/${eventId}/attendees`)
  return data
}
```

### Updates to existing API modules from Part 1

The following modules from Part 1 are shared between student and institution and need NO changes:
- `src/api/messaging.ts` — same endpoints for both roles
- `src/api/notifications.ts` — same endpoints for both roles
- `src/api/client.ts` — shared Axios instance
- `src/api/auth.ts` — shared auth endpoints

---

## 19. Institution-Specific Shared Components

### `src/components/shared/KPICard.tsx`

```typescript
Props:
- label: string
- value: string | number
- icon?: React.ReactNode
- trend?: { direction: 'up' | 'down' | 'flat'; value: string }
- onClick?: () => void

Renders:
- Compact card (white, rounded-lg, shadow-sm, border)
- Icon in top-left (24px, gray)
- Label below icon (text-xs, gray-500, uppercase tracking-wide)
- Value (text-2xl, font-bold)
- Optional trend indicator (green up arrow, red down arrow, or gray dash)
- Entire card clickable if onClick provided (hover:shadow-md)
```

### `src/components/shared/DataTable.tsx`

```typescript
Props:
- columns: { key: string; label: string; render?: (row: any) => React.ReactNode }[]
- data: any[]
- onRowClick?: (row: any) => void
- isLoading?: boolean
- emptyMessage?: string

Renders:
- Responsive table with:
  - Header row: column labels (text-xs, uppercase, gray-500, font-medium)
  - Data rows: alternating bg (white/gray-50), hover:bg-gray-100
  - Custom cell rendering via render prop
  - Loading state: skeleton rows
  - Empty state: centered message with icon
- Click on row → onRowClick(row)
```

### `src/components/shared/Modal.tsx`

```typescript
Props:
- isOpen: boolean
- onClose: () => void
- title: string
- children: React.ReactNode
- size?: 'sm' | 'md' | 'lg' (default 'md')

Renders:
- Backdrop: fixed inset-0, bg-black/50, z-50
- Modal panel: centered, white bg, rounded-xl, shadow-xl
  - Width by size: sm=max-w-sm, md=max-w-md, lg=max-w-lg
  - Header: title + close (X) button
  - Body: children (with overflow-y-auto, max-h-[70vh])
- Click backdrop → onClose
- Escape key → onClose
```

### `src/components/shared/ConfirmDialog.tsx`

```typescript
Props:
- isOpen: boolean
- onClose: () => void
- onConfirm: () => void
- title: string
- message: string
- confirmLabel?: string (default "Confirm")
- variant?: 'danger' | 'default' (default 'default')
- isLoading?: boolean

Renders:
- Uses Modal component
- Message text
- Two buttons: Cancel (gray outline) + Confirm (indigo or red if danger variant)
- isLoading disables confirm button and shows spinner
```

### `src/components/shared/Tabs.tsx`

```typescript
Props:
- tabs: { id: string; label: string; count?: number }[]
- activeTab: string
- onChange: (tabId: string) => void

Renders:
- Horizontal tab bar with bottom border
- Each tab: text-sm, px-4, py-2
- Active tab: indigo text, indigo bottom border (2px)
- Inactive tab: gray text, hover:gray-700
- Optional count badge next to label (small, rounded-full, bg-gray-100)
```

---

## 20. Verification Checklist

After building Part 2, verify:

- [ ] `npm run build` succeeds with zero TypeScript errors
- [ ] Login as institution_admin → redirects to `/i/dashboard`
- [ ] Dashboard shows KPI cards and programs list (or setup banner if no institution profile)
- [ ] `/i/setup` wizard creates institution + program + rubric step by step
- [ ] `/i/programs` lists all programs with correct status badges
- [ ] "New Program" button → `/i/programs/new` → form creates program successfully
- [ ] Edit existing program: click row → form pre-filled → save updates correctly
- [ ] Publish/unpublish toggles work from programs list
- [ ] Delete program with confirmation works
- [ ] `/i/pipeline` shows Kanban board with applications in correct columns
- [ ] Pipeline program filter dropdown works
- [ ] Cards are draggable between columns (visual feedback on drag)
- [ ] Click pipeline card → navigates to student detail page
- [ ] Student detail page shows all 4 tabs: Overview, Scores, Interview, AI Summary
- [ ] "Make Decision" creates decision via API
- [ ] "Create Offer" form submits correctly
- [ ] "Score Application" modal works with rubric selection
- [ ] `/i/reviews` shows review queue with pending/reviewed sections
- [ ] `/i/interviews` shows interview list with schedule/complete/score actions
- [ ] `/i/messages` shows conversations and sending works
- [ ] New conversation creation works from institution side
- [ ] `/i/segments` CRUD works: create, edit, delete segments
- [ ] `/i/campaigns` shows placeholder page with "Coming Soon" message
- [ ] `/i/events` lists events, create event works, view attendees works
- [ ] `/i/analytics` shows KPI cards and status bar charts
- [ ] `/i/settings` → Profile tab: edit and save institution info
- [ ] `/i/settings` → Rubrics tab: list, create new rubric with criteria
- [ ] `/i/settings` → Notifications tab: toggle preferences and save
- [ ] Sidebar collapses and expands correctly
- [ ] Sidebar nav highlights active route
- [ ] All empty states render correctly (no programs, no applications, etc.)
- [ ] API errors show user-friendly toast messages
- [ ] Notification bell in top bar shows unread count

---

## IMPORTANT NOTES FOR CODING TOOL

1. **Same rules as Part 1 apply:** No component library, all Tailwind, react-hook-form + zod for forms, TanStack Query for all data fetching, invalidate queries after mutations.

2. **@dnd-kit imports:** Use `@dnd-kit/core` for DndContext and sensors, `@dnd-kit/sortable` for SortableContext and useSortable, `@dnd-kit/utilities` for CSS.Transform. These are the only additional deps beyond Part 1.

3. **Pipeline page is THE critical page.** Spend the most time on it. It needs to feel snappy and responsive. Cards should have clear visual hierarchy: student name → program → score → date.

4. **Student Detail Page has modals.** Build a reusable Modal component first, then use it for: Decision modal, Offer modal, Scoring modal, Interview scheduling modal. Each modal has its own form with react-hook-form + zod.

5. **API module file names match this convention:**
   - `institutions.ts` → institution profile, programs, segments
   - `applications-admin.ts` → institution-side application endpoints
   - `reviews.ts` → rubrics, scoring, pipeline
   - `interviews-admin.ts` → institution-side interview endpoints
   - `events-admin.ts` → institution-side event management
   - `messaging.ts` (shared, from Part 1)
   - `notifications.ts` (shared, from Part 1)

6. **The Campaigns page is a placeholder.** Don't overthink it — it's a "Coming Soon" page. The real campaign engine is Phase 2 backend work.

7. **Analytics charts are simple CSS bars.** Don't install recharts or chart.js for MVP. Use Tailwind utility classes to render horizontal bar segments. A `<div>` with dynamic `width` percentage and background color is sufficient.

8. **Responsive is NOT a priority.** Desktop-first, minimum 1280px viewport for institution side (wider than student side because of the sidebar + pipeline board).

9. **The institution sidebar is collapsible.** It reads `sidebarCollapsed` from the UI store (shared with the toggle button). When collapsed: 64px wide, icons only. When expanded: 240px, icons + labels + section headers.

10. **Route structure was already defined in Part 1's App.tsx.** All institution routes under `/i/*` with InstitutionLayout wrapper are already set up. You just need to build the page components and import them.
