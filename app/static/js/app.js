/**
 * DocuVault - Core Application Script
 */

document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initLiveBackground();
  initModals();
  initDropdowns();
  initShortcuts();
});

// Theme Management (Dark / Light)
function initTheme() {
  const themeToggleBtn = document.getElementById('themeToggleBtn');
  const savedTheme = localStorage.getItem('docuvault_theme') || 'light';
  
  document.documentElement.setAttribute('data-theme', savedTheme);
  updateThemeIcon(savedTheme);

  if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme');
      const next = current === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('docuvault_theme', next);
      updateThemeIcon(next);
      showToast(`Switched to ${next} theme`, 'info');
    });
  }
}

function updateThemeIcon(theme) {
  const btn = document.getElementById('themeToggleBtn');
  if (btn) {
    btn.innerHTML = `<i data-lucide="${theme === 'dark' ? 'sun' : 'moon'}" id="themeIcon" style="width: 18px; height: 18px;"></i>`;
    btn.setAttribute('title', `Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`);
    if (window.lucide) {
      lucide.createIcons();
    }
  }
}

// Toast Notifications
function showToast(message, type = 'info') {
  let container = document.getElementById('toastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  
  const iconName = type === 'success' ? 'check-circle' : type === 'danger' ? 'alert-triangle' : 'info';
  
  toast.innerHTML = `
    <i data-lucide="${iconName}" class="toast-icon"></i>
    <span style="flex: 1; font-size: 0.88rem; font-weight: 500;">${message}</span>
    <button style="background:none; border:none; color:var(--text-muted); cursor:pointer;" onclick="this.parentElement.remove()">
      <i data-lucide="x" style="width:14px; height:14px;"></i>
    </button>
  `;

  container.appendChild(toast);
  if (window.lucide) lucide.createIcons();

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// Modals
function initModals() {
  // Open modal buttons: data-open-modal="modalId"
  document.querySelectorAll('[data-open-modal]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const modalId = btn.getAttribute('data-open-modal');
      openModal(modalId);
    });
  });

  // Close modal buttons: data-close-modal
  document.querySelectorAll('[data-close-modal]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const modal = btn.closest('.modal-backdrop');
      if (modal) closeModal(modal.id);
    });
  });

  // Close on backdrop click
  document.querySelectorAll('.modal-backdrop').forEach(modal => {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        closeModal(modal.id);
      }
    });
  });
}

function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add('show');
    document.body.style.overflow = 'hidden';
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('show');
    document.body.style.overflow = '';
  }
}

// Dropdowns
function initDropdowns() {
  document.addEventListener('click', (e) => {
    const trigger = e.target.closest('[data-dropdown-toggle]');
    if (trigger) {
      e.stopPropagation();
      const menu = trigger.nextElementSibling;
      if (menu && menu.classList.contains('dropdown-menu')) {
        // Close all other dropdowns
        document.querySelectorAll('.dropdown-menu.show').forEach(m => {
          if (m !== menu) m.classList.remove('show');
        });
        menu.classList.toggle('show');
      }
    } else {
      document.querySelectorAll('.dropdown-menu.show').forEach(m => m.classList.remove('show'));
    }
  });
}

// Global Shortcuts
function initShortcuts() {
  document.addEventListener('keydown', (e) => {
    if (e.key === '/' && !['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) {
      e.preventDefault();
      const searchInput = document.getElementById('globalSearchInput');
      if (searchInput) searchInput.focus();
    }
    if (e.key === 'Escape') {
      document.querySelectorAll('.modal-backdrop.show').forEach(m => closeModal(m.id));
      const previewBackdrop = document.getElementById('previewModal');
      if (previewBackdrop && previewBackdrop.classList.contains('show')) {
        closePreview();
      }
    }
  });
}

// Live Interactive Red Mathematical Shapes Background (No Web Lines)
function initLiveBackground() {
  const canvas = document.getElementById('liveParticlesCanvas');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  let width = (canvas.width = window.innerWidth);
  let height = (canvas.height = window.innerHeight);

  window.addEventListener('resize', () => {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
  });

  const mouse = { x: null, y: null, maxDist: 180 };

  window.addEventListener('mousemove', (e) => {
    mouse.x = e.clientX;
    mouse.y = e.clientY;
  });

  window.addEventListener('mouseleave', () => {
    mouse.x = null;
    mouse.y = null;
  });

  const shapeTypes = ['hexagon', 'triangle', 'concentric', 'cube', 'symbol'];
  const symbolsList = ['π', 'Σ', '∞', 'Δ', '∫', '√x', 'f(x)', 'θ', 'λ'];

  class MathShape {
    constructor() {
      this.reset();
    }

    reset() {
      this.x = Math.random() * width;
      this.y = Math.random() * height;
      this.size = Math.random() * 24 + 14;
      this.vx = (Math.random() - 0.5) * 0.45;
      this.vy = (Math.random() - 0.5) * 0.45;
      this.angle = Math.random() * Math.PI * 2;
      this.rotSpeed = (Math.random() - 0.5) * 0.015;
      this.type = shapeTypes[Math.floor(Math.random() * shapeTypes.length)];
      this.symbol = symbolsList[Math.floor(Math.random() * symbolsList.length)];
      this.alpha = Math.random() * 0.35 + 0.15;
      this.pulse = Math.random() * Math.PI;
    }

    update() {
      this.x += this.vx;
      this.y += this.vy;
      this.angle += this.rotSpeed;
      this.pulse += 0.02;

      // Wrap edges
      if (this.x < -40) this.x = width + 40;
      if (this.x > width + 40) this.x = -40;
      if (this.y < -40) this.y = height + 40;
      if (this.y > height + 40) this.y = -40;

      // Mouse repulsion (Smooth physics without drawing any lines)
      if (mouse.x !== null && mouse.y !== null) {
        const dx = this.x - mouse.x;
        const dy = this.y - mouse.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < mouse.maxDist && dist > 0) {
          const force = (mouse.maxDist - dist) / mouse.maxDist;
          this.x += (dx / dist) * force * 1.5;
          this.y += (dy / dist) * force * 1.5;
        }
      }
    }

    draw() {
      const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
      ctx.save();
      ctx.translate(this.x, this.y);
      ctx.rotate(this.angle);

      // Electric Royal Blue / Sapphire Cyan colors
      const strokeColor = isDark
        ? `rgba(96, 165, 250, ${this.alpha * 1.3})`
        : `rgba(37, 99, 235, ${this.alpha * 0.85})`;
      const fillColor = isDark
        ? `rgba(59, 130, 246, ${this.alpha * 0.22})`
        : `rgba(219, 234, 254, ${this.alpha * 0.35})`;

      ctx.strokeStyle = strokeColor;
      ctx.fillStyle = fillColor;
      ctx.lineWidth = 1.4;

      if (this.type === 'hexagon') {
        ctx.beginPath();
        for (let i = 0; i < 6; i++) {
          const a = (i * Math.PI) / 3;
          const px = this.size * Math.cos(a);
          const py = this.size * Math.sin(a);
          if (i === 0) ctx.moveTo(px, py);
          else ctx.lineTo(px, py);
        }
        ctx.closePath();
        ctx.stroke();
        ctx.fill();
      } else if (this.type === 'triangle') {
        ctx.beginPath();
        for (let i = 0; i < 3; i++) {
          const a = (i * 2 * Math.PI) / 3 - Math.PI / 2;
          const px = this.size * Math.cos(a);
          const py = this.size * Math.sin(a);
          if (i === 0) ctx.moveTo(px, py);
          else ctx.lineTo(px, py);
        }
        ctx.closePath();
        ctx.stroke();
        ctx.fill();
      } else if (this.type === 'concentric') {
        const pulseR = this.size + Math.sin(this.pulse) * 4;
        ctx.beginPath();
        ctx.arc(0, 0, pulseR, 0, Math.PI * 2);
        ctx.stroke();
        ctx.beginPath();
        ctx.arc(0, 0, pulseR * 0.55, 0, Math.PI * 2);
        ctx.stroke();
      } else if (this.type === 'cube') {
        // Isometric 3D Wireframe Cube
        const s = this.size * 0.7;
        ctx.beginPath();
        // Top diamond
        ctx.moveTo(0, -s);
        ctx.lineTo(s * 0.86, -s * 0.5);
        ctx.lineTo(0, 0);
        ctx.lineTo(-s * 0.86, -s * 0.5);
        ctx.closePath();
        ctx.stroke();

        // Downward vertical edges
        ctx.beginPath();
        ctx.moveTo(-s * 0.86, -s * 0.5);
        ctx.lineTo(-s * 0.86, s * 0.5);
        ctx.lineTo(0, s);
        ctx.lineTo(s * 0.86, s * 0.5);
        ctx.lineTo(s * 0.86, -s * 0.5);
        ctx.moveTo(0, 0);
        ctx.lineTo(0, s);
        ctx.stroke();
      } else if (this.type === 'symbol') {
        ctx.font = `${Math.round(this.size * 1.1)}px 'Plus Jakarta Sans', monospace`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillStyle = strokeColor;
        ctx.fillText(this.symbol, 0, 0);
      }

      ctx.restore();
    }
  }

  const shapeCount = Math.min(Math.floor((width * height) / 28000), 38);
  const shapes = [];

  for (let i = 0; i < shapeCount; i++) {
    shapes.push(new MathShape());
  }

  function animate() {
    ctx.clearRect(0, 0, width, height);

    for (let i = 0; i < shapes.length; i++) {
      shapes[i].update();
      shapes[i].draw();
    }

    requestAnimationFrame(animate);
  }

  animate();
}


