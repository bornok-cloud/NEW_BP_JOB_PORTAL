/* Job Portal - Main JS */

// ── Flash auto-dismiss ────────────────────────────────────
document.querySelectorAll('.alert').forEach(el => {
  const close = el.querySelector('.alert-close');
  if (close) close.addEventListener('click', () => el.remove());
  setTimeout(() => el.style.opacity = '0', 4500);
  setTimeout(() => el.remove(), 5000);
});

// ── Save Job Toggle ───────────────────────────────────────
document.querySelectorAll('.save-btn').forEach(btn => {
  btn.addEventListener('click', async function(e) {
    e.preventDefault();
    const jobId = this.dataset.jobId;
    try {
      const res = await fetch(`/save-job/${jobId}`, { method: 'POST' });
      const data = await res.json();
      this.classList.toggle('saved', data.saved);
      this.innerHTML = data.saved ? '&#9733;' : '&#9734;';
      showToast(data.saved ? 'Job saved!' : 'Job removed from saved', data.saved ? 'success' : 'info');
    } catch {}
  });
});

// ── Unread message badge ──────────────────────────────────
async function updateUnreadBadge() {
  try {
    const res = await fetch('/api/unread-count');
    const data = await res.json();
    const badge = document.getElementById('msg-badge');
    if (badge) {
      badge.textContent = data.count;
      badge.style.display = data.count > 0 ? 'inline' : 'none';
    }
  } catch {}
}
if (document.getElementById('msg-badge')) {
  updateUnreadBadge();
  setInterval(updateUnreadBadge, 30000);
}

// ── Toast notification ────────────────────────────────────
function showToast(msg, type = 'success') {
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = msg;
  Object.assign(toast.style, {
    position: 'fixed', bottom: '1.5rem', right: '1.5rem',
    background: type === 'success' ? '#10b981' : type === 'danger' ? '#ef4444' : '#3b82f6',
    color: '#fff', padding: '.75rem 1.3rem',
    borderRadius: '10px', boxShadow: '0 4px 20px rgba(0,0,0,.2)',
    fontFamily: "'DM Sans',sans-serif", fontSize: '.875rem', fontWeight: '600',
    zIndex: 9999, animation: 'fadeIn .3s ease'
  });
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}

// ── Modal helpers ─────────────────────────────────────────
function openModal(id) { document.getElementById(id)?.classList.add('open'); }
function closeModal(id) { document.getElementById(id)?.classList.remove('open'); }
document.querySelectorAll('.modal-overlay').forEach(m => {
  m.addEventListener('click', e => { if (e.target === m) m.classList.remove('open'); });
});

// ── Status update modal ───────────────────────────────────
document.querySelectorAll('[data-status-btn]').forEach(btn => {
  btn.addEventListener('click', function() {
    const appId = this.dataset.appId;
    const form = document.getElementById('status-form');
    if (form) form.action = `/employer/application/${appId}/status`;
    openModal('status-modal');
  });
});

// ── Interview date toggle ─────────────────────────────────
const statusSelect = document.getElementById('status-select');
const interviewFields = document.getElementById('interview-fields');
if (statusSelect && interviewFields) {
  statusSelect.addEventListener('change', function() {
    interviewFields.style.display = this.value === 'interview' ? 'block' : 'none';
  });
}

// ── Resume preview (builder) ──────────────────────────────
function updateResumePreview() {
  const fields = ['objective','work_experience','education','skills','certifications','languages'];
  fields.forEach(f => {
    const input = document.getElementById(`field-${f}`);
    const preview = document.getElementById(`preview-${f}`);
    if (input && preview) preview.textContent = input.value;
  });
}
document.querySelectorAll('[id^="field-"]').forEach(el => {
  el.addEventListener('input', updateResumePreview);
});

// ── Upload drag & drop ────────────────────────────────────
const uploadZone = document.querySelector('.upload-zone');
if (uploadZone) {
  uploadZone.addEventListener('dragover', e => { e.preventDefault(); uploadZone.classList.add('drag'); });
  uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('drag'));
  uploadZone.addEventListener('drop', e => {
    e.preventDefault(); uploadZone.classList.remove('drag');
    const file = e.dataTransfer.files[0];
    if (file && file.type === 'application/pdf') {
      const input = uploadZone.querySelector('input[type="file"]');
      if (input) {
        const dt = new DataTransfer(); dt.items.add(file); input.files = dt.files;
        uploadZone.querySelector('.upload-icon').textContent = '✅';
        uploadZone.querySelector('p').textContent = file.name;
      }
    }
  });
  uploadZone.addEventListener('click', () => uploadZone.querySelector('input[type="file"]')?.click());
}

// ── Score bar animate ─────────────────────────────────────
document.querySelectorAll('.score-fill').forEach(bar => {
  const w = bar.dataset.score || '0';
  bar.style.width = '0%';
  setTimeout(() => bar.style.width = w + '%', 400);
});

// ── Confirm delete ────────────────────────────────────────
document.querySelectorAll('[data-confirm]').forEach(btn => {
  btn.addEventListener('click', e => {
    if (!confirm(btn.dataset.confirm)) e.preventDefault();
  });
});

// ── Salary range display ──────────────────────────────────
const salMin = document.getElementById('sal-min');
const salMax = document.getElementById('sal-max');
const salDisplay = document.getElementById('sal-display');
if (salMin && salMax && salDisplay) {
  function updateSalDisplay() {
    salDisplay.textContent = `₱${parseInt(salMin.value).toLocaleString()} – ₱${parseInt(salMax.value).toLocaleString()}`;
  }
  salMin.addEventListener('input', updateSalDisplay);
  salMax.addEventListener('input', updateSalDisplay);
  updateSalDisplay();
}

// ── Char counter for textareas ────────────────────────────
document.querySelectorAll('textarea[maxlength]').forEach(ta => {
  const counter = document.createElement('small');
  counter.className = 'text-muted';
  ta.parentNode.appendChild(counter);
  function update() { counter.textContent = `${ta.value.length}/${ta.maxLength} chars`; }
  ta.addEventListener('input', update); update();
});

// ── Chat auto-scroll ──────────────────────────────────────
const chatMsgs = document.querySelector('.chat-messages');
if (chatMsgs) chatMsgs.scrollTop = chatMsgs.scrollHeight;

// ── Analytics chart (canvas) ──────────────────────────────
const chartCanvas = document.getElementById('analytics-chart');
if (chartCanvas && window.analyticsData) {
  const ctx = chartCanvas.getContext('2d');
  const data = window.analyticsData;
  const labels = data.map(d => d.title.substring(0,20));
  const values = data.map(d => d.total);
  const barW = chartCanvas.width / (labels.length * 2 + 1);
  const maxV = Math.max(...values, 1);
  ctx.clearRect(0, 0, chartCanvas.width, chartCanvas.height);
  labels.forEach((label, i) => {
    const x = barW + i * barW * 2;
    const h = (values[i] / maxV) * (chartCanvas.height - 60);
    const y = chartCanvas.height - h - 30;
    const grad = ctx.createLinearGradient(0, y, 0, chartCanvas.height);
    grad.addColorStop(0, '#4f46e5');
    grad.addColorStop(1, 'rgba(79,70,229,.2)');
    ctx.fillStyle = grad;
    ctx.roundRect(x, y, barW, h, [4,4,0,0]);
    ctx.fill();
    ctx.fillStyle = '#475569';
    ctx.font = '11px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(values[i], x + barW/2, y - 6);
    ctx.fillStyle = '#94a3b8';
    ctx.fillText(label, x + barW/2, chartCanvas.height - 8);
  });
}

// ── Print resume ──────────────────────────────────────────
document.getElementById('print-resume')?.addEventListener('click', () => window.print());

// ── Active sidebar link ───────────────────────────────────
const path = window.location.pathname;
document.querySelectorAll('.sidebar-link').forEach(link => {
  if (link.getAttribute('href') === path) link.classList.add('active');
});

// ── Form validation highlight ─────────────────────────────
document.querySelectorAll('form').forEach(form => {
  form.addEventListener('submit', function() {
    this.querySelectorAll('[required]').forEach(field => {
      if (!field.value.trim()) {
        field.style.borderColor = 'var(--danger)';
        field.addEventListener('input', () => field.style.borderColor = '', { once: true });
      }
    });
  });
});

/* ============================================================
   SIDEBAR — Collapsible Dashboard Toggle
   Controls:
     Desktop : hamburger collapses sidebar to icon-only mode
     Mobile  : hamburger slides sidebar in as full overlay
   State stored in localStorage so it persists across pages.
   ============================================================ */

(function SidebarController() {

  /* ── Constants ───────────────────────────────────────────── */
  var STORAGE_KEY   = 'jp_sidebar_collapsed';
  var MOBILE_BP     = 769;    // px — matches CSS breakpoint

  /* ── State ───────────────────────────────────────────────── */
  var isMobile = function() { return window.innerWidth < MOBILE_BP; };

  /* ── Apply persisted state on page load (desktop only) ───── */
  function applyPersistedState() {
    if (isMobile()) return;
    if (localStorage.getItem(STORAGE_KEY) === '1') {
      document.body.classList.add('sb-collapsed');
    }
  }

  /* ── Toggle (hamburger click) ────────────────────────────── */
  function toggleSidebar() {
    if (isMobile()) {
      // Mobile: toggle open overlay
      var isOpen = document.body.classList.toggle('sb-open');
      document.body.style.overflow = isOpen ? 'hidden' : '';
    } else {
      // Desktop: toggle collapsed icon-only mode
      var isCollapsed = document.body.classList.toggle('sb-collapsed');
      localStorage.setItem(STORAGE_KEY, isCollapsed ? '1' : '0');
    }
  }

  /* ── Close sidebar (mobile only, or any close-btn) ───────── */
  function closeSidebar() {
    document.body.classList.remove('sb-open');
    document.body.style.overflow = '';
  }

  /* ── Expose globals so onclick="" attributes work ─────────── */
  window.toggleSidebar = toggleSidebar;
  window.closeSidebar  = closeSidebar;
  // legacy names kept for safety
  window.openSidebar   = function() {
    if (isMobile()) {
      document.body.classList.add('sb-open');
      document.body.style.overflow = 'hidden';
    } else {
      toggleSidebar();
    }
  };

  /* ── Overlay click closes sidebar (mobile) ───────────────── */
  document.addEventListener('click', function(e) {
    if (e.target && e.target.id === 'sidebarOverlay') {
      closeSidebar();
    }
  });

  /* ── Escape key closes sidebar ───────────────────────────── */
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') closeSidebar();
  });

  /* ── Resize: clean up mobile state when resizing to desktop ─ */
  window.addEventListener('resize', function() {
    if (!isMobile()) {
      document.body.classList.remove('sb-open');
      document.body.style.overflow = '';
      applyPersistedState();
    }
  });

  /* ── Active sidebar link highlight (JS fallback) ─────────── */
  function highlightActiveLink() {
    var path = window.location.pathname;
    document.querySelectorAll('.sidebar-link').forEach(function(link) {
      var href = link.getAttribute('href');
      if (!href) return;
      // Jinja already adds .active via request.endpoint — 
      // this JS handles edge cases where paths match partially
      if (href !== '/' && path.startsWith(href) && !link.classList.contains('active')) {
        link.classList.add('active');
      }
    });
  }

  /* ── Init ─────────────────────────────────────────────────── */
  applyPersistedState();
  highlightActiveLink();

})();
