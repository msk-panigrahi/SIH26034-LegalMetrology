/**
 * Login page for LegalMetriX.
 */

import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Login.css';

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const user = await login(username, password);
      if (user.role === 'ADMIN') {
        navigate('/admin/dashboard');
      } else {
        navigate('/inspector/dashboard');
      }
    } catch (err) {
      setError(err.message || 'Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-left">
        <div className="login-branding">
          <div className="brand-icon">⚖</div>
          <h1 className="brand-title">LegalMetriX</h1>
          <p className="brand-subtitle">Legal Metrology Inspection &amp; Compliance Platform</p>

          <div className="workflow-steps">
            <div className="workflow-step">
              <span className="step-icon">📷</span>
              <span className="step-label">Upload Package Image</span>
            </div>
            <div className="workflow-step">
              <span className="step-icon">🔍</span>
              <span className="step-label">OCR &amp; Field Extraction</span>
            </div>
            <div className="workflow-step">
              <span className="step-icon">✅</span>
              <span className="step-label">Automated Compliance Check</span>
            </div>
            <div className="workflow-step">
              <span className="step-icon">📋</span>
              <span className="step-label">Generate Inspection Report</span>
            </div>
          </div>

          <p className="trust-text">
            Secure inspection workspace for Legal Metrology officers.
          </p>
        </div>
      </div>

      <div className="login-right">
        <div className="login-form-container">
          <h2 className="form-title">Sign In</h2>
          <p className="form-subtitle">Enter your credentials to access the platform</p>

          <div className="login-role-tabs">
            <div className="role-tab active">
              <span className="role-tab-icon">👤</span>
              <span>Inspector Login</span>
            </div>
            <div className="role-tab-info">
              Admin accounts use the same login — role is determined by your account type.
            </div>
          </div>

          {error && (
            <div className="error-banner">
              <span className="error-icon">⚠</span>
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="login-form">
            <div className="field-group">
              <label htmlFor="username">Username</label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter your username"
                required
                autoComplete="username"
              />
            </div>

            <div className="field-group">
              <label htmlFor="password">Password</label>
              <div className="password-input-wrap">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  required
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  className="toggle-password"
                  onClick={() => setShowPassword(!showPassword)}
                  tabIndex={-1}
                >
                  {showPassword ? '🙈' : '👁'}
                </button>
              </div>
            </div>

            <button type="submit" className="login-btn" disabled={loading}>
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          <p className="register-link">
            Don't have an account? <Link to="/register">Register as Inspector</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
