// --- Централизованный модуль управления звуком (SFX) ---
// Использует Tone.js для генерации звуков на лету

const MUTE_KEY = 'mg.soundMuted';
let audioContextStarted = false;
let isMuted = localStorage.getItem(MUTE_KEY) === 'true';

// --- Звуковые эффекты ---
const sfx = {
    // Короткий, сухой щелчок
    tap: new Tone.MembraneSynth({
        pitchDecay: 0.01,
        octaves: 6,
        envelope: { attack: 0.001, decay: 0.1, sustain: 0 },
    }).toDestination(),

    // Короткая мажорная мелодия
    win: new Tone.PolySynth(Tone.Synth, {
        envelope: { attack: 0.01, decay: 0.2, sustain: 0.1, release: 0.1 },
        volume: -12,
    }).toDestination(),

    // Глухой, низкий удар
    lose: new Tone.MembraneSynth({
        pitchDecay: 0.1,
        octaves: 2,
        envelope: { attack: 0.01, decay: 0.2, sustain: 0 },
        volume: -10,
    }).toDestination(),

    // Начало вращения
    spinStart: new Tone.NoiseSynth({
        noise: { type: 'white' },
        envelope: { attack: 0.01, decay: 0.2, sustain: 0 },
        volume: -20,
    }).toDestination(),

    // Падение в Crash
    crash: new Tone.Synth({
        oscillator: { type: 'sawtooth' },
        envelope: { attack: 0.01, decay: 0.2, sustain: 0, release: 0.1 },
        volume: -8,
    }).toDestination(),
};

// --- Основные функции ---

/**
 * Инициализирует AudioContext по первому действию пользователя.
 */
async function initAudioContext() {
    if (audioContextStarted || Tone.context.state === 'running') {
        audioContextStarted = true;
        return;
    }
    await Tone.start();
    console.log('AudioContext started.');
    audioContextStarted = true;
}

/**
 * Воспроизводит звуковой эффект.
 * @param {string} id - Название звука ('tap', 'win', 'lose', 'spinStart', 'spinStop', 'crash').
 * @param {object} [options] - Дополнительные параметры.
 * @param {number} [options.volume] - Громкость (переопределяет стандартную).
 * @param {number} [options.rate] - Скорость воспроизведения.
 */
export function play(id, options = {}) {
    if (isMuted) return;
    initAudioContext();

    const now = Tone.now();

    switch (id) {
        case 'tap':
        case 'spinStop': // Используем один и тот же звук для клика
            sfx.tap.triggerAttackRelease('C4', '32n', now);
            break;

        case 'win':
            sfx.win.triggerAttackRelease(['C4', 'E4', 'G4'], '16n', now, 0.35);
            break;

        case 'lose':
            sfx.lose.triggerAttackRelease('C2', '8n', now, 0.2);
            break;

        case 'spinStart':
             sfx.spinStart.triggerAttackRelease('0.2', now);
             break;

        case 'crash':
            sfx.crash.triggerAttackRelease('C4', '8n', now);
            sfx.crash.frequency.rampTo('C3', 0.25, now);
            break;

        default:
            console.warn(`Sound with id "${id}" not found.`);
            break;
    }
}

/**
 * Включает или выключает все звуки.
 * @param {boolean} muted - true, чтобы выключить звук, false - чтобы включить.
 */
export function setMuted(muted) {
    isMuted = muted;
    localStorage.setItem(MUTE_KEY, isMuted.toString());
    if (!isMuted) {
       initAudioContext();
       play('tap'); // Проигрываем звук при включении для обратной связи
    }
}

/**
 * Возвращает текущее состояние звука.
 * @returns {boolean} - true, если звук выключен.
 */
export function getMutedState() {
    return isMuted;
}
