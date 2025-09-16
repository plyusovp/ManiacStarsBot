import { getBalance, subBalance, addBalance, updateStats } from '../core/state.js';
import { applyPayout } from '../core/houseedge.js';

export const titleKey = 'coin_game_title';

let rootElement = null;
let state = {
    betAmount: 10,
    isFlipping: false,
};

function render() {
    if (!rootElement) return;
    const t = window.ManiacGames.t;

    rootElement.innerHTML = `
        <div class="game-container">
            <div class="card">
                <div id="coin-display" style="font-size: 5em; margin: 20px 0; perspective: 1000px;">
                     <div id="coin-inner" style="position: relative; width: 1em; height: 1em; transform-style: preserve-3d; transition: transform 1s cubic-bezier(0.5, 0, 0.5, 1);">
                        <div style="position: absolute; width: 100%; height: 100%; backface-visibility: hidden;">🪙</div>
                        <div style="position: absolute; width: 100%; height: 100%; backface-visibility: hidden; transform: rotateY(180deg);">✨</div>
                     </div>
                </div>
            </div>
            <div class="card">
                <input type="number" id="coin-bet-input" class="input-field" value="${state.betAmount}" min="1">
                <div class="bet-controls" style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 15px;">
                    <button class="btn" data-choice="heads">Орёл 🪙</button>
                    <button class="btn" data-choice="tails">Решка ✨</button>
                </div>
                <div id="coin-result" style="text-align: center; margin-top: 15px; font-weight: bold; min-height: 20px;">
                   ${t('dice_make_bet')}
                </div>
            </div>
        </div>
    `;
    addEventListeners();
}

async function play(choice) {
    if (state.isFlipping) return;
    const t = window.ManiacGames.t;

    if (getBalance() < state.betAmount) {
        window.ManiacGames.showNotification(t('not_enough_funds'), 'error');
        return;
    }

    state.isFlipping = true;
    subBalance(state.betAmount);
    window.ManiacGames.updateBalance();

    const resultEl = rootElement.querySelector('#coin-result');
    const coinInner = rootElement.querySelector('#coin-inner');
    const betControls = rootElement.querySelector('.bet-controls');

    resultEl.textContent = '';
    betControls.style.pointerEvents = 'none'; // Блокируем кнопки

    window.ManiacGames.playSound('spinStart');
    window.ManiacGames.hapticFeedback('medium');

    // Анимация
    const randomSpins = 360 * (4 + Math.floor(Math.random() * 2)); // 4 или 5 полных оборотов
    const result = Math.random() < 0.5 ? 'heads' : 'tails';
    const finalRotation = result === 'tails' ? 180 : 0;
    coinInner.style.transform = `rotateY(${randomSpins + finalRotation}deg)`;

    await new Promise(resolve => setTimeout(resolve, 1100)); // Ждем завершения анимации

    const isWin = choice === result;

    if (isWin) {
        const winAmount = applyPayout(state.betAmount * 2);
        addBalance(winAmount);
        updateStats({ wins: 1, topWin: winAmount });
        resultEl.style.color = 'var(--success)';
        resultEl.textContent = `${t('win_message')} +${winAmount} ⭐`;
        window.ManiacGames.playSound('win');
        window.ManiacGames.hapticFeedback('success');
    } else {
        updateStats({ losses: 1 });
        resultEl.style.color = 'var(--danger)';
        resultEl.textContent = `${t('loss_message')} -${state.betAmount} ⭐`;
        window.ManiacGames.playSound('lose');
        window.ManiacGames.hapticFeedback('error');
    }

    window.ManiacGames.updateBalance();
    state.isFlipping = false;
    betControls.style.pointerEvents = 'auto'; // Разблокируем кнопки
}

function addEventListeners() {
    rootElement.querySelector('#coin-bet-input').addEventListener('change', (e) => {
        const value = parseInt(e.target.value, 10);
        state.betAmount = isNaN(value) || value < 1 ? 1 : value;
    });

    rootElement.querySelector('.bet-controls').addEventListener('click', (e) => {
        const button = e.target.closest('button');
        if (button && button.dataset.choice) {
            play(button.dataset.choice);
        }
    });
}

export function mount(rootEl) {
    rootElement = rootEl;
    render();
}

export function unmount() {
    rootElement = null;
    state = { betAmount: 10, isFlipping: false };
}
