import { addBalance, getBalance } from '../../../../core/state.js';

export const title = 'Главная';

// --- Константы ---
const STARS_PER_TAP = 1;

// --- Переменные модуля ---
let root, elements, state;

/**
 * Анимация счётчика-флиппера
 */
function updateFlipCounter(start, end) {
    if (!elements || !elements.balanceCounter) return;
    const container = elements.balanceCounter;
    const endStr = end.toString();
    const startStr = start.toString().padStart(endStr.length, ' ');

    container.innerHTML = '';

    for (let i = 0; i < endStr.length; i++) {
        const charContainer = document.createElement('div');
        charContainer.className = 'flip-char';
        charContainer.innerHTML = `
            <div class="flip-char-inner">
                <div class="flip-char-front">${startStr[i] || ' '}</div>
                <div class="flip-char-back">${endStr[i]}</div>
            </div>
        `;
        container.appendChild(charContainer);
        if (startStr[i] !== endStr[i]) {
            setTimeout(() => charContainer.classList.add('animate'), i * 50);
        }
    }
}

/**
 * Показывает эффекты при тапе: летящий текст
 */
function showTapEffects(x, y) {
    if (!elements || !elements.feedbackContainer) return;
    const container = elements.feedbackContainer;

    const text = document.createElement('div');
    text.className = 'floating-text-new';
    text.textContent = `+${STARS_PER_TAP}`;
    container.appendChild(text);

    text.style.left = `${x}px`;
    text.style.top = `${y}px`;

    const counterRect = elements.balanceCounter.getBoundingClientRect();
    const endX = counterRect.left + counterRect.width / 2;
    const endY = counterRect.top + counterRect.height / 2;

    text.style.setProperty('--fly-to-x', `translateX(${endX - x}px)`);
    text.style.setProperty('--fly-to-y', `translateY(${endY - y}px)`);

    setTimeout(() => text.remove(), 700);
}

/**
 * Основной обработчик тапа
 */
function handleTap(event) {
    const tapX = event.clientX || (event.touches && event.touches[0].clientX);
    const tapY = event.clientY || (event.touches && event.touches[0].clientY);
    if (tapX === undefined) return;

    const oldBalance = getBalance();
    addBalance(STARS_PER_TAP);
    const newBalance = getBalance();

    updateFlipCounter(oldBalance, newBalance);
    showTapEffects(tapX, tapY);

    if (elements.star) {
        elements.star.classList.add('tapped');
        elements.star.addEventListener('animationend', () => {
            elements.star.classList.remove('tapped');
        }, { once: true });
    }

    if (window.ManiacGames) {
       window.ManiacGames.hapticFeedback('light');
    }
}

export function mount(rootEl) {
    root = rootEl;
    state = {};

    root.innerHTML = `
        <style>
            .tapper-star-container {
                width: 100%;
                flex-grow: 1;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                user-select: none;
                -webkit-tap-highlight-color: transparent;
            }
            .tapper-star-2d {
                font-size: 250px;
                line-height: 1;
                color: #f92b75;
                filter: drop-shadow(0 0 25px rgba(249, 43, 117, 0.7));
                transition: transform 0.1s ease-out;
            }
            .tapper-star-2d.tapped {
                animation: star-tap-effect 0.2s ease-out;
            }
            @keyframes star-tap-effect {
                0% { transform: scale(1); }
                50% { transform: scale(0.9); }
                100% { transform: scale(1); }
            }
        </style>
        <div class="tapper-wrapper">
            <div class="tapper-balance-container">
                <span class="tapper-balance-icon">⭐</span>
                <div id="tapper-balance-counter" class="tapper-balance-counter"></div>
            </div>
            <div class="tapper-star-container">
                <div id="tapper-star-2d" class="tapper-star-2d">★</div>
            </div>
            <div id="tap-feedback-container" class="tap-feedback-container"></div>
            <div class="tapper-energy-info"></div>
        </div>
    `;

    elements = {
        balanceCounter: root.querySelector('#tapper-balance-counter'),
        starContainer: root.querySelector('.tapper-star-container'),
        star: root.querySelector('#tapper-star-2d'),
        feedbackContainer: root.querySelector('#tap-feedback-container'),
    };

    updateFlipCounter(0, getBalance());
    elements.starContainer.addEventListener('pointerdown', handleTap);
}

export function unmount() {
    root = null;
    elements = null;
    state = null;
}
