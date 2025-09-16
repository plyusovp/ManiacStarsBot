import { addBalance, getBalance, fmt } from '../../core/state.js';

export const title = 'Главная';

// --- Game Parameters ---
const STARS_PER_TAP = 1;
const TAP_LIMIT_PER_SECOND = 16; // Ограничение скорости
const AUTOCLICKER_THRESHOLD = 30; // Кол-во быстрых тапов для подозрения
const AUTOCLICKER_COOLDOWN = 120; // ms

// --- State ---
let root, elements, state;
let tapTimestamps = [];
let fastTapCounter = 0;
let isCooldown = false;

function resetState() {
    state = {
        currentBalance: getBalance(),
    };
}

// --- Counter Animation ---
function animateCounter(start, end) {
    let current = start;
    const range = end - start;
    if (range === 0) return;
    const duration = 500; // ms
    let startTime = null;

    function step(timestamp) {
        if (!startTime) startTime = timestamp;
        const progress = Math.min((timestamp - startTime) / duration, 1);
        current = Math.floor(progress * range + start);
        elements.balanceCounter.textContent = fmt(current);
        if (progress < 1) {
            requestAnimationFrame(step);
        } else {
            elements.balanceCounter.textContent = fmt(end); // Убедимся, что финальное значение верное
        }
    }
    requestAnimationFrame(step);
}


// --- DOM Particle Generation ---
// Эта система использует DOM-элементы (div).
// Она отлично подходит для простых, нечастых эффектов, как здесь.
// Для более 100 частиц или постоянных эффектов лучше использовать <canvas>,
// как это сделано в игре Crash.
function createParticles(x, y) {
    const particleCount = 6 + Math.floor(Math.random() * 5); // 6-10 частиц
    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        const isRay = Math.random() < 0.15; // 15% шанс быть "лучом"

        particle.className = isRay ? 'particle ray' : 'particle';
        elements.particleContainer.appendChild(particle);

        const angle = Math.random() * Math.PI * 2;
        const distance = 50 + Math.random() * 40;
        const duration = 500 + Math.random() * 300;

        // Начальные стили
        particle.style.left = `${x}px`;
        particle.style.top = `${y}px`;
        particle.style.setProperty('--angle', angle);
        particle.style.setProperty('--distance', `${distance}px`);
        particle.style.setProperty('--duration', `${duration}ms`);
        if (isRay) {
             particle.style.setProperty('--rotation', `${Math.random() * 360}deg`);
        }

        // Удаляем частицу после анимации для очистки DOM.
        setTimeout(() => particle.remove(), duration);
    }
}

// --- Floating Text ---
function showFloatingText(x, y) {
    const text = document.createElement('div');
    text.className = 'floating-text';
    text.textContent = `+${STARS_PER_TAP}`;
    root.appendChild(text);

    text.style.left = `${x}px`;
    text.style.top = `${y}px`;

    setTimeout(() => text.remove(), 1500);
}


// --- Main Tap Handler ---
function handleTap(event) {
    if (isCooldown) return;

    const now = Date.now();

    // 1. Ограничение скорости (Rate Limiter)
    tapTimestamps = tapTimestamps.filter(ts => now - ts < 1000);
    if (tapTimestamps.length >= TAP_LIMIT_PER_SECOND) {
        return; // Игнорируем тап
    }
    tapTimestamps.push(now);

    // 2. Анти-автокликер
    if (tapTimestamps.length > 1) {
        const lastTapTime = tapTimestamps[tapTimestamps.length - 2];
        if (now - lastTapTime < 60) { // Очень быстрый тап
            fastTapCounter++;
        } else {
            fastTapCounter = 0;
        }
    }
    if (fastTapCounter >= AUTOCLICKER_THRESHOLD) {
        isCooldown = true;
        setTimeout(() => {
            isCooldown = false;
            fastTapCounter = 0;
        }, AUTOCLICKER_COOLDOWN);
        return;
    }


    // Координаты для эффектов
    const rect = elements.tapperCircle.getBoundingClientRect();
    const tapX = event.clientX || event.touches[0].clientX;
    const tapY = event.clientY || event.touches[0].clientY;

    // 3. Обновляем баланс
    const oldBalance = state.currentBalance;
    state.currentBalance += STARS_PER_TAP;
    addBalance(STARS_PER_TAP);
    animateCounter(oldBalance, state.currentBalance);

    // 4. Эффекты
    createParticles(tapX - rect.left, tapY - rect.top);
    showFloatingText(tapX, tapY);

    // 5. Анимации
    elements.tapperCircle.classList.remove('tapped');
    void elements.tapperCircle.offsetWidth; // трюк для перезапуска анимации
    elements.tapperCircle.classList.add('tapped');


    // 6. Звук и вибрация
    window.ManiacGames.playSound('click');
    window.ManiacGames.hapticFeedback('light');
}

export function mount(rootEl) {
    root = rootEl;
    resetState();

    root.innerHTML = `
        <div class="tapper-wrapper">
            <div class="tapper-balance-container">
                <span class="tapper-balance-icon">⭐</span>
                <h1 id="tapper-balance-counter" class="tapper-balance-counter">${fmt(state.currentBalance)}</h1>
            </div>

            <div class="tapper-area">
                <div id="particle-container"></div>
                <div class="tapper-glow"></div>
                <div id="tapper-circle" class="tapper-circle">
                    <svg class="tapper-star-svg" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
                        <defs>
                            <linearGradient id="starGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                                <stop offset="0%" style="stop-color:var(--primary-1)" />
                                <stop offset="100%" style="stop-color:var(--primary-2)" />
                            </linearGradient>
                            <filter id="inner-glow">
                               <feMorphology operator="dilate" radius="1" in="SourceAlpha" result="thicken" />
                               <feGaussianBlur in="thicken" stdDeviation="2" result="blurred" />
                               <feFlood flood-color="rgba(255,255,255,0.5)" result="glowColor" />
                               <feComposite in="glowColor" in2="blurred" operator="in" result="softGlow_colored" />
                               <feMerge>
                                  <feMergeNode in="softGlow_colored"/>
                                  <feMergeNode in="SourceGraphic"/>
                               </feMerge>
                            </filter>
                        </defs>
                        <path fill="url(#starGradient)" filter="url(#inner-glow)" d="M50,5 L61.8,38.2 L97.5,38.2 L67.8,58.8 L79.6,91 L50,69.4 L20.4,91 L32.2,58.8 L2.5,38.2 L38.2,38.2 Z"/>
                    </svg>
                </div>
                <div class="tapper-shadow"></div>
            </div>

             <div class="tapper-energy-info">
                <!-- Место для полосы энергии, если понадобится -->
             </div>
        </div>
    `;

    elements = {
        balanceCounter: root.querySelector('#tapper-balance-counter'),
        tapperCircle: root.querySelector('#tapper-circle'),
        particleContainer: root.querySelector('#particle-container'),
    };

    // Используем 'pointerdown' для более быстрой реакции на тап
    elements.tapperCircle.addEventListener('pointerdown', handleTap);
    elements.tapperCircle.addEventListener('animationend', () => {
        elements.tapperCircle.classList.remove('tapped');
    })
}

export function unmount() {
    root = null;
    elements = null;
    state = null;
    tapTimestamps = [];
}
