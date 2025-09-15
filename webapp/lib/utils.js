// Audio context for sound playback
let audioContext;
const sounds = {};

// Preload sounds
async function preloadSound(name, path) {
    try {
        if (!audioContext) {
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
        }
        const response = await fetch(path);
        const arrayBuffer = await response.arrayBuffer();
        const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
        sounds[name] = audioBuffer;
    } catch (e) {
        console.error(`Failed to load sound: ${name}`, e);
    }
}

// Preload all necessary sounds on startup
preloadSound('click', './audio/click.ogg');
preloadSound('win', './audio/win.ogg');
preloadSound('whoosh', './audio/whoosh.ogg');
preloadSound('crash', './audio/crash.ogg');


/**
 * Plays a preloaded sound.
 * @param {string} name - The name of the sound to play ('click', 'win', etc.).
 */
export function playSound(name) {
    if (sounds[name] && audioContext) {
        // Resume context on user interaction if needed
        if (audioContext.state === 'suspended') {
            audioContext.resume();
        }
        const source = audioContext.createBufferSource();
        source.buffer = sounds[name];
        source.connect(audioContext.destination);
        source.start(0);
    }
}

/**
 * Triggers haptic feedback if available in the Telegram WebApp.
 * @param {string} type - 'light', 'medium', 'heavy', 'success', 'warning', 'error'
 */
export function hapticFeedback(type) {
    const tg = window.Telegram?.WebApp;
    if (tg && tg.HapticFeedback) {
        switch (type) {
            case 'light':
                tg.HapticFeedback.impactOccurred('light');
                break;
            case 'medium':
                tg.HapticFeedback.impactOccurred('medium');
                break;
            case 'heavy':
                tg.HapticFeedback.impactOccurred('heavy');
                break;
            case 'success':
                tg.HapticFeedback.notificationOccurred('success');
                break;
            case 'warning':
                tg.HapticFeedback.notificationOccurred('warning');
                break;
            case 'error':
                tg.HapticFeedback.notificationOccurred('error');
                break;
            default:
                break;
        }
    }
}
