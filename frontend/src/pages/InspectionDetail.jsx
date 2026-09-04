/**
 * Inspection Detail — full inspection overview with extracted data, compliance, and report.
 */

import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../api/client';
import StatusBadge from '../components/UI/StatusBadge';
import LoadingSkeleton from '../components/UI/LoadingSkeleton';
import './InspectionDetail.css';

export default function InspectionDetail() {
  const { id } = useParams();
  const [inspection, setInspection] = useState(null);
  const [compliance, setCompliance] = useState(null);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('overview');
  const [generatingReport, setGeneratingReport] = useState(false);

  useEffect(() => {
    loadInspection();
  }, [id]);

  const loadInspection = async () => {
    setLoading(true);
    try {
      const data = await api.get(`/inspections/${id}`);
      setInspection(data);
      // Try loading compliance
      try {
        const comp = await api.get(`/inspections/${id}/compliance`);
        setCompliance(comp);
      } catch { /* no compliance yet */ }
      // Try loading report
      try {
        const rep = await api.get(`/inspections/${id}/report`);
        setReport(rep);
      } catch { /* no report yet */ }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const generateReport = async () => {
    setGeneratingReport(true);
    try {
      const rep = await api.post(`/inspections/${id}/report`);
      setReport(rep);
    } catch (err) {
      setError(err.message);
    } finally {
      setGeneratingReport(false);
    }
  };

  if (loading) return <LoadingSkeleton cards={3} rows={5} />;

  if (error && !inspection) {
    return (
      <div className="error-state">
        <h3>Unable to load inspection</h3>
        <p>{error}</p>
        <Link to="/inspector/history" className="retry-btn">Back to History</Link>
      </div>
    );
  }

  const ocr = inspection?.ocr_confidence != null ? {
    confidence: inspection.ocr_confidence,
    status: inspection.ocr_status,
    raw_text: inspection.raw_text,
  } : null;
  const fields = inspection?.extracted_fields;

  return (
    <div className="inspection-detail">
      <div className="page-header">
        <div>
          <h1 className="page-heading">Inspection #{id}</h1>
          <p className="page-subheading">
            {inspection?.filename} — {inspection?.created_at ? new Date(inspection.created_at).toLocaleString() : ''}
          </p>
        </div>
        <div className="header-actions">
          <Link to="/inspector/history" className="secondary-btn">← Back to History</Link>
          {compliance && !report && (
            <button className="primary-btn" onClick={generateReport} disabled={generatingReport}>
              {generatingReport ? 'Generating...' : 'Generate Report'}
            </button>
          )}
          {report && (
            <>
              <Link to={`/inspector/inspections/${id}/report`} className="primary-btn">
                View Report
              </Link>
              <button className="secondary-btn" onClick={() => window.open(`/api/inspections/${id}/report/pdf`, '_blank')}
                style={{ cursor: 'pointer' }}>
                👁 View PDF
              </button>
              <a href={`/api/inspections/${id}/report/pdf`} download className="secondary-btn"
                style={{ textDecoration: 'none' }}>
                ↓ Download PDF
              </a>
            </>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="tabs">
        {['overview', 'compliance'].map((tab) => (
          <button
            key={tab}
            className={`tab-btn ${activeTab === tab ? 'active' : ''}`}
            onClick={() => setActiveTab(tab)}
          >
            {tab === 'overview' ? 'Overview' : 'Compliance'}
          </button>
        ))}
      </div>

      {activeTab === 'overview' && (
        <div className="detail-sections">
          {/* OCR Info */}
          {ocr && (
            <div className="section-card">
              <div className="section-header">
                <h2 className="section-title">OCR Analysis</h2>
                <StatusBadge status="PASS" />
              </div>
              <div className="section-body">
                <div className="info-grid">
                  <div className="info-row">
                    <span className="info-label">OCR Confidence</span>
                    <span className="info-value">{ocr.confidence?.toFixed(1) || '—'}%</span>
                  </div>
                  <div className="info-row">
                    <span className="info-label">Status</span>
                    <span className="info-value">{ocr.status || '—'}</span>
                  </div>
                </div>
                {ocr.raw_text && (
                  <details className="raw-text-section" style={{ marginTop: 12 }}>
                    <summary style={{ cursor: 'pointer', fontWeight: 500, color: 'var(--primary)' }}>
                      View Raw OCR Text
                    </summary>
                    <pre style={{
                      marginTop: 8,
                      padding: 16,
                      background: '#f8fafc',
                      border: '1px solid var(--border)',
                      borderRadius: 8,
                      fontSize: 13,
                      lineHeight: 1.6,
                      color: 'var(--text-secondary)',
                      maxHeight: 300,
                      overflowY: 'auto',
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word',
                    }}>
                      {ocr.raw_text}
                    </pre>
                  </details>
                )}
              </div>
            </div>
          )}

          {/* Extracted Fields */}
          {fields && (
            <div className="section-card">
              <div className="section-header">
                <h2 className="section-title">Extracted Product Information</h2>
                <StatusBadge status="PASS" />
              </div>
              <div className="section-body">
                <div className="fields-grid">
                  {Object.entries(fields).map(([key, value]) => (
                    <div key={key} className="field-item">
                      <span className="field-label">
                        {key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                      </span>
                      <span className="field-value">
                        {value === null || value === undefined
                          ? 'Not detected'
                          : typeof value === 'object'
                            ? value.value || value.phone || JSON.stringify(value)
                            : String(value)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {!ocr && !fields && (
            <div className="section-card">
              <div className="empty-state">
                <p>OCR and field extraction have not been performed yet.</p>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'compliance' && (
        <div className="detail-sections">
          {compliance ? (
            <>
              <div className="section-card">
                <div className="section-header">
                  <h2 className="section-title">Automated Assessment</h2>
                  <StatusBadge status={compliance.overall_status} size="lg" />
                </div>
                <div className="section-body">
                  <div className="compliance-summary-grid">
                    <div className="summary-item pass">
                      <span className="summary-count">{compliance.summary?.passed || 0}</span>
                      <span className="summary-label">Passed</span>
                    </div>
                    <div className="summary-item fail">
                      <span className="summary-count">{compliance.summary?.failed || 0}</span>
                      <span className="summary-label">Failed</span>
                    </div>
                    <div className="summary-item warn">
                      <span className="summary-count">{compliance.summary?.warnings || 0}</span>
                      <span className="summary-label">Warnings</span>
                    </div>
                    <div className="summary-item info">
                      <span className="summary-count">{compliance.summary?.not_verifiable || 0}</span>
                      <span className="summary-label">Not Verifiable</span>
                    </div>
                  </div>
                </div>
              </div>

              {compliance.rules && (
                <div className="section-card">
                  <div className="section-header">
                    <h2 className="section-title">Rule-by-Rule Findings</h2>
                  </div>
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Rule</th>
                        <th>Requirement</th>
                        <th>Status</th>
                        <th>Severity</th>
                        <th>Evidence</th>
                      </tr>
                    </thead>
                    <tbody>
                      {compliance.rules.map((rule) => (
                        <tr key={rule.rule_id}>
                          <td><strong>{rule.rule_id}</strong></td>
                          <td>{rule.rule_name}</td>
                          <td><StatusBadge status={rule.status} /></td>
                          <td>{rule.severity}</td>
                          <td className="evidence-cell">{rule.evidence || '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          ) : (
            <div className="section-card">
              <div className="empty-state">
                <p>Compliance evaluation has not been performed yet.</p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
