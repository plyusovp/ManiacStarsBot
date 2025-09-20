// Этот модуль - наш "музыкальный центр". Он загружает все звуки при старте
// и позволяет легко проигрывать их по короткому имени (ID).

// --- Карта всех звуковых эффектов в приложении ---
// Ключ - это ID звука, значение - путь к файлу.
const SOUND_MAP = {
    tap: './assets/sfx/tap.mp3',
    win: './assets/sfx/win.mp3',
    lose: './assets/sfx/lose.mp3',
    crash_bust: './assets/sfx/crash_bust.mp3',
    slots_spin: './assets/sfx/slots_spin.mp3',
    slots_stop: './assets/sfx/slots_stop.mp3',
    bigwin: './assets/sfx/bigwin.mp3',
    // TODO: Добавь сюда остальные звуки, когда они у тебя появятся
};

const audioContext = new (window.AudioContext || window.webkitAudioContext)();
const sounds = {};
let isMuted = false;

/**
 * Загружает все звуковые файлы, указанные в SOUND_MAP.
 * Эту функцию нужно вызвать один раз при старте приложения.
 */
async function loadAllSounds() {
    console.log('[Audio] Загрузка звуков...');
    for (const id in SOUND_MAP) {
        try {
            const response = await fetch(SOUND_MAP[id]);
            const arrayBuffer = await response.arrayBuffer();
            const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
            sounds[id] = audioBuffer;
        } catch (error) {
            console.error(`Не удалось загрузить звук "${id}":`, error);
        }
    }
    console.log('[Audio] Все звуки успешно загружены!');
}

/**
 * Проигрывает звук по его ID.
 * @param {string} id - ID звука из SOUND_MAP (например, 'win').
 */
function play(id) {
    if (isMuted || !sounds[id] || !audioContext) return;

    // Возобновляем контекст, если он был приостановлен браузером
    if (audioContext.state === 'suspended') {
        audioContext.resume();
    }

    const source = audioContext.createBufferSource();
    source.buffer = sounds[id];
    source.connect(audioContext.destination);
    source.start(0);
}

/**
 * Включает или выключает все звуки в приложении.
 * @param {boolean} mutedState - true, чтобы выключить звук, false - чтобы включить.
 */
function setMuted(mutedState) {
    isMuted = mutedState;
    console.log(`[Audio] Звук ${isMuted ? 'выключен' : 'включен'}.`);
    // TODO: Сохранить этот выбор в localStorage, чтобы он запоминался
}

// Экспортируем наш аудио-менеджер
export const audio = {
    load: loadAllSounds,
    play: play,
    setMuted: setMuted,
};