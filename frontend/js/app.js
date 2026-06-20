(function() {

/* ============================================================
   STATE
   ============================================================ */
let currentUser = null;
let currentPatientId = null;

/* ============================================================
   UTILITIES
   ============================================================ */
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);
const show = (el) => { if (el) el.classList.remove('hidden'); };
const hide = (el) => { if (el) el.classList.add('hidden'); };

function fmtDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' });
}

function fmtDateTime(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleString('pt-BR');
}

/* ============================================================
   NAVIGATION
   ============================================================ */
function navigate(view, data) {
  $$('.view').forEach(v => v.classList.remove('active'));
  const el = document.getElementById(`view-${view}`);
  if (el) el.classList.add('active');

  // Update nav links
  $$('.nav-link').forEach(l => l.classList.toggle('active', l.dataset.view === view));

  if (view === 'login') {
    $('#topbar').classList.add('hidden');
  } else {
    $('#topbar').classList.remove('hidden');
  }

  if (view === 'dashboard') renderDashboard();
  if (view === 'audit') renderAuditLogs();
  if (view === 'setup-2fa') render2FA();
  if (view === 'patient' && data) { currentPatientId = data; renderPatientDetail(data); }
  if (view === 'report' && data) renderReport(data);

  window.scrollTo({ top: 0 });
}

/* ============================================================
   TOAST / LOADING
   ============================================================ */
function showError(msg) {
  const el = document.createElement('div');
  el.className = 'msg-error';
  el.textContent = msg;
  return el;
}

function spinner() {
  const d = document.createElement('div');
  d.className = 'spinner';
  return d;
}

/* ============================================================
   AUTH
   ============================================================ */
$('#form-login').addEventListener('submit', async (e) => {
  e.preventDefault();
  const email = $('#login-email').value;
  const pass = $('#login-password').value;
  const totp = $('#login-totp').value;
  const err = $('#login-error');

  try {
    hide(err);
    const data = await API.login(email, pass, totp || undefined);
    localStorage.setItem('token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    currentUser = data.user;
    $('#user-badge').textContent = `${data.user.full_name || data.user.email}`;
    navigate('dashboard');
  } catch (e) {
    if (e.message.includes('2FA code required')) {
      show($('#field-totp'));
      err.textContent = 'Código 2FA obrigatório';
      show(err);
    } else {
      err.textContent = e.message;
      show(err);
    }
  }
});

$('#btn-show-register').addEventListener('click', () => {
  hide($('#form-login'));
  hide($('#btn-show-register'));
  $('#login-footer').classList.add('hidden');
  show($('#form-register'));
});

$('#btn-cancel-register').addEventListener('click', () => {
  show($('#form-login'));
  show($('#btn-show-register'));
  hide($('#form-register'));
});

$('#form-register').addEventListener('submit', async (e) => {
  e.preventDefault();
  const err = $('#register-error');
  const data = {
    email: $('#reg-email').value,
    password: $('#reg-password').value,
    role: $('#reg-role').value,
    full_name: $('#reg-name').value || undefined,
    crm: $('#reg-crm').value || undefined,
  };
  try {
    hide(err);
    await API.register(data.email, data.password, data.role, data.full_name, data.crm);
    // auto-login
    const loginData = await API.login(data.email, data.password);
    localStorage.setItem('token', loginData.access_token);
    localStorage.setItem('refresh_token', loginData.refresh_token);
    currentUser = loginData.user;
    $('#user-badge').textContent = `${loginData.user.full_name || loginData.user.email}`;
    navigate('dashboard');
  } catch (e) {
    err.textContent = e.message;
    show(err);
  }
});

$('#btn-logout').addEventListener('click', () => {
  localStorage.removeItem('token');
  localStorage.removeItem('refresh_token');
  currentUser = null;
  $('#login-totp').value = '';
  hide($('#field-totp'));
  navigate('login');
});

/* ============================================================
   ROUTER (hash-based)
   ============================================================ */
window.addEventListener('hashchange', () => {
  const hash = location.hash.slice(1) || 'dashboard';
  // login check
  if (!localStorage.getItem('token') && hash !== 'login') {
    navigate('login');
    return;
  }
  if (hash.startsWith('patient/')) {
    const pid = hash.split('/')[1];
    navigate('patient', pid);
  } else if (hash.startsWith('report/')) {
    const rid = hash.split('/')[1];
    navigate('report', rid);
  } else {
    navigate(hash);
  }
});

// Nav clicks
$$('.nav-link[data-view]').forEach(l => {
  l.addEventListener('click', (e) => {
    e.preventDefault();
    location.hash = l.dataset.view;
  });
});

// Back buttons
$$('.back-btn').forEach(b => {
  b.addEventListener('click', () => {
    const view = b.dataset.view || 'dashboard';
    location.hash = view;
  });
});

/* ============================================================
   DASHBOARD
   ============================================================ */
async function renderDashboard() {
  const list = $('#patient-list');
  const stats = $('#stats-row');
  list.innerHTML = '<div class="spinner"></div>';

  try {
    const [patients, dashboard] = await Promise.all([
      API.listPatients(),
      API.doctorDashboard().catch(() => null),
    ]);

    // Stats
    if (dashboard) {
      stats.innerHTML = `
        <div class="stat-card"><div class="stat-value">${dashboard.total_patients}</div><div class="stat-label">Pacientes</div></div>
        <div class="stat-card"><div class="stat-value">${dashboard.total_exams}</div><div class="stat-label">Exames</div></div>
        <div class="stat-card"><div class="stat-value">${dashboard.total_reports}</div><div class="stat-label">Relatórios</div></div>
      `;
    } else {
      stats.innerHTML = '';
    }

    // Patient list
    if (!patients || patients.length === 0) {
      list.innerHTML = `<div class="empty-state"><div class="empty-icon">👤</div><p>Nenhum paciente encontrado</p></div>`;
      return;
    }

    list.innerHTML = patients.map(p => `
      <div class="card-item" data-id="${p.id}">
        <div>
          <div class="card-name">${p.full_name}</div>
          <div class="card-meta">${p.cpf_hash ? 'CPF registrado' : 'Sem CPF'} · Criado ${fmtDate(p.created_at)}</div>
        </div>
        <span class="card-badge">${(dashboard?.patients || []).find(x => x.patient_id === p.id)?.exams_count || 0} exames</span>
      </div>
    `).join('');

    list.querySelectorAll('.card-item').forEach(el => {
      el.addEventListener('click', () => {
        location.hash = `patient/${el.dataset.id}`;
      });
    });
  } catch (e) {
    list.innerHTML = `<div class="empty-state"><p>Erro ao carregar: ${e.message}</p></div>`;
  }
}

// Search patients
$('#search-patient').addEventListener('input', debounce(async (e) => {
  const q = e.target.value;
  try {
    const patients = await API.listPatients(q || undefined);
    const list = $('#patient-list');
    if (!patients || patients.length === 0) {
      list.innerHTML = `<div class="empty-state"><div class="empty-icon">🔍</div><p>Nenhum paciente encontrado para "${q}"</p></div>`;
      return;
    }
    list.innerHTML = patients.map(p => `
      <div class="card-item" data-id="${p.id}">
        <div>
          <div class="card-name">${p.full_name}</div>
          <div class="card-meta">${p.contact_phone || ''}</div>
        </div>
        <span class="card-badge">ver exames</span>
      </div>
    `).join('');
    list.querySelectorAll('.card-item').forEach(el => {
      el.addEventListener('click', () => location.hash = `patient/${el.dataset.id}`);
    });
  } catch (e) { /* ignore */ }
}, 300));

function debounce(fn, ms) {
  let timer;
  return function(...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), ms);
  };
}

$('#btn-add-patient').addEventListener('click', () => {
  showModal('Novo Paciente', `
    <div class="field"><label>Nome completo</label><input id="modal-patient-name" placeholder="Nome do paciente"></div>
    <div class="field"><label>Telefone</label><input id="modal-patient-phone" placeholder="55 11 99999-9999"></div>
    <div class="field"><label>Data de nascimento</label><input id="modal-patient-dob" type="date"></div>
    <button id="modal-save-patient" class="btn-primary">Salvar</button>
  `);
  $('#modal-save-patient').addEventListener('click', async () => {
    const name = $('#modal-patient-name').value;
    if (!name) return;
    try {
      await API.createPatient({
        full_name: name,
        contact_phone: $('#modal-patient-phone').value || undefined,
        date_of_birth: $('#modal-patient-dob').value || undefined,
      });
      closeModal();
      renderDashboard();
    } catch (e) { alert(e.message); }
  });
});

/* ============================================================
   PATIENT DETAIL
   ============================================================ */
async function renderPatientDetail(id) {
  const header = $('#patient-detail-header');
  header.innerHTML = '<div class="spinner"></div>';

  try {
    const patient = await API.getPatient(id);
    header.innerHTML = `
      <h2 style="margin-bottom:4px">${patient.full_name}</h2>
      <p style="color:var(--text-secondary);font-size:.875rem">${patient.contact_phone || ''} · Criado ${fmtDate(patient.created_at)}</p>
    `;
    currentPatientId = id;
    switchTab('exams');
    loadExams(id);
    loadReports(id);
    loadConsents(id);
  } catch (e) {
    header.innerHTML = `<p class="msg-error">${e.message}</p>`;
  }
}

// Tab switching
$$('.tab').forEach(tab => {
  tab.addEventListener('click', () => {
    const t = tab.dataset.tab;
    switchTab(t);
  });
});

function switchTab(tab) {
  $$('.tab').forEach(t => t.classList.toggle('active', t.dataset.tab === tab));
  $$('.tab-content').forEach(c => c.classList.toggle('active', c.id === `tab-${tab}`));
}

/* ---- Exams tab ---- */
async function loadExams(pid) {
  const el = $('#tab-exams');
  el.innerHTML = '<div class="spinner"></div>';
  try {
    const exams = await API.patientExams(pid);
    if (!exams || exams.length === 0) {
      el.innerHTML = '<div class="empty-state"><p>Nenhum exame cadastrado</p></div>';
      return;
    }
    el.innerHTML = `<div class="card-list">${exams.map(e => `
      <div class="card-item">
        <div>
          <div class="card-name">${e.exam_type}</div>
          <div class="card-meta">${fmtDate(e.exam_date)} · ${e.exam_type}</div>
        </div>
        <span class="card-badge">${e.uploaded_by ? 'Upload realizado' : 'Pendente'}</span>
      </div>
    `).join('')}</div>`;
  } catch (e) {
    el.innerHTML = `<div class="empty-state"><p>${e.message}</p></div>`;
  }
}

/* ---- Reports tab ---- */
async function loadReports(pid) {
  const el = $('#tab-reports');
  el.innerHTML = '<div class="spinner"></div>';
  try {
    const reports = await API.patientReports(pid);
    if (!reports || reports.length === 0) {
      el.innerHTML = `<div class="empty-state"><p>Nenhum relatório gerado</p></div>`;
      return;
    }
    el.innerHTML = `<div class="card-list">${reports.map(r => `
      <div class="card-item" data-id="${r.id}">
        <div>
          <div class="card-name">Relatório · ${r.model_version}</div>
          <div class="card-meta">${fmtDateTime(r.generated_at)} · ${r.status}</div>
        </div>
        <span class="card-badge" style="background:${r.status === 'success' ? 'var(--success-bg)' : 'var(--warning-bg)'};color:${r.status === 'success' ? 'var(--success)' : 'var(--warning)'}">${r.status}</span>
      </div>
    `).join('')}</div>`;
    el.querySelectorAll('.card-item').forEach(el => {
      el.addEventListener('click', () => location.hash = `report/${el.dataset.id}`);
    });
  } catch (e) {
    el.innerHTML = `<div class="empty-state"><p>${e.message}</p></div>`;
  }
}

/* ---- Consents tab ---- */
async function loadConsents(pid) {
  const el = $('#tab-consents');
  el.innerHTML = '<div class="spinner"></div>';
  try {
    const consents = await API.listConsents(pid);
    el.innerHTML = `
      <button id="btn-new-consent" class="btn-secondary" style="width:auto;margin-bottom:16px">+ Novo consentimento</button>
      <div class="card-list">${consents.length === 0 ? '<div class="empty-state"><p>Nenhum consentimento registrado</p></div>' :
        consents.map(c => `
          <div class="card-item">
            <div>
              <div class="card-name">${c.consent_type.replace(/_/g, ' ')}</div>
              <div class="card-meta">Assinado ${fmtDateTime(c.signed_at)} ${c.expires_at ? '· Expira '+fmtDate(c.expires_at) : ''}</div>
            </div>
            <span class="card-badge" style="background:${c.expires_at && new Date(c.expires_at) < new Date() ? 'var(--danger-bg)' : 'var(--success-bg)'};color:${c.expires_at && new Date(c.expires_at) < new Date() ? 'var(--danger)' : 'var(--success)'}">
              ${c.expires_at && new Date(c.expires_at) < new Date() ? 'Expirado' : 'Ativo'}
            </span>
          </div>
        `).join('')
      }</div>
    `;
    $('#btn-new-consent').addEventListener('click', () => {
      showModal('Novo Consentimento (LGPD)', `
        <div class="field">
          <label>Tipo</label>
          <select id="modal-consent-type">
            <option value="ai_analysis">Análise por IA</option>
            <option value="data_storage">Armazenamento de Dados</option>
            <option value="research">Pesquisa</option>
          </select>
        </div>
        <div class="field">
          <label>Texto do consentimento</label>
          <textarea id="modal-consent-text" rows="3" style="width:100%;padding:8px;border:1px solid var(--border);border-radius:8px">Autorizo o processamento dos meus exames médicos para geração de relatório de apoio à decisão clínica.</textarea>
        </div>
        <div class="field">
          <label>Data de expiração (opcional)</label>
          <input id="modal-consent-expiry" type="date">
        </div>
        <button id="modal-save-consent" class="btn-primary">Salvar consentimento</button>
      `);
      $('#modal-save-consent').addEventListener('click', async () => {
        try {
          await API.createConsent({
            patient_id: currentPatientId,
            consent_type: $('#modal-consent-type').value,
            consent_text: $('#modal-consent-text').value,
            signed_at: new Date().toISOString(),
            expires_at: $('#modal-consent-expiry').value || undefined,
          });
          closeModal();
          loadConsents(currentPatientId);
        } catch (e) { alert(e.message); }
      });
    });
  } catch (e) {
    el.innerHTML = `<div class="empty-state"><p>${e.message}</p></div>`;
  }
}

/* ============================================================
   REPORT VIEW
   ============================================================ */
async function renderReport(id) {
  const el = $('#report-card');
  el.innerHTML = '<div class="spinner"></div>';

  try {
    const report = await API.getReport(id);
    const content = report.content || { summary: '', findings: [], alerts: [], recommendations: [], disclaimer: '' };

    el.innerHTML = `
      <h1>Relatório de Apoio à Decisão Clínica</h1>
      <div class="report-meta">
        Gerado ${fmtDateTime(report.generated_at)} · ${report.model_version} · Confiança ${Math.round((report.model_confidence || 0) * 100)}%
      </div>

      <div class="report-section">
        <h3>Resumo</h3>
        <p>${content.summary || 'Nenhum resumo disponível.'}</p>
      </div>

      ${content.findings && content.findings.length ? `
      <div class="report-section">
        <h3>Achados Relevantes</h3>
        ${content.findings.map(f => `
          <div class="finding-item">
            <strong>${f.finding}</strong>
            <span class="confidence">${Math.round(f.confidence * 100)}% confiança</span>
            <p style="margin-top:4px;font-size:.875rem;color:var(--text-secondary)">${f.relevance}</p>
          </div>
        `).join('')}
      </div>` : ''}

      ${content.alerts && content.alerts.length ? `
      <div class="report-section">
        <h3>Alertas</h3>
        ${content.alerts.map(a => `
          <div class="alert-item severity-${a.severity}">
            <strong>${a.severity.toUpperCase()}:</strong> ${a.message}
          </div>
        `).join('')}
      </div>` : ''}

      ${content.recommendations && content.recommendations.length ? `
      <div class="report-section">
        <h3>Investigações Sugeridas</h3>
        <ul style="padding-left:20px">${content.recommendations.map(r => `<li style="margin-bottom:4px">${r}</li>`).join('')}</ul>
      </div>` : ''}

      <div class="report-disclaimer">
        <strong>⚠️ ${content.disclaimer || 'Ferramenta de apoio. Decisão médica é responsabilidade do médico.'}</strong>
      </div>
    `;
  } catch (e) {
    el.innerHTML = `<div class="empty-state"><p>Erro ao carregar relatório: ${e.message}</p></div>`;
  }
}

$('#back-from-report').addEventListener('click', () => {
  if (currentPatientId) location.hash = `patient/${currentPatientId}`;
  else location.hash = 'dashboard';
});

/* ============================================================
   AUDIT LOGS
   ============================================================ */
async function renderAuditLogs() {
  const el = $('#audit-table-wrapper');
  el.innerHTML = '<div class="spinner"></div>';

  try {
    const action = $('#audit-filter-action').value;
    const data = await API.getAuditLogs({ action_type: action || undefined });

    if (!data || !data.logs || data.logs.length === 0) {
      el.innerHTML = '<div class="empty-state"><p>Nenhum registro de auditoria encontrado</p></div>';
      return;
    }

    el.innerHTML = `
      <table>
        <thead><tr>
          <th>Data/Hora</th><th>Ação</th><th>Paciente</th><th>Usuário</th><th>IP</th><th>Status</th>
        </tr></thead>
        <tbody>
          ${data.logs.slice(0, 50).map(l => `
            <tr>
              <td style="white-space:nowrap">${fmtDateTime(l.timestamp)}</td>
              <td><code style="font-size:.75rem">${l.action_type}</code></td>
              <td>${l.patient_id ? l.patient_id.slice(0, 8)+'…' : '—'}</td>
              <td>${l.user_id ? l.user_id.slice(0, 8)+'…' : '—'}</td>
              <td>${l.ip_address}</td>
              <td><span style="color:${l.status === 'success' ? 'var(--success)' : 'var(--danger)'}">${l.status}</span></td>
            </tr>
          `).join('')}
        </tbody>
      </table>
      <p style="text-align:center;margin-top:8px;font-size:.8rem;color:var(--text-secondary)">${data.total} registros encontrados · exibindo até 50</p>
    `;
  } catch (e) {
    el.innerHTML = `<div class="empty-state"><p>${e.message}</p></div>`;
  }
}

$('#audit-filter-action').addEventListener('change', renderAuditLogs);

$('#btn-export-audit').addEventListener('click', () => {
  window.open(`${API.BASE}/audit/logs/export?format=csv`, '_blank');
});

/* ============================================================
   2FA SETUP
   ============================================================ */
async function render2FA() {
  const status = $('#twofa-status');
  const setup = $('#twofa-setup');
  const disable = $('#twofa-disable');
  hide(setup);
  hide(disable);

  try {
    const s = await API.status2FA();
    if (s.two_fa_enabled) {
      status.textContent = '✅ Autenticação em duas etapas está ATIVA';
      show(disable);
      hide(setup);
    } else {
      status.textContent = '❌ 2FA não está configurado';
      const setupData = await API.setup2FA();
      $('#twofa-secret-display').textContent = `Secret: ${setupData.secret}`;
      $('#qr-code-container').innerHTML = `
        <div style="background:#fff;padding:16px;border-radius:8px;border:1px solid var(--border);text-align:center">
          <p style="font-size:.8rem;color:var(--text-secondary);margin-bottom:8px">Escaneie com Google Authenticator / Authy:</p>
          <img src="https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(setupData.qr_code_uri)}" alt="QR Code TOTP" style="border-radius:8px">
        </div>`;
      show(setup);
      hide(disable);
    }
  } catch (e) {
    status.textContent = `Erro: ${e.message}`;
  }
}

$('#btn-verify-2fa').addEventListener('click', async () => {
  const code = $('#twofa-verify-code').value;
  if (code.length !== 6) return;
  try {
    await API.verify2FA(code);
    $('#twofa-status').textContent = '✅ 2FA ativado com sucesso!';
    render2FA();
  } catch (e) {
    $('#twofa-error').textContent = e.message;
    show($('#twofa-error'));
  }
});

$('#btn-disable-2fa').addEventListener('click', async () => {
  const code = $('#twofa-disable-code').value;
  if (code.length !== 6) return;
  try {
    await API.disable2FA(code);
    $('#twofa-status').textContent = '❌ 2FA desativado';
    render2FA();
  } catch (e) {
    alert(e.message);
  }
});

/* ============================================================
   MODAL
   ============================================================ */
function showModal(title, bodyHtml) {
  $('#modal-title').textContent = title;
  $('#modal-body').innerHTML = bodyHtml;
  hide($('#modal-overlay'));
  show($('#modal-overlay'));
}

function closeModal() {
  hide($('#modal-overlay'));
}

$('#modal-close').addEventListener('click', closeModal);
$('#modal-overlay').addEventListener('click', (e) => {
  if (e.target === e.currentTarget) closeModal();
});

/* ============================================================
   INIT
   ============================================================ */
async function init() {
  const token = localStorage.getItem('token');
  if (token) {
    try {
      const user = await API.me();
      currentUser = user;
      $('#user-badge').textContent = `${user.full_name || user.email}`;
    } catch {
      localStorage.removeItem('token');
    }
  }

  // Navigate based on hash or default
  const hash = location.hash.slice(1);
  if (localStorage.getItem('token')) {
    navigate(hash || 'dashboard');
  } else {
    navigate('login');
  }

  // Override hash to trigger routing on initial load
  if (!hash && localStorage.getItem('token')) location.hash = 'dashboard';
}

init();

})();
