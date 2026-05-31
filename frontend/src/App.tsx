import { createBrowserRouter, RouterProvider, Navigate, useParams } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useEffect } from 'react'
import { useAuthStore } from './stores/auth-store'
import ToastContainer from './components/ui/Toast'
import AppErrorBoundary from './components/system/AppErrorBoundary'

// Layouts
import AuthLayout from './components/layout/AuthLayout'
import StudentLayout from './components/layout/StudentLayout'
import InstitutionLayout from './components/layout/InstitutionLayout'
import RequireAuth from './components/layout/RequireAuth'
import PublicLayout from './components/layout/PublicLayout'

// Auth pages
import LoginPage from './pages/auth/LoginPage'
import SignupPage from './pages/auth/SignupPage'
import AuthCallbackPage from './pages/auth/AuthCallbackPage'

// Public pages (program browsing — linked from the marketing site at unipaith.co)
import ProgramBrowsePage from './pages/public/ProgramBrowsePage'
import InstitutionPage from './pages/public/InstitutionPage'
import ProgramDetailPage from './pages/public/ProgramDetailPage'
import PricingPage from './pages/public/PricingPage'
import AboutPage from './pages/public/AboutPage'

// Student pages — 4 main + profile/saved/settings from avatar
// Discover (Stage 1) is the new student home — replaces CounselorHomePage
// per the Phase B Discover-page rebuild. Track-segmented journey + chat
// + artifact rail.
import DiscoverHomePage from './pages/student/DiscoverHomePage'
import StudentPostsPage from './pages/student/PostsPage'
import ExplorePage from './pages/student/ExplorePage'
import ManagementPage from './pages/student/ManagementPage'
import ProfilePage from './pages/student/ProfilePage'
import StudentProgramDetailPage from './pages/student/ProgramDetailPage'
import InstitutionDetailPage from './pages/student/InstitutionDetailPage'
import SchoolSubunitPage from './pages/student/SchoolSubunitPage'
import ApplicationDetailPage from './pages/student/ApplicationDetailPage'
import SavedListPage from './pages/student/SavedListPage'
import StudentSettingsPage from './pages/student/SettingsPage'
import OnboardingPage from './pages/student/OnboardingPage'

// Institution pages
import DashboardPage from './pages/institution/DashboardPage'
import SetupPage from './pages/institution/SetupPage'
import ProgramsPage from './pages/institution/ProgramsPage'
import ProgramEditorPage from './pages/institution/ProgramEditorPage'
import PipelinePage from './pages/institution/PipelinePage'
import StudentDetailPage from './pages/institution/StudentDetailPage'
import InterviewsPage from './pages/institution/InterviewsPage'
import InstitutionMessagingPage from './pages/institution/MessagingPage'
import SegmentsPage from './pages/institution/SegmentsPage'
import CampaignsPage from './pages/institution/CampaignsPage'
import EventsPage from './pages/institution/EventsPage'
import AnalyticsPage from './pages/institution/AnalyticsPage'
import InstitutionSettingsPage from './pages/institution/SettingsPage'
import DataUploadPage from './pages/institution/DataUploadPage'
import PostsPage from './pages/institution/PostsPage'
import InquiriesPage from './pages/institution/InquiriesPage'
import PromotionsPage from './pages/institution/PromotionsPage'
import AuditLogPage from './pages/institution/AuditLogPage'
import TemplatesPage from './pages/institution/TemplatesPage'
import CohortComparisonPage from './pages/institution/CohortComparisonPage'
import IntakeRoundsPage from './pages/institution/IntakeRoundsPage'
import RequirementsChecklistPage from './pages/institution/RequirementsChecklistPage'
import AdmissionsPage from './pages/institution/AdmissionsPage'
import OutreachPage from './pages/institution/OutreachPage'
import CommunicationsPage from './pages/institution/CommunicationsPage'

import RouteErrorPage from './pages/system/RouteErrorPage'

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
  return <Navigate to={`/s/manage?tab=messages&thread=${convId}`} replace />
}

const router = createBrowserRouter([
  // Root → login (marketing site is at unipaith.co; this is the app at app.unipaith.co)
  { path: '/', element: <Navigate to="/login" replace />, errorElement: <RouteErrorPage /> },

  // Public program browsing (linked from marketing-site CTAs)
  { path: '/browse', element: <PublicLayout><ProgramBrowsePage /></PublicLayout>, errorElement: <RouteErrorPage /> },
  { path: '/school/:institutionId', element: <PublicLayout><InstitutionPage /></PublicLayout>, errorElement: <RouteErrorPage /> },
  { path: '/school/:institutionId/schools/:schoolId', element: <PublicLayout><SchoolSubunitPage isAuthenticated={false} /></PublicLayout>, errorElement: <RouteErrorPage /> },
  { path: '/program/:programId', element: <PublicLayout><ProgramDetailPage /></PublicLayout>, errorElement: <RouteErrorPage /> },
  // Spec 07 — public monetization + positioning surfaces.
  { path: '/pricing', element: <PublicLayout><PricingPage /></PublicLayout>, errorElement: <RouteErrorPage /> },
  { path: '/about', element: <PublicLayout><AboutPage /></PublicLayout>, errorElement: <RouteErrorPage /> },

  { path: '/login', element: <AuthLayout><LoginPage /></AuthLayout>, errorElement: <RouteErrorPage /> },
  { path: '/signup', element: <AuthLayout><SignupPage /></AuthLayout>, errorElement: <RouteErrorPage /> },
  { path: '/auth/callback', element: <AuthCallbackPage />, errorElement: <RouteErrorPage /> },
  { path: '/onboarding', element: <RequireAuth role="student"><OnboardingPage /></RequireAuth>, errorElement: <RouteErrorPage /> },

  // Student routes
  {
    path: '/s',
    element: <RequireAuth role="student"><StudentLayout /></RequireAuth>,
    errorElement: <RouteErrorPage />,
    children: [
      // === 4 Main Pages ===
      { index: true, element: <DiscoverHomePage /> },          // Stage 1 — Discovery
      { path: 'posts', element: <StudentPostsPage /> },           // Posts (social feed)
      { path: 'explore', element: <ExplorePage /> },            // Explore (database)
      { path: 'manage', element: <ManagementPage /> },          // Management (apps/cal/msg)
      // === Avatar dropdown pages ===
      { path: 'profile', element: <ProfilePage /> },
      { path: 'saved', element: <SavedListPage /> },
      { path: 'settings', element: <StudentSettingsPage /> },
      // === Drill-down pages ===
      { path: 'programs/:programId', element: <StudentProgramDetailPage /> },
      // Legacy alias — /s/schools/:id was the same page; redirect to the canonical
      // program route (Spec/90 G-A1).
      { path: 'schools/:programId', element: <LegacySchoolRedirect /> },
      { path: 'institutions/:institutionId', element: <InstitutionDetailPage /> },
      { path: 'institutions/:institutionId/schools/:schoolId', element: <SchoolSubunitPage /> },
      { path: 'applications/:appId', element: <ApplicationDetailPage /> },
      // === Redirects (all old routes still work) ===
      { path: 'dashboard', element: <Navigate to="/s" replace /> },
      { path: 'chat', element: <Navigate to="/s" replace /> },
      { path: 'discover', element: <Navigate to="/s/explore" replace /> },
      { path: 'match', element: <Navigate to="/s" replace /> },
      { path: 'applications', element: <Navigate to="/s/manage" replace /> },
      { path: 'calendar', element: <Navigate to="/s/manage?tab=calendar" replace /> },
      { path: 'deadlines', element: <Navigate to="/s/manage?tab=calendar" replace /> },
      { path: 'messages', element: <Navigate to="/s/manage?tab=messages" replace /> },
      { path: 'messages/:convId', element: <LegacyMessageRedirect /> },
      { path: 'financial-aid', element: <Navigate to="/s/profile?tab=financial" replace /> },
      { path: 'recommendations', element: <Navigate to="/s/profile?tab=preparation&section=recommenders" replace /> },
      // Phase D — Workshops moved from Profile to Apply > Workshops (feedback-only).
      { path: 'resume-workshop', element: <Navigate to="/s/manage?tab=workshops" replace /> },
      { path: 'essay-workshop', element: <Navigate to="/s/manage?tab=workshops" replace /> },
      { path: 'test-scores', element: <Navigate to="/s/profile?tab=academics" replace /> },
      { path: 'decisions', element: <Navigate to="/s/manage" replace /> },
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
      { path: 'dashboard', element: <DashboardPage /> },
      { path: 'setup', element: <SetupPage /> },
      // Unified pages
      { path: 'programs', element: <ProgramsPage /> },
      { path: 'programs/new', element: <ProgramEditorPage /> },
      { path: 'programs/:id/edit', element: <ProgramEditorPage /> },
      { path: 'admissions', element: <AdmissionsPage /> },
      { path: 'outreach', element: <OutreachPage /> },
      { path: 'communications', element: <CommunicationsPage /> },
      // Legacy routes (still work via direct URL)
      { path: 'pipeline', element: <PipelinePage /> },
      { path: 'pipeline/:studentId', element: <StudentDetailPage /> },
      { path: 'interviews', element: <InterviewsPage /> },
      { path: 'messages', element: <InstitutionMessagingPage /> },
      { path: 'segments', element: <SegmentsPage /> },
      { path: 'campaigns', element: <CampaignsPage /> },
      { path: 'events', element: <EventsPage /> },
      { path: 'posts', element: <PostsPage /> },
      { path: 'inquiries', element: <InquiriesPage /> },
      { path: 'promotions', element: <PromotionsPage /> },
      { path: 'audit-log', element: <AuditLogPage /> },
      { path: 'templates', element: <TemplatesPage /> },
      { path: 'cohort-compare', element: <CohortComparisonPage /> },
      { path: 'intake-rounds', element: <IntakeRoundsPage /> },
      { path: 'requirements', element: <RequirementsChecklistPage /> },
      { path: 'analytics', element: <AnalyticsPage /> },
      { path: 'data', element: <DataUploadPage /> },
      { path: 'settings', element: <InstitutionSettingsPage /> },
    ],
  },

  // Catch-all → login
  { path: '*', element: <Navigate to="/login" replace />, errorElement: <RouteErrorPage /> },
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
      </AppErrorBoundary>
    </QueryClientProvider>
  )
}
