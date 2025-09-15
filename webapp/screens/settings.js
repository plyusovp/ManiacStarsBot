import * as audio from '../lib/audio.js';

export const titleKey = 'settings_title';

let rootElement = null;
const t = window.ManiacGames.t;

function render() {
    const currentLang = window.ManiacGames.getCurrentLanguage();
    const currentTheme = window.ManiacGames.getCurrentTheme();

    rootElement.innerHTML = `
        <div class="card">
            <h2>${t('settings_general')}</h2>
            <div class="settings-list">
                <div class="setting-item">
                    <label for="sound-toggle">${t('settings_sound')}</label>
                    <label class="switch">
                        <input type="checkbox" id="sound-toggle" ${!audio.getMutedState() ? 'checked' : ''}>
                        <span class="switch-track"><span class="switch-thumb"></span></span>
                    </label>
                </div>
                <div class="setting-item">
                    <label for="haptic-toggle">${t('settings_haptics')}</label>
                    <label class="switch">
                        <input type="checkbox" id="haptic-toggle" checked>
                        <span class="switch-track"><span class="switch-thumb"></span></span>
                    </label>
                </div>
            </div>
        </div>

        <div class="card">
            <h2>${t('settings_appearance')}</h2>
             <div class="settings-list">
                <div class="setting-item">
                    <label>${t('settings_language')}</label>
                    <div id="language-selector" class="segmented-control">
                        <button data-lang="ru" class="${currentLang === 'ru' ? 'active' : ''}">RU</button>
                        <button data-lang="es" class="${currentLang === 'es' ? 'active' : ''}">ES</button>
                    </div>
                </div>
                <div class="setting-item">
                    <label>${t('settings_theme')}</label>
                     <div id="theme-selector" class="segmented-control">
                        <button data-theme="light" class="${currentTheme === 'light' ? 'active' : ''}">${t('settings_theme_light')}</button>
                        <button data-theme="dark" class="${currentTheme === 'dark' ? 'active' : ''}">${t('settings_theme_dark')}</button>
                        <button data-theme="system" class="${currentTheme === 'system' ? 'active' : ''}">${t('settings_theme_system')}</button>
                    </div>
                </div>
            </div>
        </div>

        <div class="card">
            <h2>${t('settings_info')}</h2>
            <div class="settings-links">
                <a href="#" id="show-rules-link">${t('settings_rules')}</a>
                <a href="#">${t('settings_support')}</a>
                <a href="#">${t('settings_privacy')}</a>
            </div>
        </div>
    `;

    addEventListeners();
}

function addEventListeners() {
    const soundToggle = rootElement.querySelector('#sound-toggle');
    soundToggle.addEventListener('change', (e) => {
        audio.setMuted(!e.target.checked);
    });

    const rulesLink = rootElement.querySelector('#show-rules-link');
    rulesLink.addEventListener('click', (e) => {
        e.preventDefault();
        window.ManiacGames.playSound('tap');
        showRulesModal();
    });

    const langSelector = rootElement.querySelector('#language-selector');
    langSelector.addEventListener('click', (e) => {
        const button = e.target.closest('button');
        if (button && button.dataset.lang) {
            const lang = button.dataset.lang;
            if (lang !== window.ManiacGames.getCurrentLanguage()) {
                window.ManiacGames.changeLanguage(lang);
            }
        }
    });

    const themeSelector = rootElement.querySelector('#theme-selector');
    themeSelector.addEventListener('click', (e) => {
        const button = e.target.closest('button');
        if (button && button.dataset.theme) {
            const theme = button.dataset.theme;
            window.ManiacGames.changeTheme(theme);

            // Update active state
            themeSelector.querySelectorAll('button').forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
        }
    });
}

function showRulesModal() {
    let modal = document.getElementById('rules-modal');
    if (modal) modal.remove();

    modal = document.createElement('div');
    modal.id = 'rules-modal';
    modal.className = 'modal-backdrop';
    modal.innerHTML = `
        <div class="modal-sheet">
            <h2>${t('settings_rules_modal_title')}</h2>
            <p>${t('settings_rules_modal_desc')}</p>
            <p><strong>Crash:</strong> ${t('crash_rule_desc', {default: 'Сделайте ставку и заберите выигрыш до того, как график "крашнется". Множитель постоянно растет!'})}</p>
            <p><strong>Dice:</strong> ${t('dice_rule_desc', {default: 'Угадайте, какое число выпадет на кубике. Ставьте на чёт/нечет или на точное число.'})}</p>
            <button id="close-rules-modal" class="btn btn-primary">${t('settings_rules_modal_close')}</button>
        </div>
    `;
    document.body.appendChild(modal);

    const closeModal = () => {
        modal.classList.remove('is-visible');
        document.body.classList.remove('modal-open');
    };

    modal.querySelector('#close-rules-modal').addEventListener('click', () => {
        window.ManiacGames.playSound('tap');
        closeModal();
    });
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModal();
        }
    });

    setTimeout(() => {
        modal.classList.add('is-visible');
        document.body.classList.add('modal-open');
    }, 10);
}


export function mount(rootEl) {
    rootElement = rootEl;
    render();
}

export function unmount() {
     const modal = document.getElementById('rules-modal');
    if (modal) {
        modal.remove();
    }
    document.body.classList.remove('modal-open');
    rootElement = null;
}
