import { getBalance, subBalance, addBalance, updateStats } from '../lib/balance.js';
import { applyPayout } from '../lib/houseedge.js';
import { weightedRandom } from '../lib/rng.js';

export const title = 'Слоты';

// --- Game Parameters ---
const SYMBOLS = ['🍒', '🍋', '🍇', '🔔', '⭐', '💎'];
const WEIGHTS = { '🍒': 40, '🍋': 30, '🍇': 15, '🔔': 10, '⭐': 4, '💎': 1 };
const PAYOUT_RULES = [
    { combo: ['💎', '💎', '💎'], multiplier: 100 },
    { combo: ['⭐', '⭐', '⭐'], multiplier: 50 },
    { combo: ['🔔', '🔔', '🔔'], multiplier: 20 },
    { combo: ['🍇', '🍇', '🍇'], multiplier: 10 },
    { combo: ['🍋', '🍋', '🍋'], multiplier: 5 },
    { combo: ['🍒', '🍒', '🍒'], multiplier: 3 },
    // Special rule for two stars
    { check: (r) => r.filter(s => s === '⭐').length === 2, multiplier: 3 },
    // Any two identical (except diamond)
    { check: (r) => {
        const counts = r.reduce((acc, val) => { if(val !== '💎') acc[val] = (acc[val] || 0) + 1; return acc; }, {});
        return Object.values(counts).some(count => count === 2);
    }, multiplier: 1.5 },
];


// --- State ---
let root, elements, state;

function resetState() {
    state = {
        isSpinning: false,
        betAmount: 10,
        reels: ['🍒', '🍋', '🍇'],
    };
}

function calculateWinnings(result) {
    for (const rule of PAYOUT_RULES) {
        if (rule.combo) {
            if (result.every((symbol, i) => symbol === rule.combo[i])) {
                return state.betAmount * rule.multiplier;
            }
        } else if (rule.check) {
            if (rule.check(result)) {
                return state.betAmount * rule.multiplier;
            }
        }
    }
    return 0;
}

async function spin() {
    if (state.isSpinning) return;
    if (getBalance() < state.betAmount) {
        window.ManiacGames.showNotification('Недостаточно средств', 'error');
        return;
    }

    state.isSpinning = true;
    subBalance(state.betAmount);
    window.ManiacGames.updateBalance();
    window.ManiacGames.playSound('spinStart');
    window.ManiacGames.hapticFeedback('medium');

    elements.spinButton.disabled = true;
    elements.winMessage.textContent = '';
    elements.reels.forEach(r => r.classList.remove('win', 'skeleton-pulse')); // Убираем скелет при старте

    // Generate result beforehand
    const result = [weightedRandom(WEIGHTS), weightedRandom(WEIGHTS), weightedRandom(WEIGHTS)];

    // Animate reels
    for (let i = 0; i < elements.reels.length; i++) {
        await animateReel(elements.reels[i], result[i]);
        window.ManiacGames.playSound('spinStop');
    }

    // Calculate and process winnings
    const winnings = calculateWinnings(result);
    if (winnings > 0) {
        const finalPayout = applyPayout(winnings);
        addBalance(finalPayout);
        updateStats({ wins: 1, topWin: finalPayout });
        elements.winMessage.textContent = `Выигрыш +${finalPayout} ⭐`;
        elements.reels.forEach(r => r.classList.add('win'));
        window.ManiacGames.playSound('win');
        window.ManiacGames.hapticFeedback('success');
    } else {
        updateStats({ losses: 1 });
        window.ManiacGames.playSound('lose'); // <-- Звук проигрыша
        window.ManiacGames.hapticFeedback('error');
    }

    window.ManiacGames.updateBalance();
    state.isSpinning = false;
    elements.spinButton.disabled = false;
}

async function animateReel(reelEl, finalSymbol) {
    const animationDuration = 1000 + Math.random() * 500;
    const startTime = performance.now();

    return new Promise(resolve => {
        function tick(currentTime) {
            const elapsed = currentTime - startTime;
            reelEl.textContent = SYMBOLS[Math.floor(Math.random() * SYMBOLS.length)];

            if (elapsed < animationDuration) {
                requestAnimationFrame(tick);
            } else {
                reelEl.textContent = finalSymbol;
                resolve();
            }
        }
        requestAnimationFrame(tick);
    });
}


function bindEvents() {
    elements.spinButton.addEventListener('click', spin);
    elements.betInput.addEventListener('change', e => {
        const val = parseInt(e.target.value, 10);
        state.betAmount = Math.max(1, isNaN(val) ? 1 : val);
    });
    elements.chipControls.addEventListener('click', e => {
        if (e.target.classList.contains('chip')) {
            const value = parseInt(e.target.dataset.value, 10);
            state.betAmount = value;
            elements.betInput.value = value;
            window.ManiacGames.playSound('tap');
        }
    });
}


export function mount(rootEl) {
    root = rootEl;
    resetState();
    root.innerHTML = `
        <div class="card">
            <div class="reels-container">
                <div class="reel skeleton-pulse"></div>
                <div class="reel skeleton-pulse"></div>
                <div class="reel skeleton-pulse"></div>
            </div>
        </div>
        <div class="card">
            <div id="slots-win-message" class="win-message" style="text-align:center; font-weight:bold; min-height: 1.2em; margin-bottom:15px; color:var(--success);"></div>
            <input type="number" id="slots-bet-input" class="input-field" value="${state.betAmount}">
            <div id="slots-chip-controls" class="chip-controls">
                <button class="btn chip" data-value="1">1</button>
                <button class="btn chip" data-value="5">5</button>
                <button class="btn chip" data-value="10">10</button>
                <button class="btn chip" data-value="25">25</button>
                <button class="btn chip" data-value="50">50</button>
                <button class="btn chip" data-value="100">100</button>
            </div>
            <button id="slots-spin-button" class="btn btn-success">Крутить</button>
        </div>
    `;

    elements = {
        reels: root.querySelectorAll('.reel'),
        winMessage: root.querySelector('#slots-win-message'),
        betInput: root.querySelector('#slots-bet-input'),
        chipControls: root.querySelector('#slots-chip-controls'),
        spinButton: root.querySelector('#slots-spin-button'),
    };

    // Имитируем "загрузку" слотов и заменяем скелеты на символы
    setTimeout(() => {
        if (!root) return; // Проверка, что компонент всё ещё смонтирован
        elements.reels.forEach((reel, i) => {
            reel.classList.remove('skeleton-pulse');
            reel.textContent = state.reels[i];
        });
    }, 500);


    bindEvents();
}

export function unmount() {
    root = null;
    elements = null;
    state = null;
}
