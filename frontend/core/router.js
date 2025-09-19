import { screens } from '../ui/components/screens/index.js';

export const getRoute = () => window.location.pathname || '/games';

export const navigate = (path, replace = false) => {
    const screenContainer = document.getElementById('screen-container');
    if (!screenContainer) {
        console.error('Screen container #screen-container not found!');
        return;
    }

    const route = screens.find(s => {
        if (s.path.includes(':')) {
            const pathRegex = new RegExp(`^${s.path.replace(/:\w+/g, '([^/]+)')}$`);
            return pathRegex.test(path);
        }
        return s.path === path;
    });

    if (route) {
        if (replace) {
            window.history.replaceState({}, '', path);
        } else {
            window.history.pushState({}, '', path);
        }

        // Clear previous screen
        while (screenContainer.firstChild) {
            screenContainer.removeChild(screenContainer.firstChild);
        }

        // Render new screen
        const screenElement = route.component();
        screenContainer.appendChild(screenElement);

        // Dispatch a custom event to notify other parts of the app (like nav)
        document.dispatchEvent(new CustomEvent('navigate', { detail: { path } }));
    } else {
        console.error(`No route found for path: ${path}`);
        // Optionally, navigate to a 404 page or a default page
        if (path !== '/games') {
             navigate('/games');
        }
    }
};

window.addEventListener('popstate', () => {
    const currentPath = getRoute();
    navigate(currentPath, true);
});
