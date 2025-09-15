export const title = 'UI Kit';

let rootElement = null;

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;

    // Добавляем иконки для наглядности
    let icon = 'ℹ️';
    if (type === 'success') icon = '✅';
    if (type === 'error') icon = '❌';
    if (type === 'warning') icon = '⚠️';
    toast.innerHTML = `${icon} ${message}`;


    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'toast-out 0.5s ease-out forwards';
        toast.addEventListener('animationend', () => toast.remove());
    }, 4000);
}


export function mount(rootEl) {
    rootElement = rootEl;
    rootElement.innerHTML = `
        <!-- Контейнер для Toast-уведомлений -->
        <div id="toast-container" class="toast-container"></div>

        <!-- 1. Карточка (Card) -->
        <div class="card">
            <h2>Card (Карточка)</h2>
            <p>Это стандартная карточка с тенью, скруглениями и анимацией при наведении. Внутри может быть любой контент.</p>
        </div>

        <!-- 2. Кнопки (Buttons) -->
        <div class="card">
            <h2>Buttons (Кнопки)</h2>
            <button class="btn btn-primary">Primary Button</button>
            <button class="btn btn-secondary">Secondary Button</button>
            <button class="btn btn-primary" disabled>Primary Disabled</button>
        </div>

        <!-- 3. Переключатели (Switches) -->
        <div class="card">
            <h2>Switch / Toggle (Переключатель)</h2>
            <div style="display: flex; align-items: center; gap: 15px;">
                 <label class="switch">
                    <input type="checkbox">
                    <span class="switch-track"><span class="switch-thumb"></span></span>
                </label>
                <span>Пружинистый эффект</span>
            </div>
        </div>

        <!-- 4. Модальное окно (Modal) -->
        <div class="card">
            <h2>Modal / Sheet (Панель)</h2>
            <button id="show-modal-btn" class="btn btn-secondary">Показать панель снизу</button>
        </div>
        <!-- Разметка модального окна (изначально скрыта) -->
        <div id="my-modal" class="modal-backdrop">
            <div class="modal-sheet">
                <h2>Модальная панель</h2>
                <p>Этот контент выезжает снизу. Фон затемняется. Чтобы закрыть, нажмите на фон или на кнопку ниже.</p>
                <button id="close-modal-btn" class="btn btn-primary">Закрыть</button>
            </div>
        </div>

        <!-- 5. Уведомления (Toasts) -->
        <div class="card">
            <h2>Toast (Уведомления)</h2>
            <div id="toast-controls" style="display: flex; flex-wrap: wrap; gap: 10px;">
                <button class="btn btn-secondary chip" data-type="success">Success</button>
                <button class="btn btn-secondary chip" data-type="error">Error</button>
                <button class="btn btn-secondary chip" data-type="warning">Warning</button>
            </div>
        </div>

        <!-- 6. Полоса прогресса (Progress Bar) -->
        <div class="card">
            <h2>Progress Bar (Полоса прогресса)</h2>
            <div class="progress-bar">
                <div id="progress-inner" class="progress-bar-inner" style="width: 60%;"></div>
            </div>
        </div>
    `;

    // --- Логика для интерактивных компонентов ---

    // Модальное окно
    const modal = rootElement.querySelector('#my-modal');
    const showModalBtn = rootElement.querySelector('#show-modal-btn');
    const closeModalBtn = rootElement.querySelector('#close-modal-btn');

    const showModal = () => {
        modal.classList.add('is-visible');
        document.body.classList.add('modal-open');
    };
    const closeModal = () => {
        modal.classList.remove('is-visible');
        document.body.classList.remove('modal-open');
    };

    showModalBtn.addEventListener('click', showModal);
    closeModalBtn.addEventListener('click', closeModal);
    modal.addEventListener('click', (e) => {
        if (e.target === modal) { // Закрытие по клику на фон
            closeModal();
        }
    });

    // Уведомления (Toasts)
    rootElement.querySelector('#toast-controls').addEventListener('click', (e) => {
        if (e.target.tagName === 'BUTTON') {
            const type = e.target.dataset.type;
            showToast(`Это уведомление типа "${type}"`, type);
        }
    });
}

export function unmount() {
    // Убираем класс с body, если модальное окно было открыто
    document.body.classList.remove('modal-open');
    rootElement.innerHTML = '';
    rootElement = null;
}
