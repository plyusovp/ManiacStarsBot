import { getBalance, subBalance, addBalance, updateStats } from '../core/state.js';
import { applyPayout } from '../core/houseedge.js';

export const titleKey = 'crash_game_title';

const CRASH_ALPHA = 1.6;
const CRASH_MAX = 100.0;
const BETTING_WINDOW_MS = 7000;

let root, elements, state;
let animationFrameId, countdownInterval;

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
        lastCurvePos: { x: 0, y: 0 }
    };
}

function generateCrashPoint() {
    const u = Math.random();
    const point = Math.pow(1 / (1 - u), 1 / CRASH_ALPHA);
    return Math.max(1.0, Math.min(CRASH_MAX, point));
}

function updateUI() {
    if (!root || !elements.betInput) return;
    const t = window.ManiacGames.t;

    elements.betInput.value = state.betAmount;
    elements.multiplierText.textContent = `${state.multiplier.toFixed(2)}x`;

    elements.multiplierText.style.color = state.gameState === 'crashed' ? 'var(--danger)' :
                                         state.cashedOut ? 'var(--success)' : 'var(--text)';

    switch (state.gameState) {
        case 'betting':
            elements.betButton.disabled = state.stake > 0;
            elements.betButton.className = 'btn btn-success';
            elements.betButton.textContent = state.stake > 0 ? t('crash_accepted') : `${t('crash_place_bet')} (${state.countdown}s)`;
            break;
        case 'running':
            if (state.stake > 0 && !state.cashedOut) {
                const potentialWin = Math.floor(state.stake * state.multiplier);
                elements.betButton.disabled = false;
                elements.betButton.className = 'btn btn-warning';
                elements.betButton.textContent = `${t('crash_take')} ${potentialWin} ⭐`;
            } else {
                elements.betButton.disabled = true;
                elements.betButton.className = 'btn';
                elements.betButton.textContent = t('crash_betting_closed');
            }
            break;
        case 'crashed':
            elements.betButton.disabled = true;
            elements.betButton.className = 'btn btn-danger';
            elements.betButton.textContent = t('crash_crashed');
            break;
    }
    updateHistory();
    drawCurve();
}

function updateHistory() {
    elements.history.innerHTML = state.history.slice(0, 10).map(m => {
        let color = 'var(--danger)';
        if (m >= 2.0) color = 'var(--success)';
        else if (m >= 1.2) color = 'var(--warning)';
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
    const maxX = Math.log(Math.max(20, state.crashPoint || 20));
    const maxY = Math.max(20, state.crashPoint || 20);

    let finalX = 0, finalY = height;
    for (let t_step = 0; t_step <= duration; t_step += 0.02) {
        const m = 1.00 * Math.pow(1.05, t_step * 2);
        const x = (Math.log(m) / maxX) * width;
        const y = height - (m / maxY) * height;
        if (y > 0) {
            ctx.lineTo(x, y);
            finalX = x;
            finalY = y;
        }
    }
    ctx.stroke();
    ctx.shadowBlur = 0;

    const canvasRect = elements.canvas.getBoundingClientRect();
    state.lastCurvePos.x = canvasRect.left + finalX;
    state.lastCurvePos.y = canvasRect.top + finalY;
}

function gameLoop(timestamp) {
    if (state.gameState !== 'running') return;

    if (elements.graphSkeleton) {
        elements.graphSkeleton.style.display = 'none';
        elements.graphSkeleton = null;
    }

    const elapsedSeconds = (timestamp - state.startTime) / 1000;
    state.multiplier = 1.00 * Math.pow(1.05, elapsedSeconds * 2);

    if (window.ManiacGames.particles && Math.random() < 0.5) {
        window.ManiacGames.particles.emit(state.lastCurvePos.x, state.lastCurvePos.y, {
            count: 1, speed: 1, life: 30, size: 1.5,
            color: ['#8A7CFF', '#F92B75', '#ffffff'], angle: Math.PI * 1.5, angleOffset: Math.random() * 0.4 - 0.2
        });
    }

    if (state.multiplier >= state.crashPoint) {
        state.multiplier = state.crashPoint;
        state.gameState = 'crashed';
        if (window.ManiacGames.particles) {
            window.ManiacGames.particles.emit(state.lastCurvePos.x, state.lastCurvePos.y, {
                count: 60, speed: 5, life: 90, size: 2.5, color: ['#FF6B6B', '#FFC85C', '#ffffff'],
            });
        }
        state.history.unshift(state.multiplier);
        updateStats({ maxCrashMultiplier: state.multiplier });
        if (state.stake > 0 && !state.cashedOut) {
            updateStats({ losses: 1 });
            window.ManiacGames.playSound('lose');
            window.ManiacGames.hapticFeedback('error');
        }
        window.ManiacGames.playSound('crash');
        updateUI();
        setTimeout(startNewRound, 2000);
    } else {
        updateUI();
        animationFrameId = requestAnimationFrame(gameLoop);
    }
}

function startNewRound() {
    if (animationFrameId) cancelAnimationFrame(animationFrameId);
    resetState();
    state.crashPoint = generateCrashPoint();

    if (elements.graphSkeleton) elements.graphSkeleton.style.display = 'block';

    countdownInterval = setInterval(() => {
        if (!root) {
            clearInterval(countdownInterval);
            return;
        }
        state.countdown--;
        if (state.countdown <= 0) {
            clearInterval(countdownInterval);
            if (state.gameState === 'betting') {
                 state.gameState = 'running';
                 state.startTime = performance.now();
                 window.ManiacGames.playSound('spinStart');
                 animationFrameId = requestAnimationFrame(gameLoop);
            }
        }
        updateUI();
    }, 1000);

    updateUI();
}

function handleBet() {
    if (state.gameState !== 'betting' || state.stake !== 0) return;
    const t = window.ManiacGames.t;

    const bet = state.betAmount;
    if (bet <= 0) return;
    if (getBalance() < bet) {
        window.ManiacGames.showNotification(t('not_enough_funds'), 'error');
        return;
    }
    subBalance(bet);
    state.stake = bet;
    window.ManiacGames.updateBalance();
    window.ManiacGames.playSound('tap');
    window.ManiacGames.hapticFeedback('medium');
    updateUI();
}

function handleCashout() {
     if (state.gameState !== 'running' || state.stake <= 0 || state.cashedOut) return;
     const t = window.ManiacGames.t;

    const payout = applyPayout(state.stake * state.multiplier);
    addBalance(payout);
    state.cashedOut = true;
    updateStats({ wins: 1, topWin: payout });
    window.ManiacGames.updateBalance();
    window.ManiacGames.playSound('win');
    window.ManiacGames.hapticFeedback('success');
    updateUI();
}

function bindEvents() {
    elements.betButton.addEventListener('click', () => {
        if (state.gameState === 'betting') handleBet();
        else if (state.gameState === 'running') handleCashout();
    });
    elements.betInput.addEventListener('change', e => {
        const val = parseInt(e.target.value, 10);
        state.betAmount = Math.max(1, isNaN(val) ? 1 : val);
        updateUI();
    });
    elements.chipControls.addEventListener('click', e => {
        const chip = e.target.closest('.chip');
        if (!chip) return;

        const action = chip.dataset.action;
        const value = parseInt(chip.dataset.value, 10);
        let currentBet = state.betAmount;

        if (action === 'add') currentBet += value;
        else if (action === 'set') currentBet = value;
        else if (action === 'div2') currentBet = Math.max(1, Math.floor(currentBet / 2));
        else if (action === 'mul2') currentBet *= 2;

        state.betAmount = Math.min(currentBet, getBalance());
        updateUI();
        window.ManiacGames.playSound('tap');
    });
}

export function mount(rootEl) {
    root = rootEl;
    const t = window.ManiacGames.t;

    root.innerHTML = `
        <style>
        .display-area { position: relative; width: 100%; aspect-ratio: 16/9; background: var(--bg-soft); border-radius: var(--radius-lg); overflow: hidden;}
        #crash-canvas { width: 100%; height: 100%; }
        .multiplier-text { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 2.5rem; font-weight: 700; color: var(--text); }
        .history { display: flex; gap: 8px; overflow-x: auto; padding-bottom: 5px; }
        .history-item { padding: 4px 10px; border-radius: var(--radius-pill); font-weight: 600; font-size: 0.8rem; flex-shrink: 0; }
        </style>
        <div class="card">
            <div class="display-area">
                <div id="crash-graph-skeleton" class="skeleton-pulse" style="width: 100%; height: 100%; position: absolute; top: 0; left: 0;"></div>
                <canvas id="crash-canvas"></canvas>
                <div id="crash-multiplier" class="multiplier-text">1.00x</div>
            </div>
        </div>
        <div class="card">
            <h2>${t('crash_history')}</h2>
            <div id="crash-history" class="history"></div>
        </div>
        <div class="card">
            <h2>${t('crash_bet')}</h2>
            <input type="number" id="crash-bet-input" class="input-field" value="10">
            <div id="crash-chip-controls" class="chip-controls" style="grid-template-columns: repeat(4, 1fr);">
                <button class="btn chip" data-action="add" data-value="100">+100</button>
                <button class="btn chip" data-action="div2">/2</button>
                <button class="btn chip" data-action="mul2">*2</button>
                <button class="btn chip" data-action="set" data-value="${getBalance()}">ALL</button>
            </div>
            <button id="crash-bet-button" class="btn"></button>
        </div>
    `;

    elements = {
        canvas: root.querySelector('#crash-canvas'),
        graphSkeleton: root.querySelector('#crash-graph-skeleton'),
        multiplierText: root.querySelector('#crash-multiplier'),
        history: root.querySelector('#crash-history'),
        betInput: root.querySelector('#crash-bet-input'),
        chipControls: root.querySelector('#crash-chip-controls'),
        betButton: root.querySelector('#crash-bet-button'),
    };

    const rect = elements.canvas.parentElement.getBoundingClientRect();
    elements.canvas.width = rect.width;
    elements.canvas.height = rect.height;

    bindEvents();
    startNewRound();
}

export function unmount() {
    if (animationFrameId) cancelAnimationFrame(animationFrameId);
    if (countdownInterval) clearInterval(countdownInterval);
    root = null;
    elements = null;
    state = null;
}
