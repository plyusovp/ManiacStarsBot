import { getBalance, subBalance, addBalance, updateStats } from '../core/state.js';
import { applyPayout } from '../core/houseedge.js';

export const titleKey = 'coin_game_title'; // Используем ключ из i18n

// --- Параметры игры ---
const PAYOUT_MULTIPLIER = 1.95; // Выплата чуть меньше 2x для преимущества казино

// --- Состояние ---
let root, elements, state;

/**
 * Сбрасывает состояние игры к начальным значениям
 */
function resetState() {
    state = {
        isFlipping: false,
        betAmount: 10,
        history: [], // Хранит 'heads' или 'tails'
    };
}

/**
 * Возвращает SVG-иконку для стороны монеты
 * @param {'heads' | 'tails'} side - Сторона монеты
 * @returns {string} HTML-строка с SVG
 */
function getCoinSVG(side) {
    if (side === 'heads') {
        // Простой силуэт орла для "Орла"
        return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="80%" height="80%"><path d="M18.89,14.24a1,1,0,0,0-.54-.54L17.5,13.25V9.5a1,1,0,0,0-2,0V8.81a5.4,5.4,0,0,0-7.06,0V9.5a1,1,0,0,0-2,0v3.75l-.85.45a1,1,0,0,0-.54.54,1,1,0,0,0,.1.95l1.45,2.18A9.33,9.33,0,0,0,12,22a9.33,9.33,0,0,0,5.89-4.63l1.45-2.18A1,1,0,0,0,18.89,14.24ZM12,20a7.33,7.33,0,0,1-4.57-3.63l-.43-.65-.12.18a1,1,0,0,0,0,.11v.11a1,1,0,0,0,.12.12l.13.12H7.29a1,1,0,0,0,.11-.12l.12-.12a1,1,0,0,0,.11,0h.11a1,1,0,0,0-.11-.11l-.12-.13V16a1,1,0,0,0,0-.11l.12-.12.12.12a1,1,0,0,0,.11.12h0a1,1,0,0,0,.12-.12l.12-.12h.11a1,1,0,0,0-.12.12l-.12.12a1,1,0,0,0,0,.11v.11a1,1,0,0,0,.12.12l.12.13a1,1,0,0,0,.11,0h.11a1,1,0,0,0-.11-.11l-.12-.13V16a1,1,0,0,0,0-.11l.12-.12.12.12a1,1,0,0,0,.11.12h0a1,1,0,0,0,.12-.12l.12-.12h.11a1,1,0,0,0-.12.12l-.12.12a1,1,0,0,0,0,.11v.11a1,1,0,0,0,1.37.9,7.55,7.55,0,0,1,2.5,0,1,1,0,0,0,1.37-.9V16.2a1,1,0,0,0,0-.11l-.12-.12a1,1,0,0,0-.12-.12h.11a1,1,0,0,0,.12.12l.12.12a1,1,0,0,0,.12,0h0a1,1,0,0,0,.11-.12l.12-.12.12.12a1,1,0,0,0,0,.11v.12a1,1,0,0,0,.11.12l.13.12a1,1,0,0,0-.11,0h.11a1,1,0,0,0,.12-.11l.12-.12V16a1,1,0,0,0,0-.11l-.12-.13a1,1,0,0,0-.12-.12h.11a1,1,0,0,0,.12.12l.12.12a1,1,0,0,0,.12,0h0a1,1,0,0,0,.11-.12l.12-.12.12.12a1,1,0,0,0,0,.11v.12a1,1,0,0,0,.11.12l.13.12a1,1,0,0,0-.11,0h.11a1,1,0,0,0,.12-.11l.12-.12V16a1,1,0,0,0-.12-.12l-.12.12h.11a1,1,0,0,0,.12-.12l-.43.65A7.33,7.33,0,0,1,12,20Z M12,3.5A3.5,3.5,0,0,0,8.5,7a1,1,0,0,0,2,0A1.5,1.5,0,0,1,12,5.5a1.5,1.5,0,0,1,1.5,1.5,1,1,0,0,0,2,0A3.5,3.5,0,0,0,12,3.5Z"/></svg>`;
    } else { // tails
        // Простой узор для "Решки"
        return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="80%" height="80%"><path d="M12,2A10,10,0,1,0,22,12,10,10,0,0,0,12,2Zm0,18a8,8,0,1,1,8-8A8,8,0,0,1,12,20Z" opacity=".3"/><path d="M12,4a8,8,0,0,0-8,8,1,1,0,0,0,2,0,6,6,0,0,1,6-6,1,1,0,0,0,0-2Z"/></svg>`;
    }
}

/**
 * Отрисовывает историю последних 5 бросков
 */
function renderHistory() {
    if (!elements || !elements.history) return;
    elements.history.innerHTML = state.history.map(side => `
        <div class="coin-history-item is-${side}">
            ${side === 'heads' ? 'О' : 'Р'}
        </div>
    `).join('');
}

/**
 * Обновляет сумму ставки
 * @param {number | string} value - Новое значение или модификатор
 * @param {boolean} isAbsolute - Установить абсолютное значение?
 */
function updateBet(value, isAbsolute = false) {
    const balance = getBalance();
    let newBet;

    if (isAbsolute) {
        newBet = value;
    } else if (typeof value === 'string' && value.includes('x')) {
        const multiplier = parseFloat(value.replace('x', ''));
        newBet = Math.floor(state.betAmount * multiplier);
    } else {
        newBet = state.betAmount + value;
    }

    state.betAmount = Math.max(1, Math.min(newBet, balance));
    elements.betInput.value = state.betAmount;
    window.ManiacGames.playSound('tap');
}

/**
 * Основная логика игры
 * @param {'heads' | 'tails'} choice - Выбор игрока
 */
async function play(choice) {
    if (state.isFlipping) return;

    if (getBalance() < state.betAmount) {
        window.ManiacGames.showNotification(window.ManiacGames.t('not_enough_funds'), 'error');
        return;
    }

    state.isFlipping = true;
    subBalance(state.betAmount);
    window.ManiacGames.updateBalance();
    
    elements.resultText.textContent = '';
    elements.choiceControls.querySelectorAll('button').forEach(b => b.disabled = true);
    
    window.ManiacGames.playSound('spinStart');
    window.ManiacGames.hapticFeedback('medium');

    const result = Math.random() < 0.5 ? 'heads' : 'tails';

    // Анимация
    elements.coin.classList.add('flipping');
    // Случайное доп. вращение для разнообразия
    const extraSpins = Math.floor(Math.random() * 2);
    const finalRotation = 1800 + (extraSpins * 360) + (result === 'tails' ? 180 : 0);
    elements.coinInner.style.transform = `rotateY(${finalRotation}deg)`;

    await new Promise(resolve => setTimeout(resolve, 2000)); // Длительность анимации

    const isWin = choice === result;
    
    if (isWin) {
        const winAmount = applyPayout(state.betAmount * PAYOUT_MULTIPLIER);
        addBalance(winAmount);
        updateStats({ wins: 1, topWin: winAmount });
        elements.resultText.textContent = `${window.ManiacGames.t('win_message')} +${winAmount} ⭐`;
        elements.resultText.classList.add('win');
        elements.resultText.classList.remove('lose');
        window.ManiacGames.playSound('win');
        window.ManiacGames.hapticFeedback('success');
    } else {
        updateStats({ losses: 1 });
        elements.resultText.textContent = `${window.ManiacGames.t('loss_message')}`;
        elements.resultText.classList.add('lose');
        elements.resultText.classList.remove('win');
        window.ManiacGames.playSound('lose');
        window.ManiacGames.hapticFeedback('error');
    }

    state.history.unshift(result);
    if (state.history.length > 5) state.history.pop();
    renderHistory();
    
    window.ManiacGames.updateBalance();
    elements.coin.classList.remove('flipping');
    elements.choiceControls.querySelectorAll('button').forEach(b => b.disabled = false);
    state.isFlipping = false;
}

/**
 * Привязывает обработчики событий к элементам UI
 */
function bindEvents() {
    elements.betInput.addEventListener('change', e => {
        const value = parseInt(e.target.value, 10) || 1;
        state.betAmount = Math.max(1, Math.min(value, getBalance()));
        e.target.value = state.betAmount;
    });

    elements.chipControls.addEventListener('click', e => {
        const button = e.target.closest('button');
        if (!button) return;
        const action = button.dataset.action;
        const value = button.dataset.value;

        switch(action) {
            case 'set':
                updateBet(parseInt(value), true);
                break;
            case 'add':
                updateBet(parseInt(value), false);
                break;
            case 'multiply':
                updateBet(value, false);
                break;
            case 'max':
                updateBet(getBalance(), true);
                break;
        }
    });

    elements.choiceControls.addEventListener('click', e => {
        const button = e.target.closest('button');
        if (button && button.dataset.choice) {
            play(button.dataset.choice);
        }
    });
}

/**
 * Монтирует компонент игры в DOM
 * @param {HTMLElement} rootEl - Корневой элемент для монтирования
 */
export function mount(rootEl) {
    root = rootEl;
    resetState();
    
    const t = window.ManiacGames.t;

    root.innerHTML = `
        <div class="coin-game-wrapper">
            <div id="coin-history-container" class="coin-history"></div>
            <div class="card coin-scene-card">
                <div class="coin-scene">
                    <div id="coin-flipper" class="coin">
                        <div id="coin-inner" class="coin-inner">
                            <div class="coin-face coin-front">${getCoinSVG('heads')}</div>
                            <div class="coin-face coin-back">${getCoinSVG('tails')}</div>
                        </div>
                    </div>
                </div>
                 <div id="coin-result-text" class="game-result-text"></div>
            </div>

            <div class="card">
                <label class="input-label">${t('coin_bet_size')}</label>
                <div class="bet-input-container">
                    <span class="bet-input-icon">⭐</span>
                    <input type="number" id="coin-bet-input" class="input-field" value="${state.betAmount}">
                </div>
                <div id="coin-chip-controls" class="chip-controls">
                    <button class="btn chip" data-action="add" data-value="1">+1</button>
                    <button class="btn chip" data-action="add" data-value="5">+5</button>
                    <button class="btn chip" data-action="add" data-value="10">+10</button>
                    <button class="btn chip" data-action="multiply" data-value="x2">x2</button>
                    <button class="btn chip" data-action="max" data-value="max">Max</button>
                </div>
            </div>
            
            <div id="coin-choice-controls" class="coin-choice-controls">
                <button class="btn btn-primary" data-choice="heads">${t('coin_heads')}</button>
                <button class="btn btn-secondary" data-choice="tails">${t('coin_tails')}</button>
            </div>
        </div>
    `;

    elements = {
        history: root.querySelector('#coin-history-container'),
        coin: root.querySelector('#coin-flipper'),
        coinInner: root.querySelector('#coin-inner'),
        resultText: root.querySelector('#coin-result-text'),
        betInput: root.querySelector('#coin-bet-input'),
        chipControls: root.querySelector('#coin-chip-controls'),
        choiceControls: root.querySelector('#coin-choice-controls')
    };

    renderHistory();
    bindEvents();
}

/**
 * Демонтирует компонент, очищая ресурсы
 */
export function unmount() {
    root = null;
    elements = null;
    state = null;
}
