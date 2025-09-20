import { renderNav } from './ui/components/nav.js';
import { navigate, getRoute } from './core/router.js';
import { initAudio, playTap } from './core/audio.js';
import { initI18n } from './core/i18n.js';

/**
 * Возвращает ближайший элемент (Element) для произвольного node (чтобы избежать ошибок,
 * когда event.target — текстовый узел).
 */
function getClosestElement(node) {
  while (node && node.nodeType !== 1) node = node.parentNode;
  return node;
}

async function initializeApp() {
  console.log('App init');

  // i18n может упасть — ловим ошибки чтобы не ломать всё приложение
  try {
    await initI18n('ru');
  } catch (err) {
    console.error('initI18n error:', err);
  }

  // Навигация — проверяем наличие контейнера и функций
  const navContainer = document.getElementById('bottom-nav');
  const currentRoute = (typeof getRoute === 'function' ? getRoute() : null) || 'taper';

  if (navContainer && typeof renderNav === 'function') {
    try {
      renderNav(navContainer, currentRoute);
    } catch (err) {
      console.error('renderNav error:', err);
    }
  } else {
    console.warn('bottom-nav not found or renderNav is not a function. Skipping renderNav.');
  }

  if (typeof navigate === 'function') {
    try {
      navigate(currentRoute);
    } catch (err) {
      console.error('navigate error:', err);
    }
  }

  // Постоянный обработчик для воспроизведения звука при клике по button/a
  const playOnClick = (ev) => {
    const el = getClosestElement(ev.target);
    if (!el) return;
    if (el.closest('button, a')) {
      try { playTap(); } catch (err) { console.error('playTap error:', err); }
    }
  };

  // Одноразовая инициализация аудио (может быть async). Срабатывает на первом клике пользователя.
  const initAudioOnce = async (ev) => {
    try {
      const maybePromise = initAudio();
      if (maybePromise && typeof maybePromise.then === 'function') {
        await maybePromise;
      }
    } catch (err) {
      console.error('initAudio error:', err);
    }

    // Если первый клик был по кнопке/ссылке — проигрываем звук сразу
    const el = getClosestElement(ev?.target);
    if (el && el.closest('button, a')) {
      try { playTap(); } catch (err) { console.error('playTap error:', err); }
    }

    // Устанавливаем постоянный обработчик кликов
    document.body.addEventListener('click', playOnClick);
  };

  // Регистрация одноразового обработчика — автоматически удалится после первого срабатывания
  document.body.addEventListener('click', initAudioOnce, { once: true });
}

// Запуск: если DOM уже загружен — запускаем сразу, иначе — слушаем DOMContentLoaded
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeApp);
} else {
  initializeApp();
}
