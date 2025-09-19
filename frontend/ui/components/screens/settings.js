import { translate, setLanguage, getCurrentLanguage } from '../../../core/i18n.js';
import { toggleSound, isSoundEnabled } from '../../../core/audio.js';

export const SettingsScreen = () => {
    const screen = document.createElement('div');
    screen.className = 'screen';

    const render = () => {
        screen.innerHTML = `
            <div class="card glass-card neon-accent">
                <h2>${translate('settings.title')}</h2>

                <div class="setting-item">
                    <label for="sound-toggle">${translate('settings.sound')}</label>
                    <label class="switch">
                        <input type="checkbox" id="sound-toggle" ${isSoundEnabled() ? 'checked' : ''}>
                        <span class="slider round"></span>
                    </label>
                </div>

                <div class="setting-item">
                    <label for="language-select">${translate('settings.language')}</label>
                    <select id="language-select">
                        <option value="en" ${getCurrentLanguage() === 'en' ? 'selected' : ''}>English</option>
                        <option value="ru" ${getCurrentLanguage() === 'ru' ? 'selected' : ''}>Русский</option>
                    </select>
                </div>
            </div>
        `;

        const soundToggle = screen.querySelector('#sound-toggle');
        soundToggle.addEventListener('change', (e) => {
            toggleSound(e.target.checked);
        });

        const langSelect = screen.querySelector('#language-select');
        langSelect.addEventListener('change', (e) => {
            setLanguage(e.target.value);
            // Re-render this screen and the nav to reflect language changes
            render();
            document.dispatchEvent(new CustomEvent('languageChanged'));
        });
    };

    render();
    return screen;
};
