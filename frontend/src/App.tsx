import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom'
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

// Auth pages
import LandingPage from './pages/auth/LandingPage'
import LoginPage from './pages/auth/LoginPage'
import SignupPage from './pages/auth/SignupPage'
import AuthCallbackPage from './pages/auth/AuthCallbackPage'

// Public pages
import ProgramBrowsePage from './pages/public/ProgramBrowsePage'
import InstitutionPage from './pages/public/InstitutionPage'
import ProgramDetailPage from './pages/public/ProgramDetailPage'
import ForStudentsPage from './pages/public/ForStudentsPage'
import ForInstitutionsPage from './pages/public/ForInstitutionsPage'
import EnginePage from './pages/public/EnginePage'
import PricingPage from './pages/public/PricingPage'
import AboutPage from './pages/public/AboutPage'
import BlogPage from './pages/public/BlogPage'
import PublicLayout from './components/layout/PublicLayout'

// Student pages
import StudentDashboardPage from './pages/student/DashboardPage'
import ChatPage from './pages/student/ChatPage'
import ProfilePage from './pages/student/ProfilePage'
import DiscoverPage from './pages/student/DiscoverPage'
import SchoolDetailPage from './pages/student/SchoolDetailPage'
import ApplicationsPage from './pages/student/ApplicationsPage'
import ApplicationDetailPage from './pages/student/ApplicationDetailPage'
import SavedListPage from './pages/student/SavedListPage'
import MessagesPage from './pages/student/MessagesPage'
import CalendarPage from './pages/student/CalendarPage'
// DeadlinesPage merged into CalendarPage as timeline view
import FinancialAidPage from './pages/student/FinancialAidPage'
import RecommendationsPage from './pages/student/RecommendationsPage'
import StudentSettingsPage from './pages/student/SettingsPage'
import ResumeWorkshopPage from './pages/student/ResumeWorkshopPage'
import EssayWorkshopPage from './pages/student/EssayWorkshopPage'
import DecisionComparisonPage from './pages/student/DecisionComparisonPage'
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

// Admin pages
import AdminLayout from './components/layout/AdminLayout'
import AdminDashboardPage from './pages/admin/AdminDashboardPage'
import AdminUsersPage from './pages/admin/AdminUsersPage'
import AdminSystemPage from './pages/admin/AdminSystemPage'
import AdminAICenterPage from './pages/admin/AdminAICenterPage'
import AdminCrawlerDashboardPage from './pages/admin/AdminCrawlerDashboardPage'
import RouteErrorPage from './pages/system/RouteErrorPage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 5 * 60 * 1000, retry: 1, refetchOnWindowFocus: false },
  },
})

const router = createBrowserRouter([
  // Public routes
  { path: '/', element: <LandingPage />, errorElement: <RouteErrorPage /> },
  { path: '/browse', element: <ProgramBrowsePage />, errorElement: <RouteErrorPage /> },
  { path: '/school/:institutionId', element: <InstitutionPage />, errorElement: <RouteErrorPage /> },
  { path: '/program/:programId', element: <ProgramDetailPage />, errorElement: <RouteErrorPage /> },

  // Marketing pages (with shared Navbar + Footer via PublicLayout)
  {
    element: <PublicLayout />,
    errorElement: <RouteErrorPage />,
    children: [
      { path: '/for-students', element: <ForStudentsPage /> },
      { path: '/for-institutions', element: <ForInstitutionsPage /> },
      { path: '/engine', element: <EnginePage /> },
      { path: '/pricing', element: <PricingPage /> },
      { path: '/about', element: <AboutPage /> },
      { path: '/blog', element: <BlogPage /> },
    ],
  },

  { path: '/login', element: <AuthLayout><LoginPage /></AuthLayout>, errorElement: <RouteErrorPage /> },
  { path: '/signup', element: <AuthLayout><SignupPage /></AuthLayout>, errorElement: <RouteErrorPage /> },
  { path: '/auth/callback', element: <AuthCallbackPage />, errorElement: <RouteErrorPage /> },
  { path: '/onboarding', element: <OnboardingPage />, errorElement: <RouteErrorPage /> },

  // Student routes
  {
    path: '/s',
    element: <RequireAuth role="student"><StudentLayout /></RequireAuth>,
    errorElement: <RouteErrorPage />,
    children: [
      { index: true, element: <Navigate to="/s/dashboard" replace /> },
      { path: 'dashboard', element: <StudentDashboardPage /> },
      { path: 'chat', element: <ChatPage /> },
      { path: 'profile', element: <ProfilePage /> },
      { path: 'match', element: <Navigate to="/s/discover?mode=match" replace /> },
      { path: 'discover', element: <DiscoverPage /> },
      { path: 'programs/:programId', element: <SchoolDetailPage /> },
      { path: 'schools/:programId', element: <SchoolDetailPage /> },
      { path: 'applications', element: <ApplicationsPage /> },
      { path: 'applications/:appId', element: <ApplicationDetailPage /> },
      { path: 'saved', element: <SavedListPage /> },
      { path: 'messages', element: <MessagesPage /> },
      { path: 'messages/:convId', element: <MessagesPage /> },
      { path: 'calendar', element: <CalendarPage /> },
      { path: 'deadlines', element: <Navigate to="/s/calendar?view=agenda" replace /> },
      { path: 'financial-aid', element: <FinancialAidPage /> },
      { path: 'recommendations', element: <RecommendationsPage /> },
      { path: 'resume-workshop', element: <ResumeWorkshopPage /> },
      { path: 'essay-workshop', element: <EssayWorkshopPage /> },
      { path: 'test-scores', element: <Navigate to="/s/profile" replace /> },
      { path: 'decisions', element: <DecisionComparisonPage /> },
      { path: 'intake', element: <Navigate to="/s/chat" replace /> },
      { path: 'intelligence', element: <Navigate to="/s/dashboard" replace /> },
      { path: 'settings', element: <StudentSettingsPage /> },
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
      { path: 'pipeline/:appId', element: <StudentDetailPage /> },
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

  // Admin routes
  {
    path: '/admin',
    element: <RequireAuth role="admin"><AdminLayout /></RequireAuth>,
    errorElement: <RouteErrorPage />,
    children: [
      { index: true, element: <Navigate to="/admin/overview" replace /> },
      { path: 'overview', element: <AdminDashboardPage /> },
      { path: 'users', element: <AdminUsersPage /> },
      { path: 'ai', element: <AdminAICenterPage /> },
      { path: 'system', element: <AdminSystemPage /> },
      // Legacy redirects — keep bookmarks working
      { path: 'ops', element: <Navigate to="/admin/ai?tab=pipeline" replace /> },
      { path: 'crawler', element: <AdminCrawlerDashboardPage /> },
      { path: 'ml', element: <Navigate to="/admin/ai?tab=learning" replace /> },
      { path: 'knowledge', element: <Navigate to="/admin/ai?tab=knowledge" replace /> },
    ],
  },

  // Catch-all
  { path: '*', element: <Navigate to="/" replace />, errorElement: <RouteErrorPage /> },
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
