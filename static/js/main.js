/* Study Tracker — Global JS */

// ── Theme ──────────────────────────────────────────────────────────────────
function applyTheme(theme, color) {
  document.documentElement.setAttribute('data-theme', theme || 'dark');
  document.documentElement.setAttribute('data-color', color || 'purple');
  localStorage.setItem('theme', theme);
  localStorage.setItem('color', color);
}

function loadTheme() {
  const t = localStorage.getItem('theme') || 'dark';
  const c = localStorage.getItem('color') || 'purple';
  applyTheme(t, c);
}

loadTheme();

// ── Toast ──────────────────────────────────────────────────────────────────
function showToast(msg, type = 'info', duration = 3000) {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }
  const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${icons[type]||'ℹ️'}</span><span>${msg}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.animation = 'slideInRight 0.3s reverse';
    setTimeout(() => toast.remove(), 280);
  }, duration);
}

// ── API Helpers ────────────────────────────────────────────────────────────
async function api(url, method = 'GET', data = null) {
  const opts = { method, headers: { 'Content-Type': 'application/json' } };
  if (data) opts.body = JSON.stringify(data);
  try {
    const r = await fetch(url, opts);
    if (r.status === 401) { window.location = '/login'; return null; }
    return await r.json();
  } catch (e) {
    showToast('Network error', 'error');
    return null;
  }
}

// ── Modal ──────────────────────────────────────────────────────────────────
function openModal(id) {
  document.getElementById(id)?.classList.add('open');
}
function closeModal(id) {
  document.getElementById(id)?.classList.remove('open');
}

// ── Sidebar toggle (mobile) ────────────────────────────────────────────────
function toggleSidebar() {
  document.querySelector('.sidebar')?.classList.toggle('open');
}

// ── Active nav item ────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const path = window.location.pathname;
  document.querySelectorAll('.nav-item').forEach(item => {
    const href = item.getAttribute('href');
    if (href && (path === href || (href !== '/' && path.startsWith(href)))) {
      item.classList.add('active');
    }
  });

  // Sidebar overlay close
  document.addEventListener('click', (e) => {
    const sidebar = document.querySelector('.sidebar');
    if (sidebar?.classList.contains('open') && !sidebar.contains(e.target) &&
        !e.target.closest('.menu-toggle')) {
      sidebar.classList.remove('open');
    }
  });
});

// ── Notification API ───────────────────────────────────────────────────────
function requestNotifications() {
  if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission();
  }
}

function sendNotification(title, body) {
  if ('Notification' in window && Notification.permission === 'granted') {
    new Notification(title, { body, icon: '/static/images/icon.png' });
  }
}

// ── Reminder Checker ───────────────────────────────────────────────────────
function checkReminders(reminders) {
  const now = new Date();
  const nowStr = now.toTimeString().slice(0,5);
  const dateStr = now.toISOString().slice(0,10);
  reminders.forEach(r => {
    if (r.reminder_date === dateStr && r.reminder_time === nowStr && r.is_active) {
      sendNotification('⏰ Study Reminder', r.message);
      showToast(`⏰ Reminder: ${r.message}`, 'warning', 5000);
    }
  });
}

// ── Pomodoro Timer ─────────────────────────────────────────────────────────
class PomodoroTimer {
  constructor(displayEl, btnEl) {
    this.display = displayEl;
    this.btn = btnEl;
    this.time = 25 * 60;
    this.interval = null;
    this.running = false;
    this.subject = 'General';
    this.render();
  }
  toggle() {
    this.running ? this.pause() : this.start();
  }
  start() {
    this.running = true;
    this.btn.textContent = '⏸ Pause';
    this.interval = setInterval(() => {
      this.time--;
      this.render();
      if (this.time <= 0) {
        this.complete();
      }
    }, 1000);
  }
  pause() {
    this.running = false;
    clearInterval(this.interval);
    this.btn.textContent = '▶ Resume';
  }
  reset(mins = 25) {
    this.pause();
    this.time = mins * 60;
    this.btn.textContent = '▶ Start';
    this.render();
  }
  complete() {
    this.pause();
    sendNotification('🍅 Pomodoro Complete!', 'Great work! Time for a break.');
    showToast('🍅 Pomodoro complete! Take a break!', 'success', 5000);
    api('/api/study_session', 'POST', { subject: this.subject, duration: 25 });
    this.reset(5);
  }
  render() {
    const m = Math.floor(this.time / 60).toString().padStart(2, '0');
    const s = (this.time % 60).toString().padStart(2, '0');
    if (this.display) this.display.textContent = `${m}:${s}`;
  }
}

// ── Avatar initials ────────────────────────────────────────────────────────
function getInitials(name) {
  return name.split(' ').slice(0,2).map(w => w[0]).join('').toUpperCase();
}

// ── Date formatter ─────────────────────────────────────────────────────────
function formatDate(dateStr) {
  const d = new Date(dateStr + 'T00:00:00');
  return d.toLocaleDateString('en-US', { weekday:'short', month:'short', day:'numeric' });
}

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}

// ── Streak badge text ──────────────────────────────────────────────────────
function streakBadge(n) {
  if (n >= 30) return '🏆 Legend';
  if (n >= 14) return '💎 Diamond';
  if (n >= 7)  return '🥇 Gold';
  if (n >= 3)  return '🥈 Silver';
  if (n >= 1)  return '🥉 Bronze';
  return '🌱 Start';
}
