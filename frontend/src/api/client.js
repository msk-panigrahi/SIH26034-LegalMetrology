/**
 * Centralized API client for LegalMetriX backend.
 */

const API_BASE = '/api';

class ApiClient {
  constructor() {
    this.baseUrl = API_BASE;
  }

  getToken() {
    return localStorage.getItem('token');
  }

  setToken(token) {
    localStorage.setItem('token', token);
  }

  clearToken() {
    localStorage.removeItem('token');
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const token = this.getToken();

    const headers = {
      ...options.headers,
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    // Don't set Content-Type for FormData
    if (!(options.body instanceof FormData)) {
      headers['Content-Type'] = 'application/json';
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    // Handle 401 - token expired or invalid
    if (response.status === 401) {
      this.clearToken();
      window.location.href = '/login';
      throw new Error('Session expired. Please log in again.');
    }

    // Safely parse response - may not always be JSON
    let data;
    const contentType = response.headers.get('content-type') || '';
    try {
      if (contentType.includes('application/json')) {
        data = await response.json();
      } else {
        const text = await response.text();
        // Try parsing as JSON anyway in case content-type is wrong
        try {
          data = JSON.parse(text);
        } catch {
          data = { detail: text || 'Request failed' };
        }
      }
    } catch (parseError) {
      // If parsing fails completely, create a generic error
      throw new Error('Unable to process server response. The server may be temporarily unavailable.');
    }

    if (!response.ok) {
      throw new Error(data.detail || data.message || `Request failed (${response.status})`);
    }

    return data;
  }

  get(endpoint) {
    return this.request(endpoint, { method: 'GET' });
  }

  post(endpoint, body) {
    if (body instanceof FormData) {
      return this.request(endpoint, { method: 'POST', body });
    }
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  put(endpoint, body) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(body),
    });
  }

  delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  }
}

export const api = new ApiClient();
export default api;
