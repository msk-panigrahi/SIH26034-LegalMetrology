/**
 * Inspection History — list of inspections with search and filtering.
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/client';
import StatusBadge from '../components/UI/StatusBadge';
import LoadingSkeleton from '../components/UI/LoadingSkeleton';
import './Dashboard.css';

export default function InspectionHistory() {
  const [inspections, setInspections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const pageSize = 20;

  useEffect(() => {
    loadInspections();
  }, [page, statusFilter]);

  const loadInspections = async () => {
    setLoading(true);
    try {
      let url = `/inspections?page=${page}&page_size=${pageSize}`;
      if (statusFilter) url += `&status=${statusFilter}`;
      const data = await api.get(url);
      setInspections(data.items || []);
      setTotal(data.total || 0);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const filteredInspections = inspections.filter((insp) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      String(insp.id).includes(q) ||
      (insp.filename && insp.filename.toLowerCase().includes(q))
    );
  });

  if (loading && inspections.length === 0) return <LoadingSkeleton rows={8} />;

  return (
    <div className="dashboard">
      <div className="page-header">
        <div>
          <h1 className="page-heading">Inspection History</h1>
          <p className="page-subheading">View and manage your past inspections</p>
        </div>
        <Link to="/inspector/inspections/new" className="primary-btn">
          + New Inspection
        </Link>
      </div>

      {/* Filters */}
      <div className="filters-bar">
        <input
          type="text"
          placeholder="Search by ID or filename..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="filter-input"
        />
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
          className="filter-select"
        >
          <option value="">All Statuses</option>
          <option value="COMPLIANT">Compliant</option>
          <option value="NON_COMPLIANT">Non-Compliant</option>
          <option value="REVIEW_REQUIRED">Review Required</option>
          <option value="INCOMPLETE">Incomplete</option>
        </select>
      </div>

      {error && (
        <div className="error-state">
          <p>{error}</p>
          <button onClick={loadInspections} className="retry-btn">Retry</button>
        </div>
      )}

      <div className="section-card">
        {filteredInspections.length > 0 ? (
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Filename</th>
                <th>Created</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredInspections.map((insp) => (
                <tr key={insp.id}>
                  <td><strong>#{insp.id}</strong></td>
                  <td>{insp.filename}</td>
                  <td>{new Date(insp.created_at).toLocaleDateString()}</td>
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
            <p>No inspections found.</p>
            <Link to="/inspector/inspections/new" className="primary-btn">
              + New Inspection
            </Link>
          </div>
        )}

        {/* Pagination */}
        {total > pageSize && (
          <div className="pagination">
            <button
              className="page-btn"
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
            >
              Previous
            </button>
            <span className="page-info">Page {page} of {Math.ceil(total / pageSize)}</span>
            <button
              className="page-btn"
              disabled={page >= Math.ceil(total / pageSize)}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
