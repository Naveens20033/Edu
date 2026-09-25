import { Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from './auth/AuthContext.jsx'
import AttendancePage from './pages/AttendancePage.jsx'
import LoginPage from './pages/LoginPage.jsx'
import StudentHistoryPage from './pages/StudentHistoryPage.jsx'
import CorrectionQueuePage from './pages/CorrectionQueuePage.jsx'
import FacultyHistoryPage from './pages/FacultyHistoryPage.jsx'
import SessionDetailPage from './pages/SessionDetailPage.jsx'
import DashboardPage from './pages/DashboardPage.jsx'
import LowAttendancePage from './pages/LowAttendancePage.jsx'

function Protected({ children, roles }) {
  const { user, loading } = useAuth()
  if (loading) return <main className="app-loading">Loading your workspace…</main>
  if (!user) return <Navigate to="/login" replace />
  if (roles && !roles.includes(user.role) && !user.is_superuser) return <Navigate to="/login" replace />
  return children
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/dashboard" element={<Protected><DashboardPage /></Protected>} />
      <Route path="/reports/low-attendance" element={<Protected><LowAttendancePage /></Protected>} />
      <Route path="/attendance" element={<Protected roles={['FACULTY', 'ADMIN']}><AttendancePage /></Protected>} />
      <Route path="/attendance/history" element={<Protected roles={['FACULTY', 'ADMIN']}><FacultyHistoryPage /></Protected>} />
      <Route path="/attendance/sessions/:sessionId" element={<Protected roles={['FACULTY', 'ADMIN']}><SessionDetailPage /></Protected>} />
      <Route path="/student/history" element={<Protected roles={['STUDENT']}><StudentHistoryPage /></Protected>} />
      <Route path="/corrections" element={<Protected roles={['ADMIN']}><CorrectionQueuePage /></Protected>} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}

export default function App() {
  return <AuthProvider><AppRoutes /></AuthProvider>
}
