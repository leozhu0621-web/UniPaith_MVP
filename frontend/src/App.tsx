import { createBrowserRouter, RouterProvider, Navigate, useParams, useSearchParams } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { lazy, Suspense, useEffect, type ReactNode } from 'react'
import { useAuthStore } from './stores/auth-store'
import ToastContainer from './components/ui/Toast'
import ConfirmHost from './components/ui/ConfirmDialog'
import DemoNotice from './components/system/DemoNotice'
import FeedbackWidget from './components/system/FeedbackWidget'
import AppErrorBoundary from './components/system/AppErrorBoundary'
import PageLoader from './components/ui/PageLoader'

// Layouts — eager: the shell must mount instantly and stay mounted while page
// chunks load (UX overhaul Ship A, 2026-06-12 spec §1).
import AuthLayout from './components/layout/AuthLayout'
import StudentLayout from './components/layout/StudentLayout'
import InstitutionLayout from './components/layout/InstitutionLayout'
import RequireAuth from './components/layout/RequireAuth'
import PublicLayout from './components/layout/PublicLayout'
import MySpaceShell from './pages/student/myspace/MySpaceShell'

// Redirect components — eager (tiny, and a redirect must never wait on a chunk).
import { LegacyApplicantRedirect, LegacyPipelineRedirect } from './pages/institution/LegacyPipelineRedirect'
import { POSTS_TAB_REDIRECTS } from './utils/information-architecture'

// Route error element — eager so it can render even when a page chunk fails to load.
import RouteErrorPage from './pages/system/RouteErrorPage'

// ─── Route-level code splitting (UX overhaul Ship A, 2026-06-12 spec §1) ───
// Every page is a lazy chunk; each route element wraps its page in
// <Suspense fallback={<PageLoader/>}> via page() below, so the boundary sits
// INSIDE the layout's <Outlet> and the nav/shell stays mounted while a chunk
// loads. Layouts, auth guards, and redirects above stay eager.

// Auth pages
const LoginPage = lazy(() => import('./pages/auth/LoginPage'))
const SignupPage = lazy(() => import('./pages/auth/SignupPage'))
const AuthCallbackPage = lazy(() => import('./pages/auth/AuthCallbackPage'))

// Public pages (program browsing — linked from the marketing site at unipaith.co)
const ProgramBrowsePage = lazy(() => import('./pages/public/ProgramBrowsePage'))
const InstitutionPage = lazy(() => import('./pages/public/InstitutionPage'))
const ProgramDetailPage = lazy(() => import('./pages/public/ProgramDetailPage'))
const ClaudeApiGoalPage = lazy(() => import('./pages/public/ClaudeApiGoalPage'))
const GoalHubPage = lazy(() => import('./pages/public/GoalHubPage'))
const BuildRoadmapPage = lazy(() => import('./pages/public/BuildRoadmapPage'))
const FeatureBacklogPage = lazy(() => import('./pages/public/FeatureBacklogPage'))
const ApiContractPage = lazy(() => import('./pages/public/ApiContractPage'))
const DataModelPage = lazy(() => import('./pages/public/DataModelPage'))
const AcceptancePage = lazy(() => import('./pages/public/AcceptancePage'))
const ExperienceStandardsPage = lazy(() => import('./pages/public/ExperienceStandardsPage'))
const FrontendStandardsPage = lazy(() => import('./pages/public/FrontendStandardsPage'))
const MlCorePage = lazy(() => import('./pages/public/MlCorePage'))
const ProductionReadinessPage = lazy(() => import('./pages/public/ProductionReadinessPage'))
const SearchFeedRecsPage = lazy(() => import('./pages/public/SearchFeedRecsPage'))
const SecurityTrustPage = lazy(() => import('./pages/public/SecurityTrustPage'))
const RealtimeNotificationsPage = lazy(() => import('./pages/public/RealtimeNotificationsPage'))
const ChatbotEvalPage = lazy(() => import('./pages/public/ChatbotEvalPage'))
const EvalHarnessPage = lazy(() => import('./pages/public/EvalHarnessPage'))

// Student pages — Discover (Stage 1) is the student home; My Space rooms render
// inside the eager MySpaceShell.
const DiscoverHomePage = lazy(() => import('./pages/student/DiscoverHomePage'))
const ExplorePage = lazy(() => import('./pages/student/ExplorePage'))
const MySpaceHomePage = lazy(() => import('./pages/student/myspace/MySpaceHomePage'))
const ImportPage = lazy(() => import('./pages/student/myspace/ImportPage'))
const PrepPage = lazy(() => import('./pages/student/myspace/PrepPage'))
const MessagesRoom = lazy(() => import('./pages/student/myspace/MessagesRoom'))
const ApplicationsPage = lazy(() => import('./pages/student/ApplicationsPage'))
const CalendarPage = lazy(() => import('./pages/student/CalendarPage'))
const ProfilePage = lazy(() => import('./pages/student/ProfilePage'))
const StudentProgramDetailPage = lazy(() => import('./pages/student/ProgramDetailPage'))
const InstitutionDetailPage = lazy(() => import('./pages/student/InstitutionDetailPage'))
const SchoolSubunitPage = lazy(() => import('./pages/student/SchoolSubunitPage'))
const ApplicationDetailPage = lazy(() => import('./pages/student/ApplicationDetailPage'))
const SavedListPage = lazy(() => import('./pages/student/SavedListPage'))
const StudentSettingsPage = lazy(() => import('./pages/student/SettingsPage'))
const FeedbackInboxPage = lazy(() => import('./pages/student/FeedbackInboxPage'))
const OnboardingPage = lazy(() => import('./pages/student/OnboardingPage'))

// Institution pages
const DashboardPage = lazy(() => import('./pages/institution/DashboardPage'))
const SetupPage = lazy(() => import('./pages/institution/SetupPage'))
const ProgramsPage = lazy(() => import('./pages/institution/ProgramsPage'))
const ProgramEditorPage = lazy(() => import('./pages/institution/ProgramEditorPage'))
const StudentDetailPage = lazy(() => import('./pages/institution/StudentDetailPage'))
const InterviewsPage = lazy(() => import('./pages/institution/InterviewsPage'))
const SegmentsPage = lazy(() => import('./pages/institution/SegmentsPage'))
const CampaignsPage = lazy(() => import('./pages/institution/CampaignsPage'))
const EventsPage = lazy(() => import('./pages/institution/EventsPage'))
const AnalyticsPage = lazy(() => import('./pages/institution/AnalyticsPage'))
const InstitutionSettingsPage = lazy(() => import('./pages/institution/SettingsPage'))
const DataUploadPage = lazy(() => import('./pages/institution/DataUploadPage'))
const PostsPage = lazy(() => import('./pages/institution/PostsPage'))
const InquiriesPage = lazy(() => import('./pages/institution/InquiriesPage'))
const PromotionsPage = lazy(() => import('./pages/institution/PromotionsPage'))
const AuditLogPage = lazy(() => import('./pages/institution/AuditLogPage'))
const TemplatesPage = lazy(() => import('./pages/institution/TemplatesPage'))
const CohortComparisonPage = lazy(() => import('./pages/institution/CohortComparisonPage'))
const IntakeRoundsPage = lazy(() => import('./pages/institution/IntakeRoundsPage'))
const RequirementsChecklistPage = lazy(() => import('./pages/institution/RequirementsChecklistPage'))
const AdmissionsPage = lazy(() => import('./pages/institution/AdmissionsPage'))
const OutreachPage = lazy(() => import('./pages/institution/OutreachPage'))
const CommunicationsPage = lazy(() => import('./pages/institution/CommunicationsPage'))
const RecruitmentPage = lazy(() => import('./pages/institution/RecruitmentPage'))
const DepartmentPortalPage = lazy(() => import('./pages/institution/graduate/DepartmentPortalPage'))

const NotFoundPage = lazy(() => import('./pages/system/NotFoundPage'))

// Per-route Suspense boundary: the fallback (a fixed 2px top progress bar)
// replaces only the page slot, never the surrounding layout/nav.
const page = (node: ReactNode) => <Suspense fallback={<PageLoader />}>{node}</Suspense>

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 5 * 60 * 1000, retry: 1, refetchOnWindowFocus: false },
  },
})

// Legacy redirects that must preserve the route param (Spec/04 §4.4, /90 G-A1/G-A6).
function LegacySchoolRedirect() {
  const { programId } = useParams()
  return <Navigate to={`/s/programs/${programId}`} replace />
}

function LegacyMessageRedirect() {
  const { convId } = useParams()
  return <Navigate to={`/s/messages?thread=${convId}`} replace />
}

// /s/manage retired (Spec 2026-06-10 §2) — param-preserving redirects into the
// My Space rooms. Bare /s/manage lands on mission control; tab deep links keep
// their remaining params (?thread, ?program, ?view…).
function ManageRedirect() {
  const [params] = useSearchParams()
  const tab = params.get('tab')
  const rest = new URLSearchParams(params)
  rest.delete('tab')
  const TARGETS: Record<string, string> = {
    applications: '/s/applications',
    calendar: '/s/calendar',
    messages: '/s/messages',
    prompts: '/s/prep?tab=prompts',
    workshops: '/s/prep?tab=workshops',
  }
  const base = tab ? TARGETS[tab] ?? '/s/space' : '/s/space'
  const qs = rest.toString()
  const sep = base.includes('?') ? '&' : '?'
  return <Navigate to={qs ? `${base}${sep}${qs}` : base} replace />
}

// /s/posts retired (Spec 2026-06-12) — Connect merged into the Discover hub.
// One hop, tab-mapping per POSTS_TAB_REDIRECTS.
function PostsRedirect() {
  const [params] = useSearchParams()
  const tab = params.get('tab')
  const target = (tab && POSTS_TAB_REDIRECTS[tab]) || '/s/explore?tab=updates'
  return <Navigate to={target} replace />
}

// /pricing + /about moved to the marketing site (unipaith.co). Preserve the
// previously-public app URLs by redirecting there rather than dropping them
// to a 404 (PR #265 review).
function ExternalRedirect({ to }: { to: string }) {
  useEffect(() => {
    window.location.replace(to)
  }, [to])
  return null
}

const router = createBrowserRouter([
  // Root → login (marketing site is at unipaith.co; this is the app at app.unipaith.co)
  { path: '/', element: <Navigate to="/login" replace />, errorElement: <RouteErrorPage /> },

  // Public program browsing (linked from marketing-site CTAs)
  { path: '/browse', element: <PublicLayout>{page(<ProgramBrowsePage />)}</PublicLayout>, errorElement: <RouteErrorPage /> },
  { path: '/school/:institutionId', element: <PublicLayout>{page(<InstitutionPage />)}</PublicLayout>, errorElement: <RouteErrorPage /> },
  { path: '/school/:institutionId/schools/:schoolId', element: <PublicLayout>{page(<SchoolSubunitPage isAuthenticated={false} />)}</PublicLayout>, errorElement: <RouteErrorPage /> },
  { path: '/program/:programId', element: <PublicLayout>{page(<ProgramDetailPage />)}</PublicLayout>, errorElement: <RouteErrorPage /> },
  // Spec 07 pricing/about now live on the marketing site (unipaith.co); preserve
  // the public app URLs by redirecting there rather than 404ing (PR #265 review).
  { path: '/pricing', element: <ExternalRedirect to="https://unipaith.co/pricing" />, errorElement: <RouteErrorPage /> },
  { path: '/about', element: <ExternalRedirect to="https://unipaith.co/about" />, errorElement: <RouteErrorPage /> },
  // Specs 48/49/50 — public build-transparency hub + surfaces (live data).
  { path: '/goal', element: <PublicLayout>{page(<GoalHubPage />)}</PublicLayout>, errorElement: <RouteErrorPage /> },
  // Spec 45 — public "Claude API" AI-agent transparency surface (live registry).
  { path: '/goal/claude-api', element: <PublicLayout>{page(<ClaudeApiGoalPage />)}</PublicLayout>, errorElement: <RouteErrorPage /> },
  // Spec 48 — phased build roadmap.
  { path: '/goal/roadmap', element: <PublicLayout>{page(<BuildRoadmapPage />)}</PublicLayout>, errorElement: <RouteErrorPage /> },
  // Spec 49 — Feature-List V1 coverage map.
  { path: '/goal/features', element: <PublicLayout>{page(<FeatureBacklogPage />)}</PublicLayout>, errorElement: <RouteErrorPage /> },
  // Spec 50 — front↔back API contract (router map read live from the routes).
  { path: '/goal/api', element: <PublicLayout>{page(<ApiContractPage />)}</PublicLayout>, errorElement: <RouteErrorPage /> },
  // Spec 51 — persisted data model (table map introspected live from the models).
  { path: '/goal/data-model', element: <PublicLayout>{page(<DataModelPage />)}</PublicLayout>, errorElement: <RouteErrorPage /> },
  // Spec 52 — MVP acceptance & runbook (readiness read live from the running system).
  { path: '/goal/acceptance', element: <PublicLayout>{page(<AcceptancePage />)}</PublicLayout>, errorElement: <RouteErrorPage /> },
  // Spec 53 — UX benchmark & interaction standards (per-surface backing read live).
  { path: '/goal/experience', element: <PublicLayout>{page(<ExperienceStandardsPage />)}</PublicLayout>, errorElement: <RouteErrorPage /> },
  // Spec 54 — frontend engineering build spec (api↔router parity read live).
  { path: '/goal/frontend', element: <PublicLayout>{page(<FrontendStandardsPage />)}</PublicLayout>, errorElement: <RouteErrorPage /> },
  // Spec 55 — backend production readiness (config / middleware / health read live).
  { path: '/goal/backend', element: <PublicLayout>{page(<ProductionReadinessPage />)}</PublicLayout>, errorElement: <RouteErrorPage /> },
  // Spec 56 — search / feed / recommendations substrate (routes / flags / table read live).
  { path: '/goal/search', element: <PublicLayout>{page(<SearchFeedRecsPage />)}</PublicLayout>, errorElement: <RouteErrorPage /> },
  // Spec 57 — realtime & notifications (SSE/WS routes, event catalog, broker read live).
  { path: '/goal/realtime', element: <PublicLayout>{page(<RealtimeNotificationsPage />)}</PublicLayout>, errorElement: <RouteErrorPage /> },
  // Spec 61 — chatbot training & evaluation loop (constitution / safety floor / eval suites read live).
  { path: '/goal/chatbot-eval', element: <PublicLayout>{page(<ChatbotEvalPage />)}</PublicLayout>, errorElement: <RouteErrorPage /> },
  // Spec 62 — shared evaluation harness (consumers / golden sets / judge / modes / tables read live).
  { path: '/goal/eval-harness', element: <PublicLayout>{page(<EvalHarnessPage />)}</PublicLayout>, errorElement: <RouteErrorPage /> },
  // Spec 58 — security, trust & compliance posture (controls / consent / PII / headers read live).
  { path: '/goal/security', element: <PublicLayout>{page(<SecurityTrustPage />)}</PublicLayout>, errorElement: <RouteErrorPage /> },
  // Spec 63 — ML core & knowledge processing (the Qwen↔Claude boundary, read live from the routing layer).
  { path: '/goal/ml-core', element: <PublicLayout>{page(<MlCorePage />)}</PublicLayout>, errorElement: <RouteErrorPage /> },

  { path: '/login', element: <AuthLayout>{page(<LoginPage />)}</AuthLayout>, errorElement: <RouteErrorPage /> },
  { path: '/signup', element: <AuthLayout>{page(<SignupPage />)}</AuthLayout>, errorElement: <RouteErrorPage /> },
  { path: '/auth/callback', element: page(<AuthCallbackPage />), errorElement: <RouteErrorPage /> },
  { path: '/onboarding', element: <RequireAuth role="student">{page(<OnboardingPage />)}</RequireAuth>, errorElement: <RouteErrorPage /> },

  // Student routes
  {
    path: '/s',
    element: <RequireAuth role="student"><StudentLayout /></RequireAuth>,
    errorElement: <RouteErrorPage />,
    children: [
      // === 4 Main Pages ===
      { index: true, element: page(<DiscoverHomePage />) },          // Stage 1 — Discovery
      // /s/posts retired (Spec 2026-06-12) — Connect lives in the Discover hub tabs.
      { path: 'posts', element: <PostsRedirect /> },
      { path: 'explore', element: page(<ExplorePage />) },            // Discover hub (match + connect)
      // Messages — own top-level surface (Spec 2026-06-15): a peer of My Space in
      // the nav, so it renders full-width WITHOUT the My Space rail.
      { path: 'messages', element: page(<MessagesRoom />) },
      // === My Space (Spec 2026-06-10; rail tree 2026-06-15) — mission-control home + rooms ===
      {
        element: <MySpaceShell />,
        children: [
          { path: 'space', element: page(<MySpaceHomePage />) },        // Overview — mission control
          { path: 'import', element: page(<ImportPage />) },            // Import — upload → review → gaps
          { path: 'saved', element: page(<SavedListPage />) },          // Collections
          { path: 'prep', element: page(<PrepPage />) },                // Workspace
          { path: 'applications', element: page(<ApplicationsPage />) }, // Workspace
          { path: 'calendar', element: page(<CalendarPage />) },        // Workspace
          { path: 'profile', element: page(<ProfilePage />) },          // Record
        ],
      },
      { path: 'settings', element: page(<StudentSettingsPage />) },
      // Owner-only in-app feedback inbox (gated server-side by the email allowlist).
      { path: 'feedback', element: page(<FeedbackInboxPage />) },
      // === Drill-down pages ===
      { path: 'programs/:programId', element: page(<StudentProgramDetailPage />) },
      // Legacy alias — /s/schools/:id was the same page; redirect to the canonical
      // program route (Spec/90 G-A1).
      { path: 'schools/:programId', element: <LegacySchoolRedirect /> },
      { path: 'institutions/:institutionId', element: page(<InstitutionDetailPage />) },
      { path: 'institutions/:institutionId/schools/:schoolId', element: page(<SchoolSubunitPage />) },
      { path: 'applications/:appId', element: page(<ApplicationDetailPage />) },
      // === Redirects (all old routes still work) ===
      // /s/manage retired — tab deep links map into the My Space rooms.
      { path: 'manage', element: <ManageRedirect /> },
      { path: 'dashboard', element: <Navigate to="/s/space" replace /> },
      { path: 'chat', element: <Navigate to="/s" replace /> },
      { path: 'discover', element: <Navigate to="/s/explore" replace /> },
      { path: 'match', element: <Navigate to="/s" replace /> },
      { path: 'deadlines', element: <Navigate to="/s/calendar" replace /> },
      { path: 'messages/:convId', element: <LegacyMessageRedirect /> },
      { path: 'financial-aid', element: <Navigate to="/s/applications?tab=costs" replace /> },
      { path: 'recommendations', element: <Navigate to="/s/prep?tab=recommenders" replace /> },
      // Phase D — workshops live in My Space › Prep (feedback-only).
      { path: 'resume-workshop', element: <Navigate to="/s/prep?tab=workshops" replace /> },
      { path: 'essay-workshop', element: <Navigate to="/s/prep?tab=workshops" replace /> },
      // Spec 42 — Prompt Library deep-link → Prep › Prompts.
      { path: 'prompts', element: <Navigate to="/s/prep?tab=prompts" replace /> },
      { path: 'test-scores', element: <Navigate to="/s/profile?tab=academics" replace /> },
      { path: 'decisions', element: <Navigate to="/s/applications" replace /> },
      { path: 'intake', element: <Navigate to="/s" replace /> },
      { path: 'intelligence', element: <Navigate to="/s" replace /> },
    ],
  },

  // Institution routes
  {
    path: '/i',
    element: <RequireAuth role="institution_admin"><InstitutionLayout /></RequireAuth>,
    errorElement: <RouteErrorPage />,
    children: [
      { index: true, element: <Navigate to="/i/dashboard" replace /> },
      { path: 'dashboard', element: page(<DashboardPage />) },
      { path: 'setup', element: page(<SetupPage />) },
      // Unified pages
      { path: 'programs', element: page(<ProgramsPage />) },
      { path: 'programs/new', element: page(<ProgramEditorPage />) },
      { path: 'programs/:id/edit', element: page(<ProgramEditorPage />) },
      { path: 'admissions', element: page(<AdmissionsPage />) },
      { path: 'admissions/applicant/:appId', element: page(<StudentDetailPage />) },
      { path: 'recruitment', element: page(<RecruitmentPage />) },
      // Spec 41 — graduate department review portal (scoped review + faculty + funding)
      { path: 'departments/:deptId', element: page(<DepartmentPortalPage />) },
      { path: 'outreach', element: page(<OutreachPage />) },
      { path: 'communications', element: page(<CommunicationsPage />) },
      // Spec 31 — legacy pipeline URLs redirect into admissions intake
      { path: 'pipeline', element: <LegacyPipelineRedirect /> },
      { path: 'pipeline/:studentId', element: <LegacyApplicantRedirect /> },
      { path: 'interviews', element: page(<InterviewsPage />) },
      { path: 'messages', element: <Navigate to="/i/communications?tab=inbox" replace /> },
      { path: 'segments', element: page(<SegmentsPage />) },
      { path: 'campaigns', element: page(<CampaignsPage />) },
      { path: 'events', element: page(<EventsPage />) },
      { path: 'posts', element: page(<PostsPage />) },
      { path: 'inquiries', element: page(<InquiriesPage />) },
      { path: 'promotions', element: page(<PromotionsPage />) },
      { path: 'audit-log', element: page(<AuditLogPage />) },
      { path: 'templates', element: page(<TemplatesPage />) },
      { path: 'cohort-compare', element: page(<CohortComparisonPage />) },
      { path: 'intake-rounds', element: page(<IntakeRoundsPage />) },
      { path: 'requirements', element: page(<RequirementsChecklistPage />) },
      { path: 'analytics', element: page(<AnalyticsPage />) },
      { path: 'data', element: page(<DataUploadPage />) },
      { path: 'settings', element: page(<InstitutionSettingsPage />) },
    ],
  },

  // Catch-all → login
  { path: '*', element: page(<NotFoundPage />), errorElement: <RouteErrorPage /> },
])

export default function App() {
  const loadSession = useAuthStore(s => s.loadSession)

  useEffect(() => {
    loadSession()
  }, [loadSession])

  return (
    <QueryClientProvider client={queryClient}>
      <AppErrorBoundary>
        <RouterProvider router={router} />
        <ToastContainer />
        <ConfirmHost />
        <DemoNotice />
        <FeedbackWidget />
      </AppErrorBoundary>
    </QueryClientProvider>
  )
}
