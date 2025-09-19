import { t } from '../core/i18n.js';
import { playWin, playLose } from '../core/audio.js';

const symbols = ['🍒', '🍋', '🍊', '🍉', '⭐', '🔔', '🍀'];
let currentBet = 10;

const template = `
    <div class="game-container">
        <h2>${t('slots_game_title')}</h2>
        <div class="slots-reels">
            <div class="reel" id="reel1"></div>
            <div class="reel" id="reel2"></div>
            <div class="reel" id="reel3"></div>
        </div>
        <div class="slots-controls">
            <div class="control-group">
                <label for="slots-bet-amount">${t('bet_amount')}:</label>
                <input type="number" id="slots-bet-amount" value="${currentBet}" min="1">
            </div>
            <button id="spin-button">${t('spin')}</button>
        </div>
        <div class="slots-result">
            <p id="slots-outcome"></p>
        </div>
    </div>
`;

const spinReels = () => {
    const reels = [document.getElementById('reel1'), document.getElementById('reel2'), document.getElementById('reel3')];
    const results = [];

    reels.forEach((reel, index) => {
        const symbol = symbols[Math.floor(Math.random() * symbols.length)];
        results.push(symbol);
        reel.textContent = symbol;
    });

    return results;
};


const handleSpin = () => {
    const betAmountInput = document.getElementById('slots-bet-amount');
    currentBet = parseInt(betAmountInput.value, 10);

    const outcomeElement = document.getElementById('slots-outcome');
    if (!outcomeElement) return;

    const results = spinReels();

    // Simple win condition: three of the same symbol
    if (results[0] === results[1] && results[1] === results[2]) {
        outcomeElement.textContent = `${t('win')}! You got three ${results[0]}s.`;
        outcomeElement.style.color = 'green';
        playWin();
        // bus.emit('game:win', { game: 'slots', bet: currentBet, payout: calculatedPayout });
    } else {
        outcomeElement.textContent = `${t('try_again')}`;
        outcomeElement.style.color = 'inherit';
        playLose();
        // bus.emit('game:lose', { game: 'slots', bet: currentBet });
    }
};

const init = (container) => {
    container.innerHTML = template;
    document.getElementById('spin-button').addEventListener('click', handleSpin);
};

const cleanup = () => {
    const spinButton = document.getElementById('spin-button');
    if (spinButton) {
        spinButton.removeEventListener('click', handleSpin);
    }
};

export const slotsGame = {
    id: 'slots',
    init,
    cleanup
};
