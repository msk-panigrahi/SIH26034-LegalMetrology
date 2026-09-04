/**
 * LegalMetriX — Main App with routing and route guards.
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Layout from './components/Layout/Layout';
import LandingPage from './pages/LandingPage';
import Login from './pages/Login';
import Register from './pages/Register';
import InspectorDashboard from './pages/InspectorDashboard';
import NewInspection from './pages/NewInspection';
import InspectionHistory from './pages/InspectionHistory';
import InspectionDetail from './pages/InspectionDetail';
import ReportViewer from './pages/ReportViewer';
import AdminDashboard from './pages/AdminDashboard';
import AdminInspections from './pages/AdminInspections';
import LoadingSkeleton from './components/UI/LoadingSkeleton';
import './App.css';

function ProtectedRoute({ children, allowedRoles }) {
  const { isAuthenticated, user, loading } = useAuth();

  if (loading) {
    return (
      <div className="app-loading">
        <LoadingSkeleton cards={2} rows={3} />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user?.role)) {
    return <Navigate to={user?.role === 'ADMIN' ? '/admin/dashboard' : '/inspector/dashboard'} replace />;
  }

  return <Layout>{children}</Layout>;
}

function AppRoutes() {
  const { isAuthenticated, user, loading } = useAuth();

  if (loading) {
    return (
      <div className="app-loading">
        <div className="loading-text">Loading LegalMetriX...</div>
      </div>
    );
  }

  // Unauthenticated routes
  if (!isAuthenticated) {
    return (
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    );
  }

  // Determine default redirect based on role
  const defaultPath = user?.role === 'ADMIN' ? '/admin/dashboard' : '/inspector/dashboard';

  return (
      <Routes>
        {/* Public (but authenticated) */}
        <Route path="/" element={<Navigate to={defaultPath} replace />} />
        <Route path="/login" element={<Navigate to={defaultPath} replace />} />
        <Route path="/register" element={<Navigate to={defaultPath} replace />} />

        {/* Inspector Routes */}
        <Route
          path="/inspector/dashboard"
          element={
            <ProtectedRoute allowedRoles={['INSPECTOR']}>
              <InspectorDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/inspector/inspections/new"
          element={
            <ProtectedRoute allowedRoles={['INSPECTOR']}>
              <NewInspection />
            </ProtectedRoute>
          }
        />
        <Route
          path="/inspector/history"
          element={
            <ProtectedRoute allowedRoles={['INSPECTOR']}>
              <InspectionHistory />
            </ProtectedRoute>
          }
        />
        <Route
          path="/inspector/inspections/:id"
          element={
            <ProtectedRoute allowedRoles={['INSPECTOR', 'ADMIN']}>
              <InspectionDetail />
            </ProtectedRoute>
          }
        />
        <Route
          path="/inspector/inspections/:id/report"
          element={
            <ProtectedRoute allowedRoles={['INSPECTOR', 'ADMIN']}>
              <ReportViewer />
            </ProtectedRoute>
          }
        />

        {/* Admin Routes */}
        <Route
          path="/admin/dashboard"
          element={
            <ProtectedRoute allowedRoles={['ADMIN']}>
              <AdminDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/inspections"
          element={
            <ProtectedRoute allowedRoles={['ADMIN']}>
              <AdminInspections />
            </ProtectedRoute>
          }
        />

        {/* Default redirect */}
        <Route path="*" element={<Navigate to={defaultPath} replace />} />
      </Routes>
    );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}
