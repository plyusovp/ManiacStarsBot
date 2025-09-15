// --- Модуль для управления текстами и локализацией (i18n) ---

const LANG_KEY = 'mg.lang';
let translations = {};
let currentLang = localStorage.getItem(LANG_KEY) || 'ru'; // По умолчанию русский

/**
 * Загружает JSON-файл с переводами.
 */
async function loadTranslations() {
    try {
        const response = await fetch('/locales/i18n.json');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        translations = await response.json();
    } catch (error) {
        console.error("Could not load translations:", error);
        // В случае ошибки можно загрузить резервный объект
        translations = { ru: { "error_loading": "Ошибка загрузки текстов" } };
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
        // Устанавливаем атрибут lang для всего документа для CSS и доступности
        document.documentElement.lang = lang;
    } else {
        console.warn(`Language "${lang}" not found in translations.`);
    }
}

/**
 * Возвращает переведенную строку по ключу.
 * @param {string} key - Ключ для поиска в JSON.
 * @param {object} [params] - Объект для замены плейсхолдеров (e.g., { count: 5 }).
 * @returns {string} - Переведенная строка или сам ключ, если перевод не найден.
 */
export function t(key, params = {}) {
    let text = translations[currentLang]?.[key] || key;

    // Замена плейсхолдеров
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
