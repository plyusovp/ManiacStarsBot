import { getBalance, subBalance, addBalance, updateStats } from '../core/state.js';
import { applyPayout } from '../core/houseedge.js';

export const title = 'Орёл/Решка';

let rootElement = null;
let betAmount = 10;
let isFlipping = false;

function render() {
    rootElement.innerHTML = `
        <div class="game-container">
            <div class="card">
                <div id="coin-display" style="font-size: 5em; margin: 20px 0; perspective: 1000px;">
                     <div id="coin-inner" style="position: relative; width: 1em; height: 1em; transform-style: preserve-3d;">
                        <div style="position: absolute; width: 100%; height: 100%; backface-visibility: hidden;">🪙</div>
                        <div style="position: absolute; width: 100%; height: 100%; backface-visibility: hidden; transform: rotateY(180deg);">✨</div>
                     </div>
                </div>
            </div>
            <div class="card">
                <input type="number" id="coin-bet-input" class="input-field" value="${betAmount}" min="1">
                <div class="bet-controls">
                    <button class="btn" data-choice="heads">Орёл 🪙</button>
                    <button class="btn" data-choice="tails">Решка ✨</button>
                </div>
                <div id="coin-result" style="margin-top: 15px; font-weight: bold; min-height: 20px;"></div>
            </div>
        </div>
    `;

    rootElement.querySelector('#coin-bet-input').addEventListener('change', (e) => {
        betAmount = parseInt(e.target.value, 10);
    });

    rootElement.querySelector('.bet-controls').addEventListener('click', (e) => {
        if (e.target.dataset.choice) {
            play(e.target.dataset.choice);
        }
    });
}

async function play(choice) {
    if (isFlipping) return;

    if (getBalance() < betAmount) {
        window.ManiacGames.showNotification('Недостаточно средств', 'error');
        return;
    }

    subBalance(betAmount);

    isFlipping = true;
    window.ManiacGames.updateBalance();
    const resultEl = rootElement.querySelector('#coin-result');
    const coinInner = rootElement.querySelector('#coin-inner');
    resultEl.textContent = '';

    window.ManiacGames.playSound('spinStart');
    window.ManiacGames.hapticFeedback('medium');

    // Анимация
    coinInner.style.transition = 'transform 1s';
    const randomSpins = 1800 + (Math.random() > 0.5 ? 180 : 0);
    coinInner.style.transform = `rotateY(${randomSpins}deg)`;

    await new Promise(resolve => setTimeout(resolve, 1100));

    const result = Math.random() < 0.5 ? 'heads' : 'tails';
    const isWin = choice === result;

    // Фиксируем результат после анимации
    coinInner.style.transition = 'none';
    coinInner.style.transform = `rotateY(${result === 'tails' ? 180 : 0}deg)`;


    if (isWin) {
        const winAmount = applyPayout(betAmount * 2);
        addBalance(winAmount);
        updateStats({ wins: 1, topWin: winAmount });
        resultEl.style.color = 'var(--success)';
        resultEl.textContent = `Победа! Выигрыш ${winAmount} ⭐`;
        window.ManiacGames.playSound('win');
        window.ManiacGames.hapticFeedback('success');
    } else {
        updateStats({ losses: 1 });
        resultEl.style.color = 'var(--danger)';
        resultEl.textContent = `Проигрыш! Ставка ${betAmount} ⭐ сгорела.`;
        window.ManiacGames.playSound('lose');
        window.ManiacGames.hapticFeedback('error');
    }

    window.ManiacGames.updateBalance();
    isFlipping = false;
}


export function mount(rootEl) {
    rootElement = rootEl;
    render();
}

export function unmount() {
    rootElement = null;
}
