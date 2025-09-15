import * as api from '../api.js';

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
                <input type="number" id="coin-bet-input" value="${betAmount}" min="1">
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
    if (!api.subBalance(betAmount)) {
        alert('Недостаточно средств!');
        return;
    }

    isFlipping = true;
    window.ManiacStars.updateBalance();
    const resultEl = rootElement.querySelector('#coin-result');
    const coinInner = rootElement.querySelector('#coin-inner');
    resultEl.textContent = '';

    // Анимация
    coinInner.style.transition = 'transform 1s';
    coinInner.style.transform = `rotateY(${1800 + (Math.random() > 0.5 ? 180 : 0)}deg)`;

    await new Promise(resolve => setTimeout(resolve, 1100));

    const result = Math.random() < 0.5 ? 'heads' : 'tails';
    const isWin = choice === result;

    // Фиксируем результат после анимации
    coinInner.style.transition = 'none';
    coinInner.style.transform = `rotateY(${result === 'tails' ? 180 : 0}deg)`;


    if (isWin) {
        const winAmount = betAmount * 2;
        api.addBalance(winAmount);
        window.ManiacStars.updateBalance();
        resultEl.style.color = 'var(--success-color)';
        resultEl.textContent = `Победа! Выигрыш ${winAmount} ⭐`;
    } else {
        resultEl.style.color = 'var(--danger-color)';
        resultEl.textContent = `Проигрыш! Ставка ${betAmount} ⭐ сгорела.`;
    }

    isFlipping = false;
}


export function mount(rootEl) {
    rootElement = rootEl;
    render();
}

export function unmount() {
    rootElement = null;
}
