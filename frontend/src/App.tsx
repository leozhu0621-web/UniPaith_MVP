import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useEffect } from 'react'
import { useAuthStore } from './stores/auth-store'
import ToastContainer from './components/ui/Toast'

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
import DeadlinesPage from './pages/student/DeadlinesPage'
import FinancialAidPage from './pages/student/FinancialAidPage'
import RecommendationsPage from './pages/student/RecommendationsPage'
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

// Admin pages
import AdminLayout from './components/layout/AdminLayout'
import AdminDashboardPage from './pages/admin/AdminDashboardPage'
import AdminUsersPage from './pages/admin/AdminUsersPage'
import AdminCrawlerPage from './pages/admin/AdminCrawlerPage'
import AdminMLPage from './pages/admin/AdminMLPage'
import AdminSystemPage from './pages/admin/AdminSystemPage'
import AdminOpsCenterPage from './pages/admin/AdminOpsCenterPage'

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
      { index: true, element: <Navigate to="/s/dashboard" replace /> },
      { path: 'dashboard', element: <StudentDashboardPage /> },
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
      { path: 'deadlines', element: <DeadlinesPage /> },
      { path: 'financial-aid', element: <FinancialAidPage /> },
      { path: 'recommendations', element: <RecommendationsPage /> },
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

  // Admin routes
  {
    path: '/admin',
    element: <RequireAuth role="admin"><AdminLayout /></RequireAuth>,
    children: [
      { index: true, element: <Navigate to="/admin/overview" replace /> },
      { path: 'ops', element: <AdminOpsCenterPage /> },
      { path: 'overview', element: <AdminDashboardPage /> },
      { path: 'users', element: <AdminUsersPage /> },
      { path: 'crawler', element: <AdminCrawlerPage /> },
      { path: 'ml', element: <AdminMLPage /> },
      { path: 'system', element: <AdminSystemPage /> },
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
      <ToastContainer />
    </QueryClientProvider>
  )
}
