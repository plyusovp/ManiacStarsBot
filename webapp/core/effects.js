// --- ✨ Новый модуль для управления "вау-эффектами" ---

let confettiCanvas, confettiCtx;
let confettiPieces = [];
const isLowPerf = document.body.classList.contains('low-perf');

// --- 1. Эффект "Волны от клика" (Ripple) ---
export function applyRippleEffect(element) {
    if (!element) return;
    element.addEventListener('click', function(e) {
        // Убедимся, что у элемента есть position: relative/absolute/fixed
        // Это нужно, чтобы волна позиционировалась корректно
        const computedStyle = window.getComputedStyle(this);
        if (computedStyle.position === 'static') {
            this.style.position = 'relative';
        }

        const rect = this.getBoundingClientRect();
        const ripple = document.createElement('span');
        const diameter = Math.max(this.clientWidth, this.clientHeight);
        const radius = diameter / 2;

        ripple.style.width = ripple.style.height = `${diameter}px`;
        ripple.style.left = `${e.clientX - rect.left - radius}px`;
        ripple.style.top = `${e.clientY - rect.top - radius}px`;
        ripple.classList.add('ripple-effect');

        // Удаляем старую волну, если она есть, чтобы избежать наложения
        const existingRipple = this.querySelector('.ripple-effect');
        if (existingRipple) {
            existingRipple.remove();
        }

        this.appendChild(ripple);
        // Удаляем элемент волны после завершения анимации
        setTimeout(() => ripple.remove(), 600);
    });
}


// --- 2. Эффект "Магнитный курсор" (Magnetic Hover) ---
export function applyMagneticEffect(element, options = {}) {
    if (!element || isLowPerf) return; // Отключаем на слабых устройствах и на тач-устройствах

    const strength = options.strength || 0.4;
    const distance = options.distance || 80;

    element.addEventListener('mousemove', (e) => {
        const rect = element.getBoundingClientRect();
        const x = e.clientX - rect.left - rect.width / 2;
        const y = e.clientY - rect.top - rect.height / 2;
        const dist = Math.sqrt(x * x + y * y);

        if (dist < distance) {
            element.style.transition = 'transform 0.1s ease-out';
            element.style.transform = `translate(${x * strength}px, ${y * strength}px)`;
        } else {
            element.style.transform = 'translate(0, 0)';
        }
    });

    element.addEventListener('mouseleave', () => {
        element.style.transition = 'transform 0.3s var(--ease-spring)';
        element.style.transform = 'translate(0, 0)';
    });
}


// --- 3. Эффект "Конфетти" на Canvas ---

function initConfetti() {
    confettiCanvas = document.getElementById('confetti-canvas');
    if (!confettiCanvas) {
        confettiCanvas = document.createElement('canvas');
        confettiCanvas.id = 'confetti-canvas';
        document.body.appendChild(confettiCanvas);
    }
    confettiCtx = confettiCanvas.getContext('2d');
    window.addEventListener('resize', resizeConfettiCanvas, { passive: true });
    resizeConfettiCanvas();
}

function resizeConfettiCanvas() {
    if (!confettiCanvas) return;
    confettiCanvas.width = window.innerWidth;
    confettiCanvas.height = window.innerHeight;
}

const colors = ['#8A7CFF', '#F92B75', '#33D6A6', '#FFC85C', '#EAF2FF'];

function createConfettiPiece(x, y) {
    const angle = Math.random() * Math.PI * 2;
    const velocity = Math.random() * 4 + 3;
    return {
        x, y,
        vx: Math.cos(angle) * velocity,
        vy: Math.sin(angle) * velocity,
        size: Math.random() * 4 + 3,
        color: colors[Math.floor(Math.random() * colors.length)],
        opacity: 1,
        gravity: 0.08,
        resistance: 0.96,
        life: 120, // ~2 секунды при 60fps
    };
}

let confettiAnimationId = null;
function animateConfetti() {
    if (!confettiCtx || !confettiCanvas) return;
    confettiCtx.clearRect(0, 0, confettiCanvas.width, confettiCanvas.height);

    for (let i = confettiPieces.length - 1; i >= 0; i--) {
        const p = confettiPieces[i];
        p.vx *= p.resistance;
        p.vy *= p.resistance;
        p.vy += p.gravity;
        p.x += p.vx;
        p.y += p.vy;
        p.life -= 1;
        p.opacity = p.life / 120;

        if (p.life <= 0 || p.opacity <= 0) {
            confettiPieces.splice(i, 1);
        } else {
            confettiCtx.globalAlpha = p.opacity;
            confettiCtx.fillStyle = p.color;
            confettiCtx.beginPath();
            confettiCtx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
            confettiCtx.fill();
        }
    }

    if (confettiPieces.length > 0) {
        confettiAnimationId = requestAnimationFrame(animateConfetti);
    } else {
        cancelAnimationFrame(confettiAnimationId);
        confettiAnimationId = null;
    }
}

export function launchConfetti(origin = {}) {
    if (isLowPerf) return; // Отключаем на слабых устройствах
    if (!confettiCanvas) initConfetti();

    const startX = origin.x ?? window.innerWidth / 2;
    const startY = origin.y ?? window.innerHeight / 3;
    const pieceCount = 100;

    for (let i = 0; i < pieceCount; i++) {
        if (confettiPieces.length < 300) { // Ограничение на общее количество частиц
             confettiPieces.push(createConfettiPiece(startX, startY));
        }
    }

    if (!confettiAnimationId) {
        animateConfetti();
    }
}
