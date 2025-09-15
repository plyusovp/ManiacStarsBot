// --- Высокопроизводительная система частиц на Canvas ---

let MAX_PARTICLES = 150; // Максимальное кол-во частиц на экране
const particlePool = [];
const activeParticles = [];
let canvas, ctx;
let lastTime = 0;
let isLowPerf = false; // <-- Флаг низкой производительности

/**
 * Инициализирует систему частиц.
 * @param {HTMLCanvasElement} canvasElement - Элемент canvas для отрисовки.
 */
export function init(canvasElement) {
    if (!canvasElement) {
        console.error("Particle system requires a canvas element.");
        return;
    }
    canvas = canvasElement;
    ctx = canvas.getContext('2d');

    // --- Оптимизация: Проверяем режим низкой производительности ---
    isLowPerf = document.body.classList.contains('low-perf');
    if (isLowPerf) {
        MAX_PARTICLES = 40; // Значительно уменьшаем лимит
    }

    // --- Инициализация пула частиц ---
    for (let i = 0; i < MAX_PARTICLES; i++) {
        particlePool.push({ active: false /* ... other properties */ });
    }

    resize();
    window.addEventListener('resize', resize);
}

function resize() {
    if(!canvas) return;
    const dpr = window.devicePixelRatio || 1;
    canvas.width = window.innerWidth * dpr;
    canvas.height = window.innerHeight * dpr;
    canvas.style.width = `${window.innerWidth}px`;
    canvas.style.height = `${window.innerHeight}px`;
    ctx.scale(dpr, dpr);
}

/**
 * Создает "эмиттер" - источник частиц.
 * @param {number} x - Начальная координата X.
 * @param {number} y - Начальная координата Y.
 * @param {object} options - Конфигурация частиц.
 */
export function emit(x, y, options = {}) {
    let count = options.count || 10;

    // --- Оптимизация: уменьшаем количество частиц в режиме low-perf ---
    if (isLowPerf) {
        count = Math.floor(count / 3);
    }

    for (let i = 0; i < count; i++) {
        if (activeParticles.length >= MAX_PARTICLES) return;

        let p = particlePool.find(p => !p.active);
        if (!p) p = {}; // Fallback if pool is somehow smaller than MAX

        p.active = true;
        p.x = x;
        p.y = y;

        const angle = (Math.random() * (options.angle ?? Math.PI * 2)) + (options.angleOffset || 0);
        const speed = Math.random() * (options.speed || 2);

        p.vx = Math.cos(angle) * speed;
        p.vy = Math.sin(angle) * speed;

        p.ay = options.gravity || 0;

        p.maxLife = p.life = (options.life || 60) + Math.random() * 20 - 10;
        p.alpha = 1;
        p.size = Math.max(0.5, (options.size || 2) + Math.random() * 1.5);
        p.friction = options.friction || 0.98;

        if (Array.isArray(options.color)) {
            p.color = options.color[Math.floor(Math.random() * options.color.length)];
        } else {
            p.color = options.color || '#FFFFFF';
        }

        activeParticles.push(p);
    }
}

function update(delta) {
    const effectiveDelta = Math.min(delta, 1/30) * 60;

    for (let i = activeParticles.length - 1; i >= 0; i--) {
        const p = activeParticles[i];

        p.life -= effectiveDelta;

        if (p.life <= 0 || p.alpha < 0.05) {
            p.active = false;
            activeParticles.splice(i, 1);
            continue;
        }

        p.vy += p.ay * effectiveDelta;
        p.x += p.vx * effectiveDelta;
        p.y += p.vy * effectiveDelta;

        p.alpha = p.life / p.maxLife;
    }
}

function draw() {
    if (!ctx || !canvas) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    for (const p of activeParticles) {
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2, false);
        ctx.fillStyle = p.color;
        ctx.globalAlpha = p.alpha;
        ctx.fill();
    }
    ctx.globalAlpha = 1.0;
}

export function loop(timestamp) {
    const delta = (timestamp - (lastTime || timestamp)) / 1000;
    lastTime = timestamp;

    update(delta);
    draw();

    requestAnimationFrame(loop);
}
