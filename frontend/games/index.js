import { diceGame } from './dice.js';
import { slotsGame } from './slots.js';
import { crashGame } from './crash.js';
import { coinGame } from './coin.js';

export const games = {
    dice: diceGame,
    slots: slotsGame,
    crash: crashGame,
    coin: coinGame,
};
