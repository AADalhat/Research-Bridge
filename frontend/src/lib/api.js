// Central API client. Keeps base URL, bearer token and error handling in one place.
const BASE_URL = (import.meta.env?.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1').replace(/\/+$/, '');

let token = null;
let onUnauthorized = null;

export function setUnauthorizedHandler(handler) {
  onUnauthorized = handler;
}

export function setToken(value) {
  token = value;
}

export function getToken() {
  return token;
}

// Sends one request. FormData requests must not set Content-Type manually:
// the browser needs to generate the multipart boundary.
async function request(path, options = {}) {
  const isFormData = options.body instanceof FormData;
  const headers = {
    ...(isFormData ? {} : options.body ? { 'Content-Type': 'application/json' } : {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  let response;
  try {
    response = await fetch(BASE_URL + path, { ...options, headers });
  } catch (cause) {
    if (cause.name === 'AbortError') throw cause;
    const error = new Error('Could not reach the server. Check that the backend is running and try again.');
    error.status = 0;
    throw error;
  }

  if (!response.ok) {
    if (response.status === 401 && onUnauthorized) onUnauthorized();
    let message = 'Request failed (' + response.status + ').';
    try {
      const data = await response.json();
      if (typeof data.detail === 'string') message = data.detail;
      else if (data.detail) message = typeof data.detail === 'object' ? JSON.stringify(data.detail) : message;
    } catch { /* keep default message */ }
    const error = new Error(message);
    error.status = response.status;
    throw error;
  }

  return response.status === 204 ? null : response.json();
}

export const auth = {
  login: async (registration_number, password) => {
    const result = await request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ registration_number, password }),
    });
    if (!result.access_token) throw new Error('Login response did not include an access token.');
    setToken(result.access_token);
    return result;
  },
  me: () => request('/auth/me'),
  logout: async () => {
    try { await request('/auth/logout', { method: 'POST' }); }
    finally { setToken(null); }
  },
};

// Creates a submission. Sends exactly the fields agreed for this milestone.
export async function createSubmission({ file, author_name, faculty, department, language }, { signal } = {}) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('author_name', author_name);
  formData.append('faculty', faculty);
  formData.append('department', department);
  formData.append('language', language);
  return request('/submissions', { method: 'POST', body: formData, signal });
}

// Polls one submission. The bearer token is attached automatically.
export function getSubmission(submissionId, { signal } = {}) {
  return request('/submissions/' + encodeURIComponent(submissionId), { signal });
}
