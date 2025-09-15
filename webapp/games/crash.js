import { getBalance, subBalance, addBalance, updateStats } from '../lib/balance.js';
import { applyPayout } from '../lib/houseedge.js';

export const title = 'Crash';

// --- Game Parameters (for RTP tuning) ---
const CRASH_ALPHA = 1.6; // Higher = more frequent low multipliers
const CRASH_MIN = 1.00;
const CRASH_MAX = 100.0;
const BETTING_WINDOW_MS = 7000;

// --- State ---
let root, elements, state;
let animationFrameId;

function resetState() {
    state = {
        gameState: 'betting', // betting, running, crashed
        betAmount: 10,
        stake: 0,
        multiplier: 1.00,
        crashPoint: 0,
        startTime: 0,
        history: state ? state.history : [],
        cashedOut: false,
        countdown: BETTING_WINDOW_MS / 1000,
    };
}

/**
 * Generates the crash point. The math ensures RTP can be tuned.
 * The formula creates a distribution where lower multipliers are more common.
 * @returns {number} The multiplier at which the game will crash.
 */
function generateCrashPoint() {
    const u = Math.random();
    // Inverse transform sampling for a power-law distribution
    const point = Math.pow(1 / (1 - u), 1 / CRASH_ALPHA);
    return Math.min(CRASH_MAX, Math.max(CRASH_MIN, point));
}

function updateUI() {
    if (!root) return;
    elements.betInput.value = state.betAmount;
    elements.multiplierText.textContent = `${state.multiplier.toFixed(2)}x`;

    // Colorize multiplier text
    if (state.gameState === 'crashed') {
        elements.multiplierText.style.color = 'var(--danger)';
    } else if (state.cashedOut) {
        elements.multiplierText.style.color = 'var(--success)';
    } else {
        elements.multiplierText.style.color = 'var(--text)';
    }

    // Update main button text and state
    switch (state.gameState) {
        case 'betting':
            elements.betButton.disabled = false;
            elements.betButton.className = 'btn btn-success';
            elements.betButton.textContent = `Сделать ставку (${state.countdown}с)`;
            break;
        case 'running':
            if (state.stake > 0 && !state.cashedOut) {
                const potentialWin = Math.floor(state.stake * state.multiplier);
                elements.betButton.disabled = false;
                elements.betButton.className = 'btn btn-warning';
                elements.betButton.textContent = `Забрать ${potentialWin} ⭐`;
            } else {
                elements.betButton.disabled = true;
                elements.betButton.className = 'btn';
                elements.betButton.textContent = 'Приём ставок завершён';
            }
            break;
        case 'crashed':
            elements.betButton.disabled = true;
            elements.betButton.className = 'btn btn-danger';
            elements.betButton.textContent = 'Краш!';
            break;
    }
    updateHistory();
    drawCurve();
}

function updateHistory() {
    elements.history.innerHTML = state.history.slice(0, 10).map(m => {
        let color = 'var(--danger)';
        if (m > 2.0) color = 'var(--success)';
        else if (m > 1.2) color = 'var(--warning)';
        return `<span class="history-item" style="background-color: ${color}20; color: ${color};">${m.toFixed(2)}x</span>`;
    }).join('');
}


function drawCurve() {
    const ctx = elements.canvas.getContext('2d');
    const { width, height } = elements.canvas;
    ctx.clearRect(0, 0, width, height);

    ctx.strokeStyle = 'rgba(159, 80, 255, 0.8)';
    ctx.lineWidth = 4;
    ctx.shadowBlur = 10;
    ctx.shadowColor = 'rgba(159, 80, 255, 0.5)';
    ctx.beginPath();
    ctx.moveTo(0, height);

    const duration = state.startTime ? (performance.now() - state.startTime) / 1000 : 0;
    // Logarithmic scaling for better visualization of high multipliers
    const maxX = Math.log(state.crashPoint || 20);
    const maxY = state.crashPoint || 20;

    for (let t = 0; t <= duration; t += 0.02) {
        const m = 1.00 * Math.pow(1.05, t * 2); // Exponential growth
        const x = (Math.log(m) / maxX) * width;
        const y = height - (m / maxY) * height;
        if(y > 0) ctx.lineTo(x, y);
    }
    ctx.stroke();
    ctx.shadowBlur = 0;
}


function gameLoop(timestamp) {
    if (state.gameState !== 'running') return;

    const elapsedSeconds = (timestamp - state.startTime) / 1000;
    state.multiplier = 1.00 * Math.pow(1.05, elapsedSeconds * 2);

    if (state.multiplier >= state.crashPoint) {
        state.multiplier = state.crashPoint;
        state.gameState = 'crashed';

        state.history.unshift(state.multiplier);
        updateStats({ maxCrashMultiplier: state.multiplier });

        if (state.stake > 0 && !state.cashedOut) {
            updateStats({ losses: 1 });
            window.ManiacGames.hapticFeedback('error');
        }

        window.ManiacGames.playSound('crash');
        updateUI();
        setTimeout(startNewRound, 2000); // 2s pause before new round
    } else {
        updateUI();
        animationFrameId = requestAnimationFrame(gameLoop);
    }
}

function startNewRound() {
    if (animationFrameId) cancelAnimationFrame(animationFrameId);
    resetState();
    state.crashPoint = generateCrashPoint();
    console.log(`Next crash at: ${state.crashPoint.toFixed(2)}x`);

    const countdownInterval = setInterval(() => {
        state.countdown--;
        if (state.countdown <= 0) {
            clearInterval(countdownInterval);
            if (state.gameState === 'betting') {
                 state.gameState = 'running';
                 state.startTime = performance.now();
                 window.ManiacGames.playSound('whoosh');
                 animationFrameId = requestAnimationFrame(gameLoop);
            }
        }
        updateUI();
    }, 1000);

    updateUI();
}

function handleBet() {
    if (state.gameState === 'betting' && state.stake === 0) {
        const bet = state.betAmount;
        if (bet <= 0) return;
        if (getBalance() < bet) {
            window.ManiacGames.showNotification('Недостаточно средств', 'error');
            return;
        }
        subBalance(bet);
        state.stake = bet;
        window.ManiacGames.updateBalance();
        window.ManiacGames.hapticFeedback('medium');
        elements.betButton.textContent = 'Ставка принята';
        elements.betButton.disabled = true;
    }
}

function handleCashout() {
     if (state.gameState === 'running' && state.stake > 0 && !state.cashedOut) {
        const payout = applyPayout(state.stake * state.multiplier);
        addBalance(payout);
        state.cashedOut = true;

        updateStats({ wins: 1, topWin: payout });
        window.ManiacGames.updateBalance();
        window.ManiacGames.playSound('win');
        window.ManiacGames.hapticFeedback('success');
        updateUI();
    }
}

function bindEvents() {
    elements.betButton.addEventListener('click', () => {
        if(state.gameState === 'betting') handleBet();
        else if (state.gameState === 'running') handleCashout();
    });

    elements.betInput.addEventListener('change', e => {
        const val = parseInt(e.target.value, 10);
        state.betAmount = Math.max(1, isNaN(val) ? 1 : val);
        updateUI();
    });

    elements.chipControls.addEventListener('click', e => {
        if (e.target.classList.contains('chip')) {
            const action = e.target.dataset.action;
            const value = parseInt(e.target.dataset.value, 10);
            let currentBet = state.betAmount;

            if (action === 'add') currentBet += value;
            else if (action === 'set') currentBet = value;
            else if (action === 'div2') currentBet = Math.max(1, Math.floor(currentBet / 2));
            else if (action === 'mul2') currentBet *= 2;

            state.betAmount = Math.min(currentBet, getBalance());
            updateUI();
            window.ManiacGames.playSound('click');
        }
    });
}

export function mount(rootEl) {
    root = rootEl;
    root.innerHTML = `
        <div class="card">
            <div class="display-area">
                <canvas id="crash-canvas"></canvas>
                <div id="crash-multiplier" class="multiplier-text">1.00x</div>
            </div>
        </div>
        <div class="card">
            <h2>История</h2>
            <div id="crash-history" class="history"></div>
        </div>
        <div class="card">
            <h2>Ставка</h2>
            <input type="number" id="crash-bet-input" class="input-field" value="10">
            <div id="crash-chip-controls" class="chip-controls">
                <button class="btn chip" data-action="add" data-value="10">+10</button>
                <button class="btn chip" data-action="add" data-value="50">+50</button>
                <button class="btn chip" data-action="add" data-value="100">+100</button>
                <button class="btn chip" data-action="add" data-value="500">+500</button>
                <button class="btn chip" data-action="div2">÷2</button>
                <button class="btn chip" data-action="mul2">×2</button>
                <button class="btn chip" data-action="set" data-value="1000">1k</button>
                 <button class="btn chip" data-action="set" data-value="${getBalance()}">ALL</button>
            </div>
            <button id="crash-bet-button" class="btn"></button>
        </div>
    `;

    elements = {
        canvas: root.querySelector('#crash-canvas'),
        multiplierText: root.querySelector('#crash-multiplier'),
        history: root.querySelector('#crash-history'),
        betInput: root.querySelector('#crash-bet-input'),
        chipControls: root.querySelector('#crash-chip-controls'),
        betButton: root.querySelector('#crash-bet-button'),
    };

    // Resize canvas
    const rect = elements.canvas.parentElement.getBoundingClientRect();
    elements.canvas.width = rect.width;
    elements.canvas.height = rect.height;

    bindEvents();
    startNewRound();
}

export function unmount() {
    if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
    }
    // Set a flag to stop any pending timeouts
    if(state) state.gameState = 'unmounted';
    root = null;
    elements = null;
}

/**
 * Simulates N rounds to calculate the real Return To Player (RTP).
 * This is a developer utility.
 * @param {number} rounds - The number of rounds to simulate.
 * @returns {string} The calculated RTP as a percentage string.
 */
export function simulateRTP(rounds = 10000) {
    let totalMultiplier = 0;
    for (let i = 0; i < rounds; i++) {
        totalMultiplier += generateCrashPoint();
    }
    const averageMultiplier = totalMultiplier / rounds;
    // Theoretical RTP is complex, but this gives a good idea of the average outcome
    // A true RTP simulation would involve player cashing out strategies.
    // This value represents the average "house take" if everyone played to the end.
    const houseHold = (1 - (1 / averageMultiplier)) * 100;
    return (100 - houseHold).toFixed(2);
}
