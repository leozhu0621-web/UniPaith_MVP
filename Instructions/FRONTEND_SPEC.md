# UniPaith Frontend Specification

## Product Positioning

- **Student side (2C):** "An AI-powered admissions experience" — chat-first, the AI conversation IS the app
- **Institution side (2B):** "An AI-powered student admissions operating system" — pipeline-centric, a workspace they live in

## Tech Stack

- **Framework:** Vite + React 19 + TypeScript (strict mode)
- **Styling:** Tailwind CSS 3
- **Routing:** React Router v7 (`createBrowserRouter`)
- **State:** Zustand for global state (auth, user context), React Query (TanStack Query v5) for server state / caching
- **Forms:** React Hook Form + Zod validation
- **HTTP:** Axios instance with interceptor for auth token injection + refresh
- **Icons:** Lucide React
- **Dates:** date-fns
- **Chat:** Custom WebSocket hook (future), REST polling for MVP
- **DnD:** @dnd-kit (for pipeline Kanban)

## Project Structure

```
frontend/
├── src/
│   ├── main.tsx                    # Entry point
│   ├── App.tsx                     # Router setup
│   ├── api/
│   │   ├── client.ts              # Axios instance, interceptors, token refresh
│   │   ├── auth.ts                # signup, login, refresh, me
│   │   ├── students.ts            # profile, academics, scores, activities, preferences, onboarding
│   │   ├── institutions.ts        # institution CRUD, segments
│   │   ├── programs.ts            # public browse + admin CRUD
│   │   ├── applications.ts        # create, list, update, submit
│   │   ├── documents.ts           # request-upload, confirm, list, download
│   │   ├── matching.ts            # match results, explain
│   │   ├── messaging.ts           # conversations, messages
│   │   ├── events.ts              # events, RSVPs
│   │   ├── interviews.ts          # interview scheduling, scoring
│   │   ├── reviews.ts             # application reviews, rubrics, scoring
│   │   ├── saved-lists.ts         # saved lists CRUD
│   │   └── notifications.ts       # notification feed
│   ├── stores/
│   │   ├── auth-store.ts          # Zustand: user, tokens, role, login/logout
│   │   └── ui-store.ts            # Zustand: sidebar collapsed, active chat, modals
│   ├── hooks/
│   │   ├── use-auth.ts            # Auth context hook
│   │   ├── use-api.ts             # TanStack Query wrapper hooks
│   │   └── use-chat.ts            # Chat polling / WebSocket hook
│   ├── components/
│   │   ├── ui/                    # Reusable primitives (Button, Input, Modal, Card, Badge, etc.)
│   │   ├── layout/
│   │   │   ├── StudentLayout.tsx  # Chat-first shell with side panels
│   │   │   ├── InstitutionLayout.tsx # Sidebar nav + top bar + content area
│   │   │   └── AuthLayout.tsx     # Centered card layout for login/signup
│   │   └── shared/
│   │       ├── ChatBubble.tsx
│   │       ├── MatchCard.tsx
│   │       ├── ProgramCard.tsx
│   │       ├── KanbanBoard.tsx
│   │       ├── FileUploader.tsx
│   │       ├── RichTextEditor.tsx
│   │       └── StatusBadge.tsx
│   ├── pages/
│   │   ├── auth/
│   │   │   ├── LoginPage.tsx
│   │   │   ├── SignupPage.tsx
│   │   │   └── RoleSelectPage.tsx
│   │   ├── student/               # 2C: "The Experience"
│   │   │   ├── ChatPage.tsx       # THE primary view
│   │   │   ├── ProfilePage.tsx
│   │   │   ├── DiscoverPage.tsx
│   │   │   ├── SchoolDetailPage.tsx
│   │   │   ├── ApplicationsPage.tsx
│   │   │   ├── ApplicationDetailPage.tsx
│   │   │   ├── SavedListPage.tsx
│   │   │   ├── MessagesPage.tsx
│   │   │   ├── CalendarPage.tsx
│   │   │   └── SettingsPage.tsx
│   │   ├── institution/           # 2B: "The Operating System"
│   │   │   ├── DashboardPage.tsx
│   │   │   ├── SetupPage.tsx
│   │   │   ├── ProgramsPage.tsx
│   │   │   ├── ProgramEditorPage.tsx
│   │   │   ├── PipelinePage.tsx   # THE primary view (Kanban)
│   │   │   ├── StudentDetailPage.tsx
│   │   │   ├── ReviewQueuePage.tsx
│   │   │   ├── InterviewsPage.tsx
│   │   │   ├── MessagingPage.tsx
│   │   │   ├── SegmentsPage.tsx
│   │   │   ├── CampaignsPage.tsx
│   │   │   ├── EventsPage.tsx
│   │   │   ├── AnalyticsPage.tsx
│   │   │   └── SettingsPage.tsx
│   │   └── public/
│   │       ├── LandingPage.tsx
│   │       └── ProgramBrowsePage.tsx
│   ├── types/
│   │   └── index.ts               # All TypeScript interfaces matching backend schemas
│   └── utils/
│       ├── format.ts              # Date, currency, percentage formatters
│       └── constants.ts           # Enums, tier labels, status labels
```

---

## Routing

```
/                           → LandingPage (public)
/browse                     → ProgramBrowsePage (public)
/login                      → LoginPage
/signup                     → SignupPage
/signup/role                → RoleSelectPage (student or institution)

/s/                         → StudentLayout wrapper (requires auth + role=student)
  /s/chat                   → ChatPage (default landing after login)
  /s/profile                → ProfilePage
  /s/discover               → DiscoverPage (AI-ranked matches + search)
  /s/schools/:programId     → SchoolDetailPage
  /s/applications           → ApplicationsPage
  /s/applications/:appId    → ApplicationDetailPage
  /s/saved                  → SavedListPage
  /s/messages               → MessagesPage
  /s/messages/:convId       → MessagesPage (with conversation open)
  /s/calendar               → CalendarPage
  /s/settings               → SettingsPage

/i/                         → InstitutionLayout wrapper (requires auth + role=institution_admin)
  /i/dashboard              → DashboardPage (default landing after login)
  /i/setup                  → SetupPage (institution profile, shown if not configured)
  /i/programs               → ProgramsPage
  /i/programs/new           → ProgramEditorPage (create)
  /i/programs/:id/edit      → ProgramEditorPage (edit)
  /i/pipeline               → PipelinePage (default working view)
  /i/pipeline/:studentId    → StudentDetailPage (slide-over or full page)
  /i/reviews                → ReviewQueuePage
  /i/interviews             → InterviewsPage
  /i/messages               → MessagingPage
  /i/segments               → SegmentsPage
  /i/campaigns              → CampaignsPage
  /i/events                 → EventsPage
  /i/analytics              → AnalyticsPage
  /i/settings               → SettingsPage
```

Route guards: `RequireAuth` component checks Zustand auth store. If no valid token, redirect to `/login`. If token exists but role doesn't match the section (`/s/` vs `/i/`), redirect to the correct section root.

---

## Authentication Flow

1. User signs up → chooses role (student / institution_admin) → `POST /api/v1/auth/signup`
2. User logs in → `POST /api/v1/auth/login` → receives `access_token` + `refresh_token`
3. Axios interceptor attaches `Authorization: Bearer <access_token>` to every request
4. On 401 response → interceptor calls `POST /api/v1/auth/refresh` with refresh_token → retries original request
5. On refresh failure → clear store → redirect to `/login`
6. `GET /api/v1/auth/me` on app load to restore session from stored tokens

Token storage: `localStorage` for refresh_token (long-lived), in-memory Zustand store for access_token (short-lived).

---

## STUDENT SIDE — "The Experience"

### Design Philosophy

The student experience is **chat-first**. The AI chat is the central hub — not a sidebar feature. Students interact primarily through natural language. The AI builds their profile, recommends schools, explains matches, helps with essays, and guides applications. Traditional UI views (profile, matches, applications) exist as **read-only dashboards** of what the chat has produced, with the ability to edit directly.

### Layout: `StudentLayout`

```
┌──────────────────────────────────────────────────────┐
│  UniPaith            [Profile] [🔔] [⚙️]            │
├──────────┬───────────────────────────────────────────┤
│          │                                           │
│ Nav rail │          Main content area                │
│          │                                           │
│ 💬 Chat  │   (ChatPage, ProfilePage, etc.)           │
│ 👤 Profile│                                          │
│ 🔍 Discover│                                         │
│ 📄 Apps  │                                           │
│ 💾 Saved │                                           │
│ ✉️ Messages│                                         │
│ 📅 Calendar│                                         │
│          │                                           │
├──────────┴───────────────────────────────────────────┤
│  Onboarding progress bar (if < 100%)                 │
└──────────────────────────────────────────────────────┘
```

The nav rail is a narrow icon-only sidebar (expands on hover). Chat is always the top item and default view. When onboarding is incomplete, a persistent progress bar shows at the bottom.

### Screen Details

#### S1. ChatPage (primary view)

```
┌─────────────────────────────────────────┐
│  Chat messages (scrollable)             │
│                                         │
│  [AI] Welcome to UniPaith! I'm your     │
│  admissions advisor. Let's start by     │
│  getting to know you...                 │
│                                         │
│  [Student] I'm a senior at MIT...       │
│                                         │
│  [AI] Great! Based on what you've       │
│  told me, I've found 12 programs...     │
│  [Inline match cards — clickable]       │
│                                         │
│  [AI] Here's your updated profile:      │
│  [Inline profile summary card]          │
│                                         │
├─────────────────────────────────────────┤
│  [Type a message...]           [Send]   │
│  [📎 Upload] [Quick actions ▾]          │
└─────────────────────────────────────────┘
```

- **Inline rich content:** The AI can embed match cards, profile summaries, school cards, application checklists, and action buttons directly in the chat stream
- **Quick actions dropdown:** "Update my GPA", "Add a test score", "Show my matches", "Help with essay", "Upload transcript"
- **File attachment:** Triggers the document upload flow (presigned URL → S3)
- **Chat history:** Loads via `GET /api/v1/conversations` (the AI advisor conversation)
- **MVP implementation:** REST polling every 3-5 seconds for new messages. WebSocket in Phase 2.
- **Backend endpoints used:** Messaging API for chat persistence. Student profile APIs triggered by AI actions.

#### S2. ProfilePage

A read-only dashboard showing everything the AI has extracted/collected. Organized as cards:

- **Basic Info** card (name, nationality, residence) — edit inline
- **Academic Records** card (list of schools, degrees, GPAs) — add/edit/delete
- **Test Scores** card (SAT, GRE, TOEFL, etc.) — add/edit/delete
- **Activities** card (work, research, volunteering, etc.) — add/edit/delete
- **Essay / Bio** card (free-text) — edit
- **Goals** card (free-text + structured career goals) — edit
- **Preferences** card (countries, budget, city size, funding, values) — edit
- **Documents** card (uploaded files with download links) — upload/delete
- **Onboarding completion** indicator at top

Each card has an "Edit" button that opens an inline form or modal. After any edit, `_update_onboarding()` is called on the backend to refresh completion %.

Backend endpoints: `GET/PUT /students/me/profile`, `GET/POST/PUT/DELETE /students/me/academics`, `/test-scores`, `/activities`, `/preferences`, `/documents/*`

#### S3. DiscoverPage

AI-curated school matches + manual search/filter.

```
┌─────────────────────────────────────────┐
│  Your Matches          [Filter ▾] [🔍]  │
│  Profile 87% complete — complete for    │
│  better matches                         │
├─────────────────────────────────────────┤
│                                         │
│  🟢 SAFETY (4)                          │
│  ┌─────────┐ ┌─────────┐               │
│  │ MIT CS  │ │ Stanford│               │
│  │ 92% fit │ │ 89% fit │               │
│  │ Tier: S │ │ Tier: S │               │
│  └─────────┘ └─────────┘               │
│                                         │
│  🟡 MATCH (6)                           │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐  │
│  │ ...     │ │ ...     │ │ ...     │  │
│  └─────────┘ └─────────┘ └─────────┘  │
│                                         │
│  🔴 REACH (2)                           │
│  ...                                    │
│                                         │
│  Browse All Programs                    │
│  [Search...] [Country ▾] [Degree ▾]    │
│  [Program cards grid]                   │
└─────────────────────────────────────────┘
```

- Top section: AI-matched programs grouped by tier (reach / match / safety)
- Each card shows: program name, institution, match score %, tier badge, key stats
- Click → SchoolDetailPage
- Save / unsave (heart icon) → saved lists API
- Bottom section: public program search (`GET /api/v1/programs` with filters)
- Filter bar: country, degree type, tuition range, search query
- Requires 80%+ onboarding completion for AI matches; shows prompt to complete profile if below

Backend endpoints: matching API (TBD Phase 2 endpoint), `GET /programs` (public search), saved lists API

#### S4. SchoolDetailPage

Deep dive on a specific program.

- **Hero section:** Institution name, logo, location, ranking badges
- **Program details:** Degree type, duration, tuition, acceptance rate, deadlines, requirements
- **AI match analysis:** Score breakdown (academic fit, preference alignment, etc.) + NL explanation
- **Highlights:** Key selling points from program data
- **Application status:** If already applied — show status. If not — "Apply" CTA.
- **Save / Compare** buttons
- **Engagement signals:** Viewing this page fires `POST /engagement-signals` (viewed_program, time_spent)

Backend endpoints: `GET /programs/{id}`, matching explain API, engagement signals API, applications API

#### S5. ApplicationsPage

All applications in a list/grid.

- Status filter tabs: All / Draft / Submitted / Under Review / Decision
- Each card: program name, institution, status badge, submitted date, completion %
- Click → ApplicationDetailPage
- "Start New Application" button → picks from saved/matched programs

Backend endpoints: `GET /applications`

#### S6. ApplicationDetailPage

Per-program application management.

- **Checklist panel:** Auto-generated requirements checklist with completion status
- **Documents panel:** Upload/manage documents for this application (transcript, essay, resume, recommendation)
- **Essay workshop:** AI-assisted essay writing area (drafts, AI feedback, version history)
- **Resume builder:** AI-adapted resume for this specific program
- **Status timeline:** Visual progress (draft → submitted → under review → interview → decision)
- **Submit button:** Only active when checklist is 100% complete
- **Offer section:** If decision=admitted, shows offer details + accept/decline

Backend endpoints: `GET/PUT /applications/{id}`, `/documents/*`, `/checklists`, essay/resume schemas

#### S7. SavedListPage

Manage saved program lists.

- Create/rename/delete lists
- Drag programs between lists
- Quick-compare view: side-by-side stats for selected programs

Backend endpoints: saved lists API

#### S8. MessagesPage

Conversations with institutions.

- Conversation list sidebar (left)
- Message thread (right)
- New message button → select institution/program to message
- Unread count badges

Backend endpoints: messaging API

#### S9. CalendarPage

Deadlines and events.

- Calendar view (month/week/day toggle)
- Auto-populated with: application deadlines, interview slots, event RSVPs
- Can add custom reminders
- Click event → navigate to relevant detail page

Backend endpoints: student calendar API, events API

#### S10. SettingsPage

- Account info (email, role)
- Notification preferences
- Change password (redirects to Cognito hosted UI)
- Delete account

---

## INSTITUTION SIDE — "The Operating System"

### Design Philosophy

The institution experience is a **professional workspace** centered on a student pipeline. Think: a CRM that understands admissions. The pipeline board is the primary working surface — everything else supports the flow of moving students through stages. AI assists with scoring, matching, and insights but doesn't replace human judgment.

### Layout: `InstitutionLayout`

```
┌──────────────────────────────────────────────────────┐
│  UniPaith             [🔔 12] [Search...] [Admin ▾]  │
├──────────┬───────────────────────────────────────────┤
│          │                                           │
│ Sidebar  │          Main content area                │
│          │                                           │
│ 📊 Dashboard│                                        │
│ 🏫 Programs│                                         │
│ 📋 Pipeline│  (DashboardPage, PipelinePage, etc.)    │
│ 📝 Reviews │                                         │
│ 🎤 Interviews│                                       │
│ ✉️ Messages│                                         │
│ ───────── │                                          │
│ 🎯 Segments│                                         │
│ 📢 Campaigns│                                        │
│ 🗓️ Events │                                          │
│ 📈 Analytics│                                        │
│ ───────── │                                          │
│ ⚙️ Settings│                                         │
│          │                                           │
└──────────┴───────────────────────────────────────────┘
```

Full sidebar with icons + labels. Collapsible to icon-only mode. Section dividers separate core workflow (pipeline, reviews, interviews) from outreach (segments, campaigns, events) and admin (settings, analytics).

### Screen Details

#### I1. DashboardPage (landing)

```
┌─────────────────────────────────────────┐
│  Good morning, [Name]                   │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐     │
│  │ 342 │ │  47 │ │  12 │ │  8  │     │
│  │Total│ │ New │ │Under│ │Offers│     │
│  │Apps │ │Today│ │Revw │ │Sent │     │
│  └─────┘ └─────┘ └─────┘ └─────┘     │
│                                         │
│  Pipeline Summary (mini bar chart)      │
│  [Discovered: 1200] [Reviewed: 340]     │
│  [Shortlisted: 85] [Interview: 28]     │
│  [Decision: 47] [Enrolled: 12]          │
│                                         │
│  Recent Activity                        │
│  • John Smith submitted application     │
│  • AI scored 15 new applications        │
│  • Interview with Jane Doe at 2pm       │
│                                         │
│  Upcoming Deadlines                     │
│  • Fall 2026 MS CS deadline: Apr 15     │
│  • Webinar: AI in Admissions — Apr 3    │
│                                         │
│  Action Items                           │
│  • 12 applications need review          │
│  • 3 interviews need scheduling         │
│  • 2 offer responses overdue            │
└─────────────────────────────────────────┘
```

KPI cards at top, pipeline summary chart, activity feed, upcoming deadlines, action items.

Backend endpoints: aggregation queries across applications, events, interviews, reviews

#### I2. SetupPage

First-run setup for new institution accounts. Wizard-style:

1. Institution profile (name, type, country, description)
2. First program (create at least one program)
3. Preferences (what kind of students are you looking for?)
4. Publish (review and publish first program)

Backend endpoints: `POST /institutions/me`, `POST /institutions/me/programs`, publish flow

#### I3. ProgramsPage

List all programs with stats.

- Table/grid view toggle
- Columns: name, degree, status (published/draft), applications count, acceptance rate, deadline
- Actions: edit, publish/unpublish, delete
- "Add Program" button → ProgramEditorPage

Backend endpoints: `GET /institutions/me/programs`

#### I4. ProgramEditorPage

Full-page form for creating/editing a program.

- Sections: Basic info, requirements, description, preferences, deadlines, highlights, faculty
- Preview mode (what students will see)
- Publish validation (shows what's missing)
- Save as draft / Publish buttons

Backend endpoints: `POST/PUT /institutions/me/programs/{id}`, publish/unpublish

#### I5. PipelinePage (primary working view)

Kanban board with configurable columns.

```
┌─────────────────────────────────────────────────────┐
│  Pipeline  [Program: All ▾] [Segment: All ▾] [🔍]   │
├─────────┬─────────┬─────────┬─────────┬─────────────┤
│Discovered│Reviewed │Shortlist│Interview│ Decision    │
│  (1200) │  (340)  │  (85)  │  (28)   │  (47)       │
├─────────┼─────────┼─────────┼─────────┼─────────────┤
│┌───────┐│┌───────┐│┌───────┐│┌───────┐│┌───────────┐│
││J. Smith││A. Chen ││M. Patel││T. Kim  ││R. Garcia   ││
││GPA 3.8 ││GPA 3.9 ││GPA 3.7 ││GPA 3.6 ││✅ Admitted  ││
││92% fit ││87% fit ││85% fit ││88% fit ││Offer sent  ││
││🟢 Safety││🟡 Match ││🟡 Match ││🔴 Reach ││Awaiting    ││
│└───────┘│└───────┘│└───────┘│└───────┘│└───────────┘│
│┌───────┐│┌───────┐│         │         │             │
││...     ││...     ││         │         │             │
│└───────┘│└───────┘│         │         │             │
└─────────┴─────────┴─────────┴─────────┴─────────────┘
```

- **Columns:** Discovered → Reviewed → Shortlisted → Interview → Decision → Enrolled
- **Student cards:** Name, key stats (GPA, match score), tier badge, status indicator
- **Drag-and-drop** to move students between stages
- **Filters:** By program, segment, match tier, score range
- **Click card** → slide-over panel or navigate to StudentDetailPage
- **Bulk actions:** Select multiple → move stage, assign reviewer, send campaign
- **Search** within pipeline

Backend endpoints: applications API (status-based queries), matching API, drag → `PUT /applications/{id}` status update

#### I6. StudentDetailPage

Full student profile from the institution's perspective.

- **Header:** Student name, match score, tier badge, current application status
- **AI Summary:** One-paragraph AI-generated fit analysis (from matching explain API)
- **Profile tabs:**
  - Overview (bio, goals, key stats)
  - Academics (records, GPA, test scores)
  - Activities (work, research, extracurriculars)
  - Documents (uploaded transcripts, essays, resume — with download links)
  - Application (status, checklist completion, submitted materials)
- **Scoring panel:** Rubric-based scoring form (criterion scores + notes)
- **Actions:** Move to next stage, assign reviewer, schedule interview, send message
- **CRM timeline:** All touchpoints with this student (views, messages, events attended, campaign interactions)
- **Comparison button:** Compare this student against other shortlisted candidates

Backend endpoints: student profile API (institution view), applications, reviews/scoring, CRM records, messaging

#### I7. ReviewQueuePage

Prioritized list of applications needing review.

- Sort by: submission date, match score, assigned reviewer, program
- Filter by: program, status, reviewer assignment
- Each row: student name, program, match score, submitted date, assigned reviewer, status
- Click → opens scoring interface (inline or StudentDetailPage)
- Assign reviewer dropdown
- AI-suggested scores shown alongside (from `scored_by_type = ai_suggested`)

Backend endpoints: reviews API, applications API, rubrics API, application scores API

#### I8. InterviewsPage

Interview scheduling and management.

- Calendar view + list view toggle
- Upcoming interviews with student name, time, type (video/in-person), status
- Schedule new interview: pick student, propose times, set type and duration
- After interview: scoring form with rubric + recommendation (strong_admit / admit / borderline / reject)
- Status tracking: invited → scheduling → confirmed → completed

Backend endpoints: interviews API, interview scores API

#### I9. MessagingPage

Conversations with students.

- Conversation list with student name, program, last message preview, unread badge
- Threaded message view
- Quick templates for common messages
- Message status (sent, read)

Backend endpoints: messaging API

#### I10. SegmentsPage

Define and manage target student segments.

- List of segments with name, criteria summary, student count
- Create/edit segment: visual criteria builder (GPA range, field, region, test scores)
- Preview: see which students match this segment
- Link segments to campaigns

Backend endpoints: segments API, matching/filter API

#### I11. CampaignsPage

Outreach campaign management.

- Campaign list with status (draft, scheduled, active, completed)
- Create campaign: select segment, compose message, schedule send
- Performance: delivered, opened, clicked, responded counts
- Templates library

Backend endpoints: campaigns API, campaign recipients API

#### I12. EventsPage

Event management (webinars, campus visits, info sessions).

- Event list with date, type, RSVP count, capacity
- Create/edit event form
- RSVP list with student details
- Post-event: mark attendance

Backend endpoints: events API, event RSVPs API

#### I13. AnalyticsPage

Reporting dashboard.

- Application funnel chart (by program)
- Yield rate trends
- Match score distribution
- Demographic breakdown of applicants
- Engagement metrics (program views, saves, time spent)
- Compare programs side-by-side

Backend endpoints: aggregation queries, engagement signals API, applications API

#### I14. SettingsPage

- Institution profile edit
- Team management (add reviewers)
- Rubric management (create/edit scoring rubrics)
- Notification preferences
- API keys / integration settings (future)

Backend endpoints: institution API, reviewers API, rubrics API

---

## Shared Components Specification

### `api/client.ts` — HTTP Client

```
- Base URL from VITE_API_URL env var (default: http://localhost:8000/api/v1)
- Request interceptor: inject Authorization header from auth store
- Response interceptor: on 401, attempt token refresh, retry original request
- Response interceptor: on 403, show "Access denied" toast
- Response interceptor: on 5xx, show "Server error" toast
- Automatic JSON serialization/deserialization
```

### `components/ui/` — Design System Primitives

The following primitives should be created as the foundation. No external component library — hand-build with Tailwind:

- **Button** — variants: primary, secondary, ghost, danger. Sizes: sm, md, lg. Loading state.
- **Input** — text, number, email, password. With label, error message, helper text.
- **Textarea** — with character count, auto-resize.
- **Select** — single and multi-select with search.
- **Modal** — centered overlay with header, body, footer. Sizes: sm, md, lg, full.
- **Card** — with header, body, footer slots. Hover and click variants.
- **Badge** — status colors (green/yellow/red/blue/gray). Sizes: sm, md.
- **Toast** — success, error, warning, info. Auto-dismiss. Stackable.
- **Tabs** — horizontal tab bar with content panels.
- **Table** — sortable columns, pagination, row selection, loading skeleton.
- **Dropdown** — trigger + menu. With icons, dividers, keyboard navigation.
- **Avatar** — with initials fallback.
- **Skeleton** — loading placeholder for all major components.
- **EmptyState** — illustration + message + CTA for empty views.
- **ProgressBar** — determinate with percentage label.

### `components/shared/` — Domain Components

- **ChatBubble** — message bubble with sender avatar, timestamp, rich content slots
- **MatchCard** — program card with match score, tier badge, key stats, save button
- **ProgramCard** — lighter card for search results
- **KanbanBoard** — generic drag-and-drop column board (used for pipeline)
- **KanbanColumn** — single column with header count + scrollable cards
- **KanbanCard** — draggable student summary card
- **FileUploader** — drag-and-drop zone + file list, handles presigned URL flow
- **StatusBadge** — application/interview/event status with appropriate color
- **ScoreBreakdown** — visual breakdown of match score components
- **RubricScorer** — form for scoring against a rubric's criteria
- **Timeline** — vertical timeline for CRM touchpoints or application history

---

## State Management

### Auth Store (Zustand)

```typescript
interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  signup: (email: string, password: string, role: string) => Promise<void>
  logout: () => void
  refreshAccessToken: () => Promise<void>
  loadSession: () => Promise<void>  // called on app mount
}
```

### Server State (TanStack Query)

All API data fetched via TanStack Query hooks. Key patterns:

- `useProfile()` → `GET /students/me/profile` (stale time: 5 min)
- `useMatches()` → matching API (stale time: 10 min)
- `useApplications()` → `GET /applications` (stale time: 1 min)
- `usePipeline(filters)` → applications by status (stale time: 30 sec for pipeline)
- Mutations invalidate relevant queries (e.g., `createAcademicRecord` invalidates `profile`)

---

## Build Order

The frontend should be built in this order. Each step corresponds to a prompt file in `Instructions/Frontend/`:

1. **Prompt 01 — Foundation:** Project setup, routing, auth store, API client, auth pages (login/signup). Outcome: can sign up, log in, see correct role-based shell.

2. **Prompt 02 — Student Shell:** StudentLayout, nav rail, ChatPage (basic message UI with REST polling), ProfilePage (read-only display of profile data). Outcome: student can log in and see their chat + profile.

3. **Prompt 03 — Student Profile CRUD:** Edit forms for all profile sections (academics, test scores, activities, preferences, documents), onboarding progress indicator. Outcome: student can fully build their profile through forms.

4. **Prompt 04 — Student Discovery & Applications:** DiscoverPage (public program search + match display), SchoolDetailPage, ApplicationsPage, ApplicationDetailPage (checklist, documents, essay area). Outcome: student can browse schools, view matches, and manage applications.

5. **Prompt 05 — Student Supporting Pages:** SavedListPage, MessagesPage, CalendarPage, SettingsPage. Outcome: complete student experience.

6. **Prompt 06 — Institution Shell:** InstitutionLayout, sidebar nav, DashboardPage (KPI cards + activity feed), SetupPage (first-run wizard). Outcome: institution admin can log in and see dashboard.

7. **Prompt 07 — Institution Programs:** ProgramsPage (list), ProgramEditorPage (create/edit form with validation), publish/unpublish flow. Outcome: institution can manage their programs.

8. **Prompt 08 — Institution Pipeline:** PipelinePage (Kanban board with drag-and-drop), StudentDetailPage (full student review), status transitions. Outcome: institution can manage student pipeline.

9. **Prompt 09 — Institution Reviews & Interviews:** ReviewQueuePage, rubric-based scoring, InterviewsPage, interview scheduling and scoring. Outcome: institution can review applications and manage interviews.

10. **Prompt 10 — Institution Outreach & Analytics:** SegmentsPage, CampaignsPage, EventsPage, AnalyticsPage, MessagingPage. Outcome: complete institution experience.

11. **Prompt 11 — UI Polish & Shared Components:** Design system primitives, empty states, loading skeletons, error boundaries, toast notifications, responsive adjustments. Outcome: polished, production-ready feel.

---

## Backend Endpoint Coverage

This frontend design covers ALL existing backend routes:

| Backend Route File | Frontend Consumer |
|---|---|
| auth.py | LoginPage, SignupPage, auth store |
| students.py | ProfilePage, ChatPage (AI actions) |
| institutions.py | SetupPage, SettingsPage |
| programs.py | ProgramsPage, ProgramEditorPage, DiscoverPage, SchoolDetailPage, ProgramBrowsePage |
| applications.py | ApplicationsPage, ApplicationDetailPage, PipelinePage |
| documents.py | ProfilePage (documents), ApplicationDetailPage |
| messaging.py | MessagesPage (student), MessagingPage (institution), ChatPage |
| events.py | CalendarPage (student), EventsPage (institution) |
| interviews.py | InterviewsPage (institution) |
| reviews.py | ReviewQueuePage, StudentDetailPage (scoring) |
| saved_lists.py | SavedListPage, DiscoverPage |
| notifications.py | Notification bell in both layouts |
| ml_admin.py | AnalyticsPage (model performance section) |
| crawler_admin.py | SettingsPage (data sources section — admin only) |
| workshops.py | EventsPage (workshop type events) |
