import { getBalance, subBalance, addBalance, updateStats } from '../lib/balance.js';
import { applyPayout } from '../lib/houseedge.js';
import { randomInt } from '../lib/rng.js';

export const titleKey = 'dice_game_title';

// --- Game Payouts ---
const PAYOUT_EVEN_ODD = 1.9;
const PAYOUT_EXACT = 5.5;

// --- State ---
let root, elements, state;
const t = window.ManiacGames.t;

function resetState() {
    state = {
        isRolling: false,
        betAmount: 10,
        betType: null, // 'even', 'odd', or a number 1-6
        lastResult: 0,
    };
}


function getDiceFace(value) {
    // ... (код getDiceFace без изменений)
    const dotPositions = {
        1: '<div class="dot d-center"></div>',
        2: '<div class="dot d-top-left"></div><div class="dot d-bottom-right"></div>',
        3: '<div class="dot d-top-left"></div><div class="dot d-center"></div><div class="dot d-bottom-right"></div>',
        4: '<div class="dot d-top-left"></div><div class="dot d-top-right"></div><div class="dot d-bottom-left"></div><div class="dot d-bottom-right"></div>',
        5: '<div class="dot d-top-left"></div><div class="dot d-top-right"></div><div class="dot d-center"></div><div class="dot d-bottom-left"></div><div class="dot d-bottom-right"></div>',
        6: '<div class="dot d-top-left"></div><div class="dot d-top-right"></div><div class="dot d-mid-left"></div><div class="dot d-mid-right"></div><div class="dot d-bottom-left"></div><div class="dot d-bottom-right"></div>',
    };
    return dotPositions[value] || '';
}

async function rollDice(targetFace) {
    state.isRolling = true;
    window.ManiacGames.playSound('spinStart');
    window.ManiacGames.hapticFeedback('medium');
    elements.dice.classList.add('rolling');

    const rollDuration = 1500;
    return new Promise(resolve => {
         const interval = setInterval(() => {
            const randomFace = randomInt(1, 6);
            elements.dice.innerHTML = getDiceFace(randomFace);
        }, 80);

        setTimeout(() => {
            clearInterval(interval);
            elements.dice.innerHTML = getDiceFace(targetFace);
            elements.dice.classList.remove('rolling');
            state.isRolling = false;
            window.ManiacGames.playSound('spinStop');
            resolve();
        }, rollDuration);
    });
}

async function playGame(betType) {
    if (state.isRolling) return;
    if (getBalance() < state.betAmount) {
        window.ManiacGames.showNotification(t('not_enough_funds'), 'error');
        return;
    }

    state.betType = isNaN(betType) ? betType : parseInt(betType, 10);

    subBalance(state.betAmount);
    window.ManiacGames.updateBalance();

    const result = randomInt(1, 6);
    elements.resultText.textContent = '...';

    await rollDice(result);

    let isWin = false;
    let payoutMultiplier = 0;

    if (state.betType === 'even' && result % 2 === 0) {
        isWin = true;
        payoutMultiplier = PAYOUT_EVEN_ODD;
    } else if (state.betType === 'odd' && result % 2 !== 0) {
        isWin = true;
        payoutMultiplier = PAYOUT_EVEN_ODD;
    } else if (typeof state.betType === 'number' && state.betType === result) {
        isWin = true;
        payoutMultiplier = PAYOUT_EXACT;
    }

    if (isWin) {
        const payout = applyPayout(state.betAmount * payoutMultiplier);
        addBalance(payout);
        updateStats({ wins: 1, topWin: payout });
        elements.resultText.textContent = `${t('win_message')} +${payout} ⭐`;
        elements.resultText.style.color = 'var(--success)';
        window.ManiacGames.playSound('win');
        window.ManiacGames.hapticFeedback('success');
    } else {
        updateStats({ losses: 1 });
        elements.resultText.textContent = `${t('loss_message')} -${state.betAmount} ⭐`;
        elements.resultText.style.color = 'var(--danger)';
        window.ManiacGames.playSound('lose');
        window.ManiacGames.hapticFeedback('error');
    }
    window.ManiacGames.updateBalance();
}

function bindEvents() {
    elements.betInput.addEventListener('change', e => {
        const value = parseInt(e.target.value, 10);
        state.betAmount = isNaN(value) || value < 1 ? 1 : value;
        e.target.value = state.betAmount;
    });

    elements.betControls.addEventListener('click', e => {
        const button = e.target.closest('button');
        if (button && button.dataset.bet) {
            window.ManiacGames.playSound('tap');
            playGame(button.dataset.bet);
        }
    });
}


export function mount(rootEl) {
    root = rootEl;
    resetState();
    root.innerHTML = `
        <div class="card dice-2d-container">
            <div id="dice-2d-face" class="dice-face">
                ${getDiceFace(6)}
            </div>
        </div>
        <div class="card">
             <div id="dice-result" style="text-align:center; font-weight:bold; min-height: 1.2em; margin-bottom:15px;">${t('dice_make_bet')}</div>
             <input type="number" id="dice-bet-input" class="input-field" value="${state.betAmount}">
             <div id="dice-bet-controls" class="chip-controls" style="grid-template-columns: 1fr 1fr; margin-top:15px;">
                <button class="btn" data-bet="even">${t('dice_even')} (x${PAYOUT_EVEN_ODD})</button>
                <button class="btn" data-bet="odd">${t('dice_odd')} (x${PAYOUT_EVEN_ODD})</button>
             </div>
             <div class="chip-controls" style="grid-template-columns: repeat(3, 1fr);">
                <button class="btn chip" data-bet="1">1</button>
                <button class="btn chip" data-bet="2">2</button>
                <button class="btn chip" data-bet="3">3</button>
                <button class="btn chip" data-bet="4">4</button>
                <button class="btn chip" data-bet="5">5</button>
                <button class="btn chip" data-bet="6">6</button>
             </div>
             <p style="text-align:center; font-size:0.8rem; color: var(--muted); margin-top:10px;">${t('dice_exact_bet')} (x${PAYOUT_EXACT})</p>
        </div>
    `;

    elements = {
        dice: root.querySelector('#dice-2d-face'),
        betInput: root.querySelector('#dice-bet-input'),
        betControls: root.querySelector('#dice-bet-controls'),
        resultText: root.querySelector('#dice-result'),
    };

    bindEvents();
}

export function unmount() {
    root = null;
    elements = null;
    state = null;
}
