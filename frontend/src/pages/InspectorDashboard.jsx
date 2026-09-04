/**
 * Inspector Dashboard — statistics and recent inspections.
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import StatusBadge from '../components/UI/StatusBadge';
import LoadingSkeleton from '../components/UI/LoadingSkeleton';
import './Dashboard.css';

export default function InspectorDashboard() {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      const data = await api.get('/dashboard/inspector');
      setStats(data);
    } catch (err) {
      setError(err.message || 'Unable to load dashboard. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <LoadingSkeleton cards={5} />;

  if (error) {
    return (
      <div className="error-state">
        <h3>Unable to load dashboard</h3>
        <p>{error}</p>
        <button onClick={loadDashboard} className="retry-btn">Retry</button>
      </div>
    );
  }

  const greeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 17) return 'Good afternoon';
    return 'Good evening';
  };

  return (
    <div className="dashboard">
      <div className="page-header">
        <div>
          <h1 className="page-heading">{greeting()}, {user?.full_name?.split(' ')[0] || 'Inspector'}</h1>
          <p className="page-subheading">Overview of your inspection activity</p>
        </div>
        <Link to="/inspector/inspections/new" className="primary-btn">
          + New Inspection
        </Link>
      </div>

      <div className="stat-grid">
        <div className="stat-card stat-total">
          <span className="stat-icon">&#128202;</span>
          <div className="stat-info">
            <span className="stat-value">{stats.total_inspections}</span>
            <span className="stat-label">Total Inspections</span>
          </div>
        </div>
        <div className="stat-card stat-compliant">
          <span className="stat-icon">&#10003;</span>
          <div className="stat-info">
            <span className="stat-value">{stats.compliant}</span>
            <span className="stat-label">Compliant</span>
          </div>
        </div>
        <div className="stat-card stat-non-compliant">
          <span className="stat-icon">&#10005;</span>
          <div className="stat-info">
            <span className="stat-value">{stats.non_compliant}</span>
            <span className="stat-label">Non-Compliant</span>
          </div>
        </div>
        <div className="stat-card stat-review">
          <span className="stat-icon">&#9888;</span>
          <div className="stat-info">
            <span className="stat-value">{stats.review_required}</span>
            <span className="stat-label">Review Required</span>
          </div>
        </div>
        <div className="stat-card stat-incomplete">
          <span className="stat-icon">&#9675;</span>
          <div className="stat-info">
            <span className="stat-value">{stats.incomplete}</span>
            <span className="stat-label">Incomplete</span>
          </div>
        </div>
      </div>

      {/* OCR Confidence Card */}
      {stats.avg_ocr_confidence > 0 && (
        <div className="info-banner">
          <span className="info-banner-label">Average OCR Confidence:</span>
          <span className="info-banner-value">{stats.avg_ocr_confidence.toFixed(1)}%</span>
        </div>
      )}

      <div className="section-card">
        <div className="section-header">
          <h2 className="section-title">Recent Inspections</h2>
          <Link to="/inspector/history" className="view-all-link">View All &rarr;</Link>
        </div>

        {stats.recent_inspections && stats.recent_inspections.length > 0 ? (
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Product</th>
                <th>Date</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {stats.recent_inspections.map((insp) => (
                <tr key={insp.id}>
                  <td>
                    <Link to={`/inspector/inspections/${insp.id}`}>#{insp.id}</Link>
                  </td>
                  <td>{insp.product_name || insp.status || '—'}</td>
                  <td>{insp.created_at ? new Date(insp.created_at).toLocaleDateString() : '—'}</td>
                  <td>
                    <StatusBadge status={insp.overall_status || 'INCOMPLETE'} />
                  </td>
                  <td>
                    <Link to={`/inspector/inspections/${insp.id}`} className="view-link">
                      View Details
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="empty-state">
            <p>No inspections yet. Start your first inspection to see it here.</p>
            <Link to="/inspector/inspections/new" className="primary-btn">
              + New Inspection
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
