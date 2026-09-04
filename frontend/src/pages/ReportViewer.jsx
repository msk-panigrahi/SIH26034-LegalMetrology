/**
 * Report Viewer — displays a professional inspection report.
 */

import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../api/client';
import StatusBadge from '../components/UI/StatusBadge';
import LoadingSkeleton from '../components/UI/LoadingSkeleton';
import './ReportViewer.css';

export default function ReportViewer() {
  const { id } = useParams();
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadReport();
  }, [id]);

  const loadReport = async () => {
    try {
      const data = await api.get(`/inspections/${id}/report`);
      setReport(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <LoadingSkeleton cards={2} rows={3} />;

  if (error) {
    return (
      <div className="error-state">
        <h3>Unable to load report</h3>
        <p>{error}</p>
        <Link to={`/inspector/inspections/${id}`} className="retry-btn">Back to Inspection</Link>
      </div>
    );
  }

  const rd = report?.report_data || {};

  return (
    <div className="report-viewer">
      <div className="page-header">
        <div>
          <h1 className="page-heading">Inspection Report</h1>
          <p className="page-subheading">Report {report.report_number}</p>
        </div>
        <div className="header-actions">
          <Link to={`/inspector/inspections/${id}`} className="secondary-btn">← Back</Link>
          <button className="secondary-btn" onClick={() => window.open(`/api/inspections/${id}/report/pdf`, '_blank')}
            style={{ cursor: 'pointer' }}>
            👁 View PDF
          </button>
          <a href={`/api/inspections/${id}/report/pdf`} download className="primary-btn"
            style={{ textDecoration: 'none' }}>
            ↓ Download PDF
          </a>
        </div>
      </div>

      <div className="report-paper">
        {/* Report Header */}
        <div className="report-header">
          <div className="report-brand">
            <span className="report-logo">⚖</span>
            <div>
              <h2 className="report-brand-name">LegalMetriX</h2>
              <p className="report-brand-sub">Legal Metrology Inspection &amp; Compliance Platform</p>
            </div>
          </div>
          <div className="report-meta">
            <div className="meta-row">
              <span className="meta-label">Report No:</span>
              <span className="meta-value">{report.report_number}</span>
            </div>
            <div className="meta-row">
              <span className="meta-label">Inspection ID:</span>
              <span className="meta-value">#{id}</span>
            </div>
            <div className="meta-row">
              <span className="meta-label">Date:</span>
              <span className="meta-value">
                {report.created_at ? new Date(report.created_at).toLocaleDateString('en-IN', {
                  day: 'numeric', month: 'long', year: 'numeric'
                }) : '—'}
              </span>
            </div>
            {rd.inspector && (
              <div className="meta-row">
                <span className="meta-label">Inspector:</span>
                <span className="meta-value">{rd.inspector.name}</span>
              </div>
            )}
          </div>
        </div>

        <div className="report-divider" />

        {/* Product Details */}
        {rd.product && (
          <div className="report-section">
            <h3 className="report-section-title">Product Details</h3>
            <div className="report-grid">
              {Object.entries(rd.product).map(([key, value]) => (
                value && (
                  <div key={key} className="report-field">
                    <span className="report-field-label">
                      {key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                    </span>
                    <span className="report-field-value">
                      {typeof value === 'object' ? value.value || JSON.stringify(value) : String(value)}
                    </span>
                  </div>
                )
              ))}
            </div>
          </div>
        )}

        <div className="report-divider" />

        {/* Compliance Assessment */}
        {rd.compliance && (
          <div className="report-section">
            <h3 className="report-section-title">Automated Compliance Assessment</h3>
            <div className="report-compliance-status">
              <StatusBadge status={rd.compliance.overall_status} size="lg" />
              <div className="report-compliance-summary">
                <span>Rules Checked: {rd.compliance.rules_checked}</span>
                <span>Passed: {rd.compliance.passed}</span>
                <span>Failed: {rd.compliance.failed}</span>
                <span>Warnings: {rd.compliance.warnings}</span>
              </div>
            </div>
          </div>
        )}

        <div className="report-divider" />

        {/* Findings */}
        {rd.findings && rd.findings.length > 0 && (
          <div className="report-section">
            <h3 className="report-section-title">Rule Findings</h3>
            <table className="report-table">
              <thead>
                <tr>
                  <th>Rule</th>
                  <th>Requirement</th>
                  <th>Status</th>
                  <th>Legal Basis</th>
                  <th>Evidence</th>
                </tr>
              </thead>
              <tbody>
                {rd.findings.map((f) => (
                  <tr key={f.rule_id}>
                    <td><strong>{f.rule_id}</strong></td>
                    <td>{f.rule_name}</td>
                    <td><StatusBadge status={f.status} /></td>
                    <td>{f.legal_basis}</td>
                    <td className="evidence-cell">{f.evidence || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Disclaimer */}
        <div className="report-disclaimer">
          <p>
            This automated assessment is based on detected package declarations and the configured
            Legal Metrology rules. It should not be interpreted as a substitute for inspection by
            an authorized Legal Metrology officer.
          </p>
        </div>
      </div>
    </div>
  );
}
