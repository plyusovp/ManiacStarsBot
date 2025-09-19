let audioContext;
let masterGain;

// Pre-create empty buffers for different sounds
// This avoids loading sounds from URLs, which can be problematic.
// Instead, we'll generate simple sounds programmatically.
const soundBuffers = {
    tap: null,
    win: null,
    lose: null,
};

// Creates a simple oscillator-based sound and returns an AudioBuffer
const createTone = (freq, duration, type = 'sine') => {
    if (!audioContext) return null;
    const sampleRate = audioContext.sampleRate;
    const frameCount = sampleRate * duration;
    const buffer = audioContext.createBuffer(1, frameCount, sampleRate);
    const data = buffer.getChannelData(0);
    for (let i = 0; i < frameCount; i++) {
        const time = i / sampleRate;
        data[i] = Math.sin(freq * 2 * Math.PI * time) * Math.exp(-time * 5); // Simple decay
    }
    return buffer;
};

// Function to initialize the AudioContext on user interaction
export const initAudio = () => {
    if (!audioContext) {
        try {
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
            masterGain = audioContext.createGain();
            masterGain.gain.value = 0.5; // Set volume to 50%
            masterGain.connect(audioContext.destination);

            // Generate programmatic sounds
            soundBuffers.tap = createTone(440, 0.1, 'triangle'); // A short 'blip'
            soundBuffers.win = createTone(880, 0.2, 'sine');    // A higher 'win' sound
            soundBuffers.lose = createTone(220, 0.3, 'square');  // A lower 'lose' sound

            console.log("Audio initialized successfully.");
        } catch (e) {
            console.error("Web Audio API is not supported in this browser.", e);
        }
    }
};

// Generic function to play a sound from our buffer cache
const playSound = (buffer) => {
    if (!audioContext || !buffer || masterGain.gain.value === 0) {
        // Resume context if it was suspended
        if (audioContext && audioContext.state === 'suspended') {
            audioContext.resume();
        }
        return;
    }
    const source = audioContext.createBufferSource();
    source.buffer = buffer;
    source.connect(masterGain);
    source.start(0);
};

// Exported functions to play specific sounds
export const playTap = () => playSound(soundBuffers.tap);
export const playWin = () => playSound(soundBuffers.win);
export const playLose = () => playSound(soundBuffers.lose);

// Function to toggle sound on/off
export const toggleSound = (enabled) => {
    if (masterGain) {
        masterGain.gain.value = enabled ? 0.5 : 0;
    }
};
