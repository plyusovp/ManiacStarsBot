let translations = {};
let currentLanguage = 'en';

// Load translations from the JSON file
async function loadTranslations() {
    try {
        const response = await fetch('./locales/i18n.json');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        translations = await response.json();
    } catch (error) {
        console.error("Could not load translations:", error);
    }
}

// Set the current language
function setLanguage(lang) {
    currentLanguage = lang;
    // Potentially, you could emit an event here to update the UI
    // import { bus } from './bus.js';
    // bus.emit('language:changed');
}

// Get a translation string
export function t(key) {
    return translations[currentLanguage]?.[key] || key;
}

// Initialize the i18n module
export async function initI18n(defaultLang = 'en') {
    setLanguage(defaultLang);
    await loadTranslations();
}
