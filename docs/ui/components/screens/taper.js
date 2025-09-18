import { addBalance, getBalance } from '../../../../core/state.js';

export const titleKey = 'taper_title';

// --- Константы ---
const STARS_PER_TAP = 1;

// --- Переменные модуля ---
let root, elements, state;

/**
 * Анимация счётчика-флиппера
 */
function updateFlipCounter(start, end) {
    const container = elements.balanceCounter;
    const endStr = end.toString();
    const startStr = start.toString().padStart(endStr.length, ' ');

    container.innerHTML = '';

    for (let i = 0; i < endStr.length; i++) {
        const charContainer = document.createElement('div');
        charContainer.className = 'flip-char';

        const s1 = startStr[i] || ' ';
        const s2 = endStr[i];

        charContainer.innerHTML = `
            <div class="flip-char-inner">
                <div class="flip-char-front">${s1}</div>
                <div class="flip-char-back">${s2}</div>
            </div>
        `;
        container.appendChild(charContainer);

        if (s1 !== s2) {
            setTimeout(() => {
                charContainer.classList.add('animate');
                window.ManiacGames.playSound('counterTick', { delay: Math.random() * 0.2 });
            }, i * 50);
        }
    }
}

/**
 * Показывает эффекты при тапе: летящий текст
 */
function showTapEffects(x, y) {
    const container = elements.feedbackContainer;

    const text = document.createElement('div');
    text.className = 'floating-text-new';
    text.textContent = `+${STARS_PER_TAP}`;
    container.appendChild(text);

    text.style.left = `${x}px`;
    text.style.top = `${y}px`;

    // Анимация просто вверх и исчезновение
    text.style.setProperty('--fly-to-x', `translateX(-50%)`);
    text.style.setProperty('--fly-to-y', `translateY(-150px)`);


    window.ManiacGames.playSound('swoosh');
    setTimeout(() => text.remove(), 1000);
}

/**
 * Основной обработчик тапа
 */
function handleTap(event) {
    const starEl = elements.star;
    // Анимация сжатия
    starEl.classList.add('tapped');
    setTimeout(() => starEl.classList.remove('tapped'), 150);

    const tapX = event.clientX || (event.touches && event.touches[0].clientX);
    const tapY = event.clientY || (event.touches && event.touches[0].clientY);

    if (tapX === undefined) return;

    const oldBalance = getBalance();
    addBalance(STARS_PER_TAP);
    const newBalance = getBalance();

    updateFlipCounter(oldBalance, newBalance);
    showTapEffects(tapX, tapY);

    window.ManiacGames.playSound('crystalClick');
    window.ManiacGames.hapticFeedback('light');
}

export function mount(rootEl) {
    root = rootEl;
    state = {};

    root.innerHTML = `
        <div class="tapper-wrapper">
            <div class="tapper-balance-container">
                <span class="tapper-balance-icon">⭐</span>
                <div id="tapper-balance-counter" class="tapper-balance-counter"></div>
            </div>

            <div id="tapper-star-container" class="tapper-star-container">
                <div id="tapper-star" class="star-2d"></div>
            </div>

            <div id="tap-feedback-container" class="tap-feedback-container"></div>

            <div class="tapper-energy-info">
                <!-- Placeholder for future energy bar -->
            </div>
        </div>
    `;

    elements = {
        balanceCounter: root.querySelector('#tapper-balance-counter'),
        starContainer: root.querySelector('#tapper-star-container'),
        star: root.querySelector('#tapper-star'),
        feedbackContainer: root.querySelector('#tap-feedback-container'),
    };

    updateFlipCounter(0, getBalance());

    elements.starContainer.addEventListener('pointerdown', handleTap);
}

export function unmount() {
    // Очищаем ресурсы, если нужно
    root = null;
    elements = null;
    state = null;
}
