/* LicenseLens — Client-side API helper using fetch + JWT from sessionStorage */

const API = {
  baseURL: '/api',

  getToken() {
    return localStorage.getItem('ll_access_token') || '';
  },

  async request(method, path, body = null) {
    const headers = { 'Content-Type': 'application/json' };
    const token = this.getToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const opts = { method, headers };
    if (body) opts.body = JSON.stringify(body);

    const res = await fetch(`${this.baseURL}${path}`, opts);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || err.error || `HTTP ${res.status}`);
    }
    return res.json();
  },

  get:    (path)        => API.request('GET', path),
  post:   (path, body)  => API.request('POST', path, body),
  put:    (path, body)  => API.request('PUT', path, body),
  delete: (path)        => API.request('DELETE', path),
};

// Table search utility
function filterTable(tableId, query) {
  const rows = document.querySelectorAll('#' + tableId + ' tbody tr');
  const q = query.toLowerCase();
  rows.forEach(row => {
    row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
  });
}

// Badge helper
function riskBadge(level) {
  const map = {
    CRITICAL: 'badge-critical',
    HIGH: 'badge-high',
    MEDIUM: 'badge-medium',
    LOW: 'badge-low',
  };
  return map[level] || 'badge-secondary';
}
