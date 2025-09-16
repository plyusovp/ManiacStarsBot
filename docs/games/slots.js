import { getBalance, subBalance, addBalance, updateStats } from '../core/state.js';
import { applyPayout } from '../core/houseedge.js';
import { weightedRandom } from '../core/rng.js';

export const titleKey = 'slots_game_title';

const SYMBOLS = ['🍒', '🍋', '🍇', '🔔', '⭐', '💎'];
const WEIGHTS = { '🍒': 40, '🍋': 30, '🍇': 15, '🔔': 10, '⭐': 4, '💎': 1 };
const PAYOUT_RULES = [
    { combo: ['💎', '💎', '💎'], multiplier: 100 },
    { combo: ['⭐', '⭐', '⭐'], multiplier: 50 },
    { combo: ['🔔', '🔔', '🔔'], multiplier: 20 },
    { combo: ['🍇', '🍇', '🍇'], multiplier: 10 },
    { combo: ['🍋', '🍋', '🍋'], multiplier: 5 },
    { combo: ['🍒', '🍒', '🍒'], multiplier: 3 },
    { check: (r) => r.filter(s => s === '⭐').length === 2, multiplier: 3 },
    { check: (r) => {
        const counts = r.reduce((acc, val) => { if(val !== '💎') acc[val] = (acc[val] || 0) + 1; return acc; }, {});
        return Object.values(counts).some(count => count === 2);
    }, multiplier: 1.5 },
];

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
    const t = window.ManiacGames.t;

    if (getBalance() < state.betAmount) {
        window.ManiacGames.showNotification(t('not_enough_funds'), 'error');
        return;
    }

    state.isSpinning = true;
    subBalance(state.betAmount);
    window.ManiacGames.updateBalance();
    window.ManiacGames.playSound('spinStart');
    window.ManiacGames.hapticFeedback('medium');

    elements.spinButton.disabled = true;
    elements.winMessage.textContent = '';
    elements.reels.forEach(r => r.classList.remove('win'));

    const result = [weightedRandom(WEIGHTS), weightedRandom(WEIGHTS), weightedRandom(WEIGHTS)];
    const animationPromises = [];
    for (let i = 0; i < elements.reels.length; i++) {
        animationPromises.push(animateReel(elements.reels[i], result[i], i));
    }
    await Promise.all(animationPromises);

    const winnings = calculateWinnings(result);
    if (winnings > 0) {
        const finalPayout = applyPayout(winnings);
        addBalance(finalPayout);
        updateStats({ wins: 1, topWin: finalPayout });
        elements.winMessage.textContent = `${t('win_message')} +${finalPayout} ⭐`;
        elements.reels.forEach(r => r.classList.add('win'));
        window.ManiacGames.playSound('win');
        window.ManiacGames.hapticFeedback('success');
    } else {
        updateStats({ losses: 1 });
        window.ManiacGames.playSound('lose');
        window.ManiacGames.hapticFeedback('error');
    }

    window.ManiacGames.updateBalance();
    state.isSpinning = false;
    elements.spinButton.disabled = false;
}

function animateReel(reelEl, finalSymbol, reelIndex) {
    const animationDuration = 1000 + reelIndex * 300 + Math.random() * 200;
    const startTime = performance.now();

    return new Promise(resolve => {
        function tick(currentTime) {
            const elapsed = currentTime - startTime;
            reelEl.textContent = SYMBOLS[Math.floor(Math.random() * SYMBOLS.length)];

            if (elapsed < animationDuration) {
                requestAnimationFrame(tick);
            } else {
                reelEl.textContent = finalSymbol;
                window.ManiacGames.playSound('spinStop');
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
        const chip = e.target.closest('.chip');
        if (chip) {
            const value = parseInt(chip.dataset.value, 10);
            state.betAmount = value;
            elements.betInput.value = value;
            window.ManiacGames.playSound('tap');
        }
    });
}

export function mount(rootEl) {
    root = rootEl;
    resetState();
    const t = window.ManiacGames.t;

    root.innerHTML = `
        <style>
        .reels-container { display: flex; justify-content: center; gap: 15px; margin-bottom: 20px; }
        .reel { width: 80px; height: 100px; background: var(--bg-soft); border-radius: 10px; display: flex; justify-content: center; align-items: center; font-size: 3rem; transition: all 0.2s; }
        .reel.win { background: var(--accent); color: white; transform: scale(1.1); box-shadow: 0 0 20px var(--accent); }
        </style>
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
                <button class="btn chip" data-value="10">10</button>
                <button class="btn chip" data-value="25">25</button>
                <button class="btn chip" data-value="50">50</button>
                <button class="btn chip" data-value="100">100</button>
            </div>
            <button id="slots-spin-button" class="btn btn-success">${t('slots_spin')}</button>
        </div>
    `;

    elements = {
        reels: root.querySelectorAll('.reel'),
        winMessage: root.querySelector('#slots-win-message'),
        betInput: root.querySelector('#slots-bet-input'),
        chipControls: root.querySelector('#slots-chip-controls'),
        spinButton: root.querySelector('#slots-spin-button'),
    };

    setTimeout(() => {
        if (!root) return;
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
