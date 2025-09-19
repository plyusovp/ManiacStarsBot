import { t } from '../core/i18n.js';
import { playWin, playLose } from '../core/audio.js';

let currentBet = 10;
let multiplier = 1.0;
let gameState = 'waiting'; // waiting, running, crashed
let gameLoopInterval;

const template = `
    <div class="game-container">
        <h2>${t('crash_game_title')}</h2>
        <div class="crash-graph">
            <p id="multiplier-display">x1.00</p>
        </div>
        <div class="crash-controls">
            <div class="control-group">
                <label for="crash-bet-amount">${t('bet_amount')}:</label>
                <input type="number" id="crash-bet-amount" value="${currentBet}" min="1">
            </div>
            <button id="crash-button">${t('place_bet')}</button>
        </div>
        <div class="crash-result">
            <p id="crash-outcome"></p>
        </div>
    </div>
`;

const resetGame = () => {
    multiplier = 1.0;
    gameState = 'waiting';
    document.getElementById('multiplier-display').textContent = `x${multiplier.toFixed(2)}`;
    document.getElementById('multiplier-display').style.color = 'white';
    document.getElementById('crash-button').textContent = t('place_bet');
    document.getElementById('crash-button').disabled = false;
    document.getElementById('crash-outcome').textContent = '';
};

const startGameLoop = () => {
    gameState = 'running';
    document.getElementById('crash-button').textContent = t('cash_out');

    // Determine crash point
    const crashPoint = 1 + Math.random() * 99; // Crash somewhere between 1.00 and 100.00

    gameLoopInterval = setInterval(() => {
        multiplier += 0.01;
        document.getElementById('multiplier-display').textContent = `x${multiplier.toFixed(2)}`;

        if (multiplier >= crashPoint) {
            clearInterval(gameLoopInterval);
            gameState = 'crashed';
            document.getElementById('multiplier-display').style.color = 'red';
            document.getElementById('crash-button').textContent = t('crashed');
            document.getElementById('crash-button').disabled = true;
            document.getElementById('crash-outcome').textContent = `${t('crashed_at')} x${multiplier.toFixed(2)}`;
            playLose();
            setTimeout(resetGame, 3000);
        }
    }, 50); // Speed of the multiplier increase
};

const handleCrashButton = () => {
    if (gameState === 'waiting') {
        const betAmountInput = document.getElementById('crash-bet-amount');
        currentBet = parseInt(betAmount-input.value, 10);
        startGameLoop();
    } else if (gameState === 'running') {
        clearInterval(gameLoopInterval);
        gameState = 'cashed_out';
        const winAmount = (currentBet * multiplier).toFixed(2);
        document.getElementById('crash-outcome').textContent = `${t('cashed_out_at')} x${multiplier.toFixed(2)}! ${t('you_won')} ${winAmount}`;
        document.getElementById('crash-button').disabled = true;
        playWin();
        // bus.emit('game:win', { game: 'crash', bet: currentBet, payout: winAmount });
        setTimeout(resetGame, 3000);
    }
};

const init = (container) => {
    container.innerHTML = template;
    document.getElementById('crash-button').addEventListener('click', handleCrashButton);
};

const cleanup = () => {
    clearInterval(gameLoopInterval);
    const crashButton = document.getElementById('crash-button');
    if (crashButton) {
        crashButton.removeEventListener('click', handleCrashButton);
    }
};

export const crashGame = {
    id: 'crash',
    init,
    cleanup
};
