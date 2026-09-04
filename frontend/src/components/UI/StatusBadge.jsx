/**
 * Status badge for compliance and rule statuses.
 */

import './StatusBadge.css';

const STATUS_MAP = {
  COMPLIANT: { label: 'Compliant', className: 'badge-success' },
  PASS: { label: 'Pass', className: 'badge-success' },
  NON_COMPLIANT: { label: 'Non-Compliant', className: 'badge-danger' },
  FAIL: { label: 'Fail', className: 'badge-danger' },
  REVIEW_REQUIRED: { label: 'Review Required', className: 'badge-warning' },
  WARNING: { label: 'Warning', className: 'badge-warning' },
  INCOMPLETE: { label: 'Incomplete', className: 'badge-neutral' },
  NOT_VERIFIABLE: { label: 'Not Verifiable', className: 'badge-info' },
  NOT_APPLICABLE: { label: 'N/A', className: 'badge-neutral' },
};

export default function StatusBadge({ status, size = 'md' }) {
  const info = STATUS_MAP[status] || { label: status || 'Unknown', className: 'badge-neutral' };

  return (
    <span className={`status-badge ${info.className} badge-${size}`}>
      {info.label}
    </span>
  );
}
