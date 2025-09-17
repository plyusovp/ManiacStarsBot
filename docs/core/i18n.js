// --- Модуль для управления текстами и локализацией (i18n) ---

const LANG_KEY = 'mg.lang';
let translations = {};
let currentLang = localStorage.getItem(LANG_KEY) || 'ru'; // По умолчанию русский

// Резервные тексты на случай, если файл не загрузится
const fallbackTranslations = {
    "ru": { "nav_main": "Главная", "nav_games": "Игры", "nav_friends": "Друзья", "nav_profile": "Профиль", "nav_settings": "Настройки", "error_loading": "Ошибка загрузки текстов" },
    "es": { "nav_main": "Principal", "nav_games": "Juegos", "nav_friends": "Amigos", "nav_profile": "Perfil", "nav_settings": "Ajustes", "error_loading": "Error loading texts" }
};

/**
 * Загружает JSON-файл с переводами.
 */
async function loadTranslations() {
     try {
        const response = await fetch('locales/i18n.json');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        translations = await response.json();
    } catch (error) {
        console.error("Could not load translations file, using fallback:", error);
        alert("DEBUG: Could not load i18n.json. Using fallback. Error: " + error.message);
        translations = fallbackTranslations;
    }
}

/**
 * Устанавливает текущий язык и сохраняет выбор.
 * @param {string} lang - Код языка (e.g., 'ru', 'es').
 */
export function setLanguage(lang) {
    if (translations[lang]) {
        currentLang = lang;
       localStorage.setItem(LANG_KEY, lang);
        document.documentElement.lang = lang;
    } else {
        console.warn(`Language "${lang}" not found in translations.`);
    }
}

/**
 * Возвращает переведенную строку по ключу.
 * @param {string} key - Ключ для поиска в JSON.
 * @param {object} [params] - Объект для замены плейсхолдеров.
 * @returns {string} - Переведенная строка или сам ключ, если перевод не найден.
 */
export function t(key, params = {}) {
     let text = translations[currentLang]?.[key] || key;
     for (const param in params) {
        text = text.replace(new RegExp(`{{${param}}}`, 'g'), params[param]);
     }
    return text;
}

/**
 * Инициализация модуля: загрузка переводов и установка языка.
 */
export async function init() {
    await loadTranslations();
    setLanguage(currentLang);
}

/**
 * Возвращает текущий язык.
 * @returns {string}
 */
export function getCurrentLanguage() {
    return currentLang;
}
