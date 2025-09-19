import { t } from '../../../core/i18n.js';
import { games } from '../../../games/index.js';

let currentGame = null;

const template = `
    <div class="screen">
        <div class="games-selection">
            ${Object.keys(games).map(gameId => `<button class="game-selector" data-game="${gameId}">${t(gameId)}</button>`).join('')}
        </div>
        <div id="game-container"></div>
    </div>
`;

const loadGame = (gameId) => {
    const gameContainer = document.getElementById('game-container');
    if (!gameContainer) return;

    // Cleanup the previous game if it exists
    if (currentGame && games[currentGame] && games[currentGame].cleanup) {
        games[currentGame].cleanup();
    }

    // Load the new game
    currentGame = gameId;
    if (games[currentGame] && games[currentGame].init) {
        games[currentGame].init(gameContainer);
    }
};

const init = (container) => {
    container.innerHTML = template;
    const gameSelectors = document.querySelectorAll('.game-selector');
    gameSelectors.forEach(button => {
        button.addEventListener('click', (e) => {
            const gameId = e.target.dataset.game;
            loadGame(gameId);
        });
    });

    // Load the first game by default
    const firstGameId = Object.keys(games)[0];
    if (firstGameId) {
        loadGame(firstGameId);
    }
};

const cleanup = () => {
    if (currentGame && games[currentGame] && games[currentGame].cleanup) {
        games[currentGame].cleanup();
    }
    currentGame = null;
};

export const GamesScreen = {
    id: 'games',
    template,
    init,
    cleanup
};
