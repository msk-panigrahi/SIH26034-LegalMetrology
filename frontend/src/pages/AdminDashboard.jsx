/**
 * Admin Dashboard — system-wide statistics and inspector activity.
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/client';
import StatusBadge from '../components/UI/StatusBadge';
import LoadingSkeleton from '../components/UI/LoadingSkeleton';
import './Dashboard.css';
import './AdminDashboard.css';

export default function AdminDashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      const data = await api.get('/dashboard/admin');
      setStats(data);
    } catch (err) {
      setError(err.message || 'Unable to load admin dashboard. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <LoadingSkeleton cards={7} />;

  if (error) {
    return (
      <div className="error-state">
        <h3>Unable to load admin dashboard</h3>
        <p>{error}</p>
        <button onClick={loadDashboard} className="retry-btn">Retry</button>
      </div>
    );
  }

  return (
    <div className="dashboard admin-dashboard">
      <div className="page-header">
        <div>
          <h1 className="page-heading">LegalMetriX Administration</h1>
          <p className="page-subheading">System-wide Legal Metrology Inspection Overview</p>
        </div>
      </div>

      {/* System Summary Cards */}
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

      <div className="stat-grid stat-grid-2">
        <div className="stat-card stat-total">
          <span className="stat-icon">&#128101;</span>
          <div className="stat-info">
            <span className="stat-value">{stats.total_inspectors}</span>
            <span className="stat-label">Total Inspectors</span>
          </div>
        </div>
        <div className="stat-card stat-compliant">
          <span className="stat-icon">&#9989;</span>
          <div className="stat-info">
            <span className="stat-value">{stats.active_inspectors}</span>
            <span className="stat-label">Active Inspectors</span>
          </div>
        </div>
        {stats.avg_ocr_confidence > 0 && (
          <div className="stat-card stat-review">
            <span className="stat-icon">&#128269;</span>
            <div className="stat-info">
              <span className="stat-value">{stats.avg_ocr_confidence.toFixed(1)}%</span>
              <span className="stat-label">Avg OCR Confidence</span>
            </div>
          </div>
        )}
      </div>

      {/* Inspector Statistics */}
      {stats.inspector_statistics && stats.inspector_statistics.length > 0 && (
        <div className="section-card">
          <div className="section-header">
            <h2 className="section-title">Inspector Activity</h2>
          </div>
          <table className="data-table">
            <thead>
              <tr>
                <th>Inspector</th>
                <th>Total</th>
                <th>Compliant</th>
                <th>Non-Compliant</th>
                <th>Review Required</th>
                <th>Incomplete</th>
                <th>Last Activity</th>
              </tr>
            </thead>
            <tbody>
              {stats.inspector_statistics.map((insp) => (
                <tr key={insp.inspector_id}>
                  <td><strong>{insp.name}</strong></td>
                  <td>{insp.total_inspections}</td>
                  <td>{insp.compliant}</td>
                  <td>{insp.non_compliant}</td>
                  <td>{insp.review_required}</td>
                  <td>{insp.incomplete || 0}</td>
                  <td>
                    {insp.last_inspection_at
                      ? new Date(insp.last_inspection_at).toLocaleDateString()
                      : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Recent Inspections */}
      {stats.recent_inspections && stats.recent_inspections.length > 0 && (
        <div className="section-card">
          <div className="section-header">
            <h2 className="section-title">Recent System Inspections</h2>
            <Link to="/admin/inspections" className="view-all-link">View All &rarr;</Link>
          </div>
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Product</th>
                <th>Inspector</th>
                <th>Date</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {stats.recent_inspections.map((insp) => (
                <tr key={insp.id}>
                  <td>
                    <Link to={`/inspector/inspections/${insp.id}`}>#{insp.id}</Link>
                  </td>
                  <td>{insp.product_name || '—'}</td>
                  <td>{insp.inspector_id ? `Inspector #${insp.inspector_id}` : '—'}</td>
                  <td>{insp.created_at ? new Date(insp.created_at).toLocaleDateString() : '—'}</td>
                  <td>
                    <StatusBadge status={insp.overall_status || 'INCOMPLETE'} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Empty State */}
      {stats.total_inspections === 0 && (
        <div className="section-card">
          <div className="empty-state">
            <p>No inspections have been conducted yet. The system is ready for use.</p>
          </div>
        </div>
      )}
    </div>
  );
}
