/**
 * Landing Page — public-facing LegalMetriX landing with stats.
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import './LandingPage.css';

export default function LandingPage() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    fetch('/api/public/stats')
      .then((res) => {
        if (res.ok) return res.json();
        return null;
      })
      .then((data) => {
        if (data) setStats(data);
      })
      .catch(() => {});
  }, []);

  return (
    <div className="landing-page">
      {/* Hero Section */}
      <header className="landing-header">
        <div className="landing-nav">
          <div className="landing-logo">
            <span className="logo-icon">&#9878;</span>
            <span className="logo-text">LegalMetriX</span>
          </div>
          <div className="landing-nav-links">
            <Link to="/login" className="nav-link">Inspector Login</Link>
            <Link to="/register" className="nav-link nav-link-outline">Register</Link>
          </div>
        </div>
      </header>

      <main className="landing-main">
        {/* Hero */}
        <section className="hero-section">
          <div className="hero-content">
            <div className="hero-badge">Packaged Commodity Compliance</div>
            <h1 className="hero-title">LegalMetriX</h1>
            <p className="hero-subtitle">
              Automated Compliance Screening &amp; Inspection Support for Legal Metrology Officers
            </p>
            <p className="hero-description">
              An intelligent inspection support platform that helps Legal Metrology officers digitize
              package verification, extract mandatory declarations using OCR, automatically evaluate
              compliance rules, maintain inspection history, and generate inspection reports.
            </p>
            <div className="hero-actions">
              <Link to="/login" className="hero-btn hero-btn-primary">Inspector Login</Link>
              <Link to="/register" className="hero-btn hero-btn-secondary">Register as Inspector</Link>
            </div>
          </div>
          <div className="hero-visual">
            <div className="hero-card hero-card-1">
              <span className="hero-card-icon">&#128247;</span>
              <span>Upload Package Image</span>
            </div>
            <div className="hero-card hero-card-2">
              <span className="hero-card-icon">&#128269;</span>
              <span>OCR &amp; Field Extraction</span>
            </div>
            <div className="hero-card hero-card-3">
              <span className="hero-card-icon">&#9989;</span>
              <span>Automated Compliance</span>
            </div>
            <div className="hero-card hero-card-4">
              <span className="hero-card-icon">&#128203;</span>
              <span>Generate Reports</span>
            </div>
          </div>
        </section>

        {/* Stats Section */}
        {stats && (
          <section className="stats-section">
            <div className="stats-grid">
              <div className="stat-item">
                <span className="stat-number">{stats.total_inspections}</span>
                <span className="stat-desc">Inspections Reviewed</span>
              </div>
              <div className="stat-item stat-green">
                <span className="stat-number">{stats.compliant}</span>
                <span className="stat-desc">Compliant</span>
              </div>
              <div className="stat-item stat-red">
                <span className="stat-number">{stats.non_compliant}</span>
                <span className="stat-desc">Non-Compliant</span>
              </div>
              <div className="stat-item stat-amber">
                <span className="stat-number">{stats.review_required}</span>
                <span className="stat-desc">Review Required</span>
              </div>
              <div className="stat-item stat-blue">
                <span className="stat-number">{stats.total_inspectors}</span>
                <span className="stat-desc">Active Inspectors</span>
              </div>
            </div>
          </section>
        )}

        {/* Features */}
        <section className="features-section">
          <h2 className="features-title">How It Works</h2>
          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon-wrap feature-icon-blue">
                <span>&#128247;</span>
              </div>
              <h3>Upload Package Image</h3>
              <p>Capture or upload a photo of the packaged commodity label. Supports JPG, PNG, and other common formats.</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon-wrap feature-icon-purple">
                <span>&#128269;</span>
              </div>
              <h3>OCR &amp; Extraction</h3>
              <p>Advanced OCR extracts text and identifies mandatory declarations: product name, MRP, net quantity, manufacturer details, dates, and more.</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon-wrap feature-icon-green">
                <span>&#9989;</span>
              </div>
              <h3>Compliance Rules</h3>
              <p>Deterministic rule engine evaluates extracted declarations against Legal Metrology (Packaged Commodities) Rules, 2011.</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon-wrap feature-icon-amber">
                <span>&#128203;</span>
              </div>
              <h3>Reports &amp; History</h3>
              <p>Generate professional PDF inspection reports. Maintain complete inspection history with search and filtering.</p>
            </div>
          </div>
        </section>

        {/* Legal Notice */}
        <section className="legal-notice-section">
          <div className="legal-notice">
            <span className="legal-notice-icon">&#9878;</span>
            <div>
              <strong>Inspection Support System</strong>
              <p>
                LegalMetriX is an automated compliance screening and inspection support tool.
                Final legal determination remains with the authorized Legal Metrology officer.
              </p>
            </div>
          </div>
        </section>
      </main>

      <footer className="landing-footer">
        <p>LegalMetriX &mdash; Packaged Commodity Legal Metrology Compliance &amp; Inspection Support System</p>
        <p className="footer-small">Rule Version: LM-PCR-2026 | Legal Metrology (Packaged Commodities) Rules, 2011</p>
      </footer>
    </div>
  );
}
