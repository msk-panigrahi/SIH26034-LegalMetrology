/**
 * Main application layout with sidebar navigation and header.
 */

import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import './Layout.css';

const inspectorLinks = [
  { to: '/inspector/dashboard', label: 'Dashboard', icon: '📊' },
  { to: '/inspector/inspections/new', label: 'New Inspection', icon: '📷' },
  { to: '/inspector/history', label: 'Inspection History', icon: '📋' },
];

const adminLinks = [
  { to: '/admin/dashboard', label: 'Dashboard', icon: '📊' },
  { to: '/admin/inspections', label: 'All Inspections', icon: '📋' },
];

export default function Layout({ children }) {
  const { user, logout, isAdmin } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const links = isAdmin ? adminLinks : inspectorLinks;

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-header">
          <span className="sidebar-logo">⚖</span>
          <div className="sidebar-brand">
            <span className="brand-name">LegalMetriX</span>
            <span className="brand-sub">Inspection Platform</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            >
              <span className="nav-icon">{link.icon}</span>
              <span className="nav-label">{link.label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="user-info">
            <div className="user-avatar">
              {user?.full_name?.charAt(0) || 'U'}
            </div>
            <div className="user-details">
              <span className="user-name">{user?.full_name}</span>
              <span className="user-role">{user?.role}</span>
            </div>
          </div>
          <button className="logout-btn" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </aside>

      <div className="main-area">
        <header className="topbar">
          <div className="topbar-left">
            <h1 className="page-title">LegalMetriX</h1>
          </div>
          <div className="topbar-right">
            <span className="topbar-user">{user?.full_name}</span>
          </div>
        </header>

        <main className="content">
          {children}
        </main>
      </div>
    </div>
  );
}
