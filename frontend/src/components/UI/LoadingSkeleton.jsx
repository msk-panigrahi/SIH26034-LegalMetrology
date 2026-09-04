/**
 * Loading skeleton placeholder for pages.
 */

import './LoadingSkeleton.css';

export default function LoadingSkeleton({ cards = 3, rows = 5 }) {
  return (
    <div className="skeleton-container">
      <div className="skeleton-header">
        <div className="skeleton-line skeleton-title" />
        <div className="skeleton-line skeleton-subtitle" />
      </div>

      <div className="skeleton-grid">
        {Array.from({ length: cards }).map((_, i) => (
          <div key={i} className="skeleton-card">
            <div className="skeleton-icon" />
            <div className="skeleton-card-lines">
              <div className="skeleton-line skeleton-value" />
              <div className="skeleton-line skeleton-label" />
            </div>
          </div>
        ))}
      </div>

      <div className="skeleton-table">
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="skeleton-row">
            <div className="skeleton-line skeleton-cell" style={{ width: '10%' }} />
            <div className="skeleton-line skeleton-cell" style={{ width: '35%' }} />
            <div className="skeleton-line skeleton-cell" style={{ width: '25%' }} />
            <div className="skeleton-line skeleton-cell" style={{ width: '20%' }} />
          </div>
        ))}
      </div>
    </div>
  );
}
