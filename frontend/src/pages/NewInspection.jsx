/**
 * New Inspection — upload image and run the full inspection pipeline.
 */

import { useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/client';
import StatusBadge from '../components/UI/StatusBadge';
import './NewInspection.css';

const STEPS = [
  { key: 'upload', label: 'Upload Image' },
  { key: 'ocr', label: 'OCR Analysis' },
  { key: 'extract', label: 'Field Extraction' },
  { key: 'compliance', label: 'Compliance Check' },
  { key: 'report', label: 'Report' },
];

export default function NewInspection() {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [activeStep, setActiveStep] = useState(-1);
  const [completedSteps, setCompletedSteps] = useState([]);
  const [failedStep, setFailedStep] = useState(null);
  const [error, setError] = useState('');
  const [inspectionId, setInspectionId] = useState(null);

  // Result states
  const [ocrResult, setOcrResult] = useState(null);
  const [extractResult, setExtractResult] = useState(null);
  const [complianceResult, setComplianceResult] = useState(null);

  const [processing, setProcessing] = useState(false);

  const handleFileSelect = (e) => {
    const selected = e.target.files[0];
    if (selected) {
      setFile(selected);
      setPreview(URL.createObjectURL(selected));
      setError('');
    }
  };

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    const dropped = e.dataTransfer.files[0];
    if (dropped && dropped.type.startsWith('image/')) {
      setFile(dropped);
      setPreview(URL.createObjectURL(dropped));
      setError('');
    }
  }, []);

  const handleDragOver = (e) => e.preventDefault();

  const markStep = (stepKey, result) => {
    setCompletedSteps((prev) => [...prev, stepKey]);
    return result;
  };

  const runPipeline = async () => {
    if (!file) return;
    setProcessing(true);
    setError('');
    setActiveStep(0);
    setCompletedSteps([]);
    setFailedStep(null);

    try {
      // Step 1: Upload
      const formData = new FormData();
      formData.append('file', file);
      const uploadResult = await api.post('/inspections/upload', formData);
      const id = uploadResult.inspection_id;
      setInspectionId(id);
      markStep('upload');
      setActiveStep(1);

      // Step 2: OCR
      const ocrData = await api.post(`/inspections/${id}/ocr`);
      setOcrResult(ocrData);
      markStep('ocr');
      setActiveStep(2);

      // Step 3: Field Extraction
      const extractData = await api.post(`/inspections/${id}/extract-fields`);
      setExtractResult(extractData);
      markStep('extract');
      setActiveStep(3);

      // Step 4: Compliance
      const compData = await api.post(`/inspections/${id}/compliance`);
      setComplianceResult(compData);
      markStep('compliance');
      setActiveStep(4);

      // Step 5: Report
      const reportData = await api.post(`/inspections/${id}/report`);
      markStep('report');
      setActiveStep(-1);
    } catch (err) {
      setError(err.message);
      setFailedStep(activeStep);
    } finally {
      setProcessing(false);
    }
  };

  const reset = () => {
    setFile(null);
    setPreview(null);
    setActiveStep(-1);
    setCompletedSteps([]);
    setFailedStep(null);
    setError('');
    setInspectionId(null);
    setOcrResult(null);
    setExtractResult(null);
    setComplianceResult(null);
  };

  const currentStepIdx = activeStep >= 0 ? activeStep : -1;

  return (
    <div className="new-inspection">
      <div className="page-header">
        <div>
          <h1 className="page-heading">New Inspection</h1>
          <p className="page-subheading">Upload a package image to start the inspection pipeline</p>
        </div>
      </div>

      {/* Processing Stepper */}
      {completedSteps.length > 0 || processing || error ? (
        <div className="stepper-card">
          <div className="stepper">
            {STEPS.map((step, idx) => {
              const isCompleted = completedSteps.includes(step.key);
              const isCurrent = currentStepIdx === idx;
              const isFailed = failedStep === idx;
              const isPending = idx > currentStepIdx && !isCompleted;

              return (
                <div
                  key={step.key}
                  className={`stepper-step ${isCompleted ? 'completed' : ''} ${isCurrent ? 'current' : ''} ${isFailed ? 'failed' : ''} ${isPending ? 'pending' : ''}`}
                >
                  <div className="step-indicator">
                    {isCompleted ? '✓' : isFailed ? '✕' : isCurrent ? '●' : '○'}
                  </div>
                  <span className="step-label">{step.label}</span>
                  {idx < STEPS.length - 1 && <div className="step-connector" />}
                </div>
              );
            })}
          </div>
        </div>
      ) : null}

      {/* Error Banner */}
      {error && (
        <div className="error-banner">
          <span className="error-icon">⚠</span>
          <span>{error}</span>
          <button onClick={runPipeline} className="retry-btn">Retry</button>
        </div>
      )}

      {/* Upload Zone */}
      {!processing && completedSteps.length === 0 && !error && (
        <div
          className={`upload-zone ${file ? 'has-file' : ''}`}
          onClick={() => fileInputRef.current?.click()}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/png,image/jpg"
            onChange={handleFileSelect}
            style={{ display: 'none' }}
          />

          {preview ? (
            <div className="upload-preview">
              <img src={preview} alt="Package preview" />
              <div className="upload-file-info">
                <span className="file-name">{file.name}</span>
                <span className="file-size">{(file.size / 1024).toFixed(1)} KB</span>
                <button
                  className="remove-btn"
                  onClick={(e) => { e.stopPropagation(); reset(); }}
                >
                  Remove
                </button>
              </div>
            </div>
          ) : (
            <div className="upload-prompt">
              <span className="upload-icon">📷</span>
              <p className="upload-text">Drag &amp; drop package photo here</p>
              <p className="upload-subtext">or click to browse</p>
              <p className="upload-formats">JPG, JPEG, PNG</p>
            </div>
          )}
        </div>
      )}

      {/* Start Button */}
      {file && completedSteps.length === 0 && !processing && !error && (
        <div className="action-bar">
          <button className="primary-btn large" onClick={runPipeline}>
            Start Inspection Pipeline
          </button>
        </div>
      )}

      {/* Results */}
      {completedSteps.length > 0 && (
        <div className="results-section">
          {/* OCR Summary */}
          {ocrResult && (
            <div className="section-card">
              <div className="section-header">
                <h2 className="section-title">OCR Analysis</h2>
                <StatusBadge status="PASS" />
              </div>
              <div className="section-body">
                <div className="info-row">
                  <span className="info-label">Confidence</span>
                  <span className="info-value">{ocrResult.ocr?.confidence?.toFixed(1) || '—'}%</span>
                </div>
                <div className="info-row">
                  <span className="info-label">Words Detected</span>
                  <span className="info-value">{ocrResult.ocr?.word_count || '—'}</span>
                </div>
                <details className="raw-text-section">
                  <summary>View Raw OCR Text</summary>
                  <pre className="raw-text">{ocrResult.ocr?.raw_text}</pre>
                </details>
              </div>
            </div>
          )}

          {/* Extracted Fields */}
          {extractResult && (
            <div className="section-card">
              <div className="section-header">
                <h2 className="section-title">Extracted Product Information</h2>
                <StatusBadge status="PASS" />
              </div>
              <div className="section-body">
                <div className="fields-grid">
                  {extractResult.fields && Object.entries(extractResult.fields).map(([key, value]) => (
                    <div key={key} className="field-item">
                      <span className="field-label">{key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</span>
                      <span className="field-value">
                        {value === null || value === undefined
                          ? 'Not detected'
                          : typeof value === 'object'
                            ? value.value || JSON.stringify(value)
                            : String(value)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Compliance Summary */}
          {complianceResult && (
            <div className="section-card">
              <div className="section-header">
                <h2 className="section-title">Compliance Assessment</h2>
                <StatusBadge status={complianceResult.overall_status} size="lg" />
              </div>
              <div className="section-body">
                <div className="compliance-summary-grid">
                  <div className="summary-item pass">
                    <span className="summary-count">{complianceResult.summary?.passed || 0}</span>
                    <span className="summary-label">Passed</span>
                  </div>
                  <div className="summary-item fail">
                    <span className="summary-count">{complianceResult.summary?.failed || 0}</span>
                    <span className="summary-label">Failed</span>
                  </div>
                  <div className="summary-item warn">
                    <span className="summary-count">{complianceResult.summary?.warnings || 0}</span>
                    <span className="summary-label">Warnings</span>
                  </div>
                  <div className="summary-item info">
                    <span className="summary-count">{complianceResult.summary?.not_verifiable || 0}</span>
                    <span className="summary-label">Not Verifiable</span>
                  </div>
                </div>

                {complianceResult.rules && (
                  <table className="data-table" style={{ marginTop: 16 }}>
                    <thead>
                      <tr>
                        <th>Rule</th>
                        <th>Requirement</th>
                        <th>Status</th>
                        <th>Evidence</th>
                      </tr>
                    </thead>
                    <tbody>
                      {complianceResult.rules.map((rule) => (
                        <tr key={rule.rule_id}>
                          <td><strong>{rule.rule_id}</strong></td>
                          <td>{rule.rule_name}</td>
                          <td><StatusBadge status={rule.status} /></td>
                          <td className="evidence-cell">{rule.evidence || '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="action-bar">
            {inspectionId && (
              <button
                className="primary-btn"
                onClick={() => navigate(`/inspector/inspections/${inspectionId}`)}
              >
                View Full Inspection
              </button>
            )}
            <button className="secondary-btn" onClick={reset}>
              Start New Inspection
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
