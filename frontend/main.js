import * as screens from './ui/components/screens/index.js';

// --- ИЗМЕНЕНО ---
// Я добавил маршрут для '/taper', чтобы он правильно обрабатывался.
const routes = {
  '/': screens.games,
  '/referrals': screens.referrals,
  '/profile': screens.profile,
  '/settings': screens.settings,
  '/taper': screens.taper,
};

const navigate = (path) => {
  // Проверяем, что мы не пытаемся перейти на ту же страницу
  if (window.location.pathname === path) {
    return;
  }
  window.history.pushState({}, path, window.location.origin + path);
  router();
};

const router = async () => {
  const path = window.location.pathname;
  const screen = routes[path] || routes['/']; // Если путь не найден, переходим на главную

  // Находим и очищаем контейнер приложения
  const app = document.getElementById('app');
  if (app) {
    // Вызываем функцию init для отрисовки нового экрана
    await screen.init(app);
    updateActiveLink(path);
  } else {
    console.error("Элемент с id 'app' не найден!");
  }
};

// Функция для обновления активной ссылки в навигации
const updateActiveLink = (path) => {
    document.querySelectorAll('nav a').forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === path) {
            link.classList.add('active');
        }
    });
};


// --- КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ ---
// Оборачиваем весь код в 'DOMContentLoaded'.
// Это гарантирует, что HTML-документ полностью загрузится перед тем,
// как JavaScript попытается найти и изменить его элементы.
// Это решает ошибку "Cannot set properties of null".
window.addEventListener('DOMContentLoaded', () => {
  document.body.addEventListener('click', (e) => {
    // Убеждаемся, что клик был по ссылке с атрибутом data-link
    if (e.target.matches('[data-link]')) {
      e.preventDefault(); // Предотвращаем стандартный переход по ссылке
      navigate(e.target.getAttribute('href'));
    }
  });

  // Первый запуск роутера при загрузке страницы
  router();
});
