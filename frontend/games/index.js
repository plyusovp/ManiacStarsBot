// Импортируем инициализаторы всех игр
import { initCoinGame } from './coin.js';
import { initCrashGame } from './crash.js';
import { initDiceGame } from './dice.js';
import { initSlotsGame } from './slots.js';

// Главная функция, которая запускает все игры
export function initializeGames() {
    console.log('Initializing all games...');
    initCoinGame();
    initCrashGame();
    initDiceGame();
    initSlotsGame();
    // Тут можно добавить общую логику для всех игр, если она понадобится
}
