import { screens } from '../ui/components/screens/index.js';

// Эта функция теперь будет смотреть на URL после знака #
export const getRoute = () => window.location.hash.substring(1);

export const navigate = (route) => {
    const screenContainer = document.getElementById('screen-container');
    if (!screenContainer) {
        console.error('Screen container #screen-container not found!');
        return;
    }

    // Находим нужный компонент экрана по его ID
    const screenComponent = Object.values(screens).find(s => s.id === route);

    if (screenComponent) {
        // Устанавливаем новый хэш в URL, чтобы страница обновлялась
        window.location.hash = route;

        // Очищаем предыдущий экран
        while (screenContainer.firstChild) {
            screenContainer.removeChild(screenContainer.firstChild);
        }

        // Вызываем функцию init нового экрана
        if (typeof screenComponent.init === 'function') {
            screenComponent.init(screenContainer);
        } else {
            console.error(`Screen component for "${route}" has no init function!`);
        }

    } else {
        console.error(`No screen found for route: ${route}`);
        // Если маршрут не найден, переходим на экран "taper" по умолчанию
        if (route !== 'taper') {
             navigate('taper');
        }
    }
};

// Обрабатываем изменение хэша (например, при использовании кнопок "назад/вперед" в браузере)
window.addEventListener('hashchange', () => {
    const currentRoute = getRoute() || 'taper';
    navigate(currentRoute);
});
