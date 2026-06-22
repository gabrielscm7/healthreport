const API = (() => {
  function detectBase() {
    const saved = localStorage.getItem('api_base');
    if (saved) return saved;
    
    // Em produção (Railway): window.location.origin já aponta pro backend
    // Em dev local: se estiver em localhost:8000, usa o origin
    // Se estiver em localhost:3000 (dev separado), fallback pra localhost:8000
    
    if (window.location.hostname === 'localhost' && window.location.port !== '8000') {
      return 'http://localhost:8000';
    }
    return window.location.origin;  // Produção: railway.app
  }

  const BASE = detectBase();

  function token() { return localStorage.getItem('token'); }
  function headers(extra = {}) {
    const h = { 'Content-Type': 'application/json', ...extra };
    const t = token();
    if (t) h['Authorization'] = `Bearer ${t}`;
    return h;
  }

  async function request(method, path, body = null) {
    const opts = { method, headers: headers() };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(`${BASE}${path}`, opts);
    if (res.status === 204) return null;
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
    return data;
  }

  const get    = (p) => request('GET', p);
  const post   = (p, b) => request('POST', p, b);
  const patch  = (p, b) => request('PATCH', p, b);
  const del    = (p) => request('DELETE', p);

  return {
    BASE,
    // Auth
    login: (email, pass, totp) => post('/auth/login', { email, password: pass, totp_code: totp }),
    register: (email, pass, role, full_name, crm) => post('/auth/register', { email, password: pass, role, full_name, crm }),
    me: () => get('/auth/me'),
    // 2FA
    setup2FA: () => post('/auth/2fa/setup'),
    verify2FA: (code) => post(`/auth/2fa/verify?code=${code}`),
    disable2FA: (code) => post(`/auth/2fa/disable?code=${code}`),
    status2FA: () => get('/auth/2fa/status'),
    // Patients
    listPatients: (search) => get(`/patients${search ? '?search='+encodeURIComponent(search) : ''}`),
    getPatient: (id) => get(`/patients/${id}`),
    createPatient: (data) => post('/patients', data),
    // Patient portal
    patientExams: (pid) => get(`/patient/${pid}/exams`),
    patientReports: (pid) => get(`/patient/${pid}/reports`),
    getReport: (rid) => get(`/specialist/report/${rid}`),
    // Admin
    organizeExams: (q, pid) => post('/admin/process', { action: 'organize_documents', query: q, patient_id: pid }),
    generateReport: (pid, md, did) => post('/specialist/report', { patient_id: pid, exams_markdown: md, requesting_doctor_id: did }),
    // Audit
    getAuditLogs: (params = {}) => {
      const q = new URLSearchParams();
      Object.entries(params).forEach(([k, v]) => { if (v !== undefined && v !== '') q.set(k, v); });
      return get(`/audit/logs?${q.toString()}&limit=50`);
    },
    // Consents
    listConsents: (pid) => get(`/consents/${pid}`),
    createConsent: (data) => post('/consents', data),
    revokeConsent: (cid) => del(`/consents/${cid}`),
    // Dashboard
    doctorDashboard: () => get('/doctor/dashboard'),
    // LGPD
    myData: () => get('/lgpd/my-data'),
  };
})();
