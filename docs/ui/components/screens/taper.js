import { addBalance, getBalance } from '../../../../core/state.js';
import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';

export const title = 'Главная';

// --- Константы ---
const STARS_PER_TAP = 1;
const LARVAE_COUNT = 30; // Количество "личинок" внутри
const STAR_BOUNDS = 0.85; // Область, в которой плавают "личинки"

// --- Переменные модуля ---
let root, elements, state;
let three, animationFrameId;


/**
 * Создает текстуру мягкой, светящейся звезды на 2D-холсте.
 * Это позволяет добиться точного визуального стиля, как на референсе.
 * @returns {THREE.CanvasTexture}
 */
function createStarTexture() {
    const canvas = document.createElement('canvas');
    const size = 512;
    canvas.width = size;
    canvas.height = size;
    const ctx = canvas.getContext('2d');

    // 1. Внешнее дымчатое свечение
    ctx.shadowColor = 'rgba(249, 43, 117, 0.7)';
    ctx.shadowBlur = 80;

    // 2. Основной градиент звезды
    const gradient = ctx.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2.5);
    gradient.addColorStop(0, 'rgba(255, 160, 210, 1)');
    gradient.addColorStop(1, 'rgba(249, 43, 117, 1)');
    ctx.fillStyle = gradient;

    // 3. Рисуем саму форму мягкой звезды с помощью кривых
    const points = 5;
    const outerRadius = size / 2.3;
    const innerRadius = size / 4;

    ctx.beginPath();
    let angle = -Math.PI / 2;
    const angleStep = Math.PI / points;

    // Начальная точка
    ctx.moveTo(size/2 + Math.cos(angle) * outerRadius, size/2 + Math.sin(angle) * outerRadius);

    // Проходим по всем вершинам, соединяя их сглаженными кривыми
    for (let i = 0; i < points * 2; i++) {
        let radius = (i % 2) === 1 ? innerRadius : outerRadius;
        let nextAngle = angle + angleStep;

        let cp1_angle = angle + angleStep * 0.5;
        let cp1_radius_factor = (i % 2) === 0 ? 1.1 : 0.8;

        let cp1x = size/2 + Math.cos(cp1_angle) * radius * cp1_radius_factor;
        let cp1y = size/2 + Math.sin(cp1_angle) * radius * cp1_radius_factor;

        let endX = size/2 + Math.cos(nextAngle) * radius;
        let endY = size/2 + Math.sin(nextAngle) * radius;

        ctx.quadraticCurveTo(cp1x, cp1y, endX, endY);
        angle = nextAngle;
    }
    ctx.closePath();
    ctx.fill();

    return new THREE.CanvasTexture(canvas);
}


/**
 * Инициализация 3D сцены
 */
function initThree() {
    const container = elements.canvasContainer;
    const { width, height } = container.getBoundingClientRect();

    // Scene, Camera, Renderer
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
    camera.position.z = 2.8;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    // Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
    scene.add(ambientLight);

    // Star Group (for easier animation)
    const starGroup = new THREE.Group();
    scene.add(starGroup);

    // 1. Основное тело звезды (текстура на плоскости)
    const starTexture = createStarTexture();
    const starMaterial = new THREE.MeshBasicMaterial({
        map: starTexture,
        transparent: true,
    });
    const starGeometry = new THREE.PlaneGeometry(3.8, 3.8);
    const starMesh = new THREE.Mesh(starGeometry, starMaterial);
    starGroup.add(starMesh);

    // 2. Движущиеся "Личинки" (система частиц)
    const larvaePositions = new Float32Array(LARVAE_COUNT * 3);
    const larvaeData = []; // Для хранения скорости и других данных

    for (let i = 0; i < LARVAE_COUNT; i++) {
        // Генерируем случайную позицию внутри круга
        const angle = Math.random() * Math.PI * 2;
        const radius = Math.random() * STAR_BOUNDS;
        larvaePositions[i * 3] = Math.cos(angle) * radius;
        larvaePositions[i * 3 + 1] = Math.sin(angle) * radius;
        larvaePositions[i * 3 + 2] = 0.1; // Слегка впереди звезды

        larvaeData.push({
            velocity: new THREE.Vector3((Math.random() - 0.5) * 0.005, (Math.random() - 0.5) * 0.005, 0),
        });
    }
    const larvaeGeom = new THREE.BufferGeometry();
    larvaeGeom.setAttribute('position', new THREE.BufferAttribute(larvaePositions, 3));

    const larvaeMat = new THREE.PointsMaterial({
        color: 0xffe0ff,
        size: 0.05,
        blending: THREE.AdditiveBlending,
        transparent: true,
        opacity: 0.8,
        sizeAttenuation: true
    });
    const larvae = new THREE.Points(larvaeGeom, larvaeMat);
    starGroup.add(larvae);

    // Post-processing (Glow Effect)
    const composer = new EffectComposer(renderer);
    composer.addPass(new RenderPass(scene, camera));
    const bloomPass = new UnrealBloomPass(new THREE.Vector2(width, height), 1.0, 0.5, 0.2);
    composer.addPass(bloomPass);

    three = { scene, camera, renderer, composer, starGroup, larvae, larvaeData };

    // Handle Resize
    const onResize = () => {
        const { width, height } = container.getBoundingClientRect();
        camera.aspect = width / height;
        camera.updateProjectionMatrix();
        renderer.setSize(width, height);
        composer.setSize(width, height);
    };
    window.addEventListener('resize', onResize);

    return {
        dispose: () => window.removeEventListener('resize', onResize)
    };
}


/**
 * Анимационный цикл
 */
const clock = new THREE.Clock();
function animate() {
    const elapsedTime = clock.getElapsedTime();

    if (three) {
        // Плавное покачивание звезды
        three.starGroup.rotation.z = Math.sin(elapsedTime * 0.5) * 0.05;
        three.starGroup.position.y = Math.sin(elapsedTime * 0.7) * 0.05;

        // Анимация "личинок"
        const positions = three.larvae.geometry.attributes.position;
        const starRadiusSq = STAR_BOUNDS * STAR_BOUNDS;

        for (let i = 0; i < three.larvaeData.length; i++) {
            const data = three.larvaeData[i];

            let x = positions.getX(i) + data.velocity.x;
            let y = positions.getY(i) + data.velocity.y;

            // Отталкиваем от краев круга
            if (x*x + y*y > starRadiusSq) {
                data.velocity.x *= -1;
                data.velocity.y *= -1;
            }

            // Добавляем случайное блуждание
            data.velocity.x += (Math.random() - 0.5) * 0.0002;
            data.velocity.y += (Math.random() - 0.5) * 0.0002;
            // Ограничиваем максимальную скорость
            data.velocity.clampLength(0.001, 0.004);

            positions.setXY(i, x, y);
        }
        positions.needsUpdate = true; // Важно для обновления позиций

        three.composer.render();
    }
    animationFrameId = requestAnimationFrame(animate);
}

/**
 * Анимация счётчика-флиппера
 */
function updateFlipCounter(start, end) {
    const container = elements.balanceCounter;
    const startStr = start.toString().padStart(end.toString().length, ' ');
    const endStr = end.toString();

    container.innerHTML = ''; // Очищаем контейнер

    for (let i = 0; i < endStr.length; i++) {
        const charContainer = document.createElement('div');
        charContainer.className = 'flip-char';

        const s1 = startStr[i] || ' ';
        const s2 = endStr[i];

        charContainer.innerHTML = `
            <div class="flip-char-inner">
                <div class="flip-char-front">${s1}</div>
                <div class="flip-char-back">${s2}</div>
            </div>
        `;
        container.appendChild(charContainer);

        if (s1 !== s2) {
            setTimeout(() => {
                charContainer.classList.add('animate');
                window.ManiacGames.playSound('counterTick', { delay: Math.random() * 0.2 });
            }, i * 50); // Небольшая задержка для каждой цифры
        }
    }
}

/**
 * Показывает эффекты при тапе: взрыв частиц и летящий текст
 */
function showTapEffects(x, y) {
    const container = elements.feedbackContainer;

    const text = document.createElement('div');
    text.className = 'floating-text-new';
    text.textContent = `+${STARS_PER_TAP}`;
    container.appendChild(text);

    text.style.left = `${x}px`;
    text.style.top = `${y}px`;

    const counterRect = elements.balanceCounter.getBoundingClientRect();
    const endX = counterRect.left + counterRect.width / 2;
    const endY = counterRect.top + counterRect.height / 2;

    text.style.setProperty('--fly-to-x', `translateX(${endX - x}px)`);
    text.style.setProperty('--fly-to-y', `translateY(${endY - y}px)`);

    const particleCount = 8 + Math.floor(Math.random() * 5);
    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle-burst';
        container.appendChild(particle);

        const angle = Math.random() * Math.PI * 2;
        const distance = 60 + Math.random() * 40;

        particle.style.left = `${x}px`;
        particle.style.top = `${y}px`;
        particle.style.setProperty('--tx', `${Math.cos(angle) * distance}px`);
        particle.style.setProperty('--ty', `${Math.sin(angle) * distance}px`);
        particle.style.background = Math.random() > 0.5 ? 'var(--primary-1)' : 'var(--primary-2)';

        setTimeout(() => particle.remove(), 600);
    }

    window.ManiacGames.playSound('swoosh');
    setTimeout(() => text.remove(), 700);
}


/**
 * Основной обработчик тапа
 */
function handleTap(event) {
    const tapX = event.clientX || (event.touches && event.touches[0].clientX);
    const tapY = event.clientY || (event.touches && event.touches[0].clientY);

    if (tapX === undefined) return;

    const oldBalance = getBalance();
    addBalance(STARS_PER_TAP);
    const newBalance = getBalance();

    updateFlipCounter(oldBalance, newBalance);
    showTapEffects(tapX, tapY);

    if (three && !state.isStarAnimating) {
        state.isStarAnimating = true;
        const group = three.starGroup;
        const startScale = 1;
        let elapsed = 0;
        const duration = 300;

        function squeeze() {
            elapsed += 16.67;
            const progress = Math.min(elapsed / duration, 1);
            const scale = 1 - 0.15 * Math.sin(progress * Math.PI);
            group.scale.set(scale, scale, scale);

            if (progress < 1) {
                requestAnimationFrame(squeeze);
            } else {
                group.scale.set(startScale, startScale, startScale);
                state.isStarAnimating = false;
            }
        }
        squeeze();
    }

    window.ManiacGames.playSound('crystalClick');
    window.ManiacGames.hapticFeedback('light');
}

/**
 * Обработчик наклона устройства (гироскоп)
 */
function handleDeviceMotion(event) {
    if (!three || !event.gamma || !event.beta) return;

    const gamma = THREE.MathUtils.degToRad(event.gamma) * 0.1;
    const beta = THREE.MathUtils.degToRad(event.beta) * 0.1;

    const targetPosition = new THREE.Vector3(gamma, -beta, 0);
    three.starGroup.position.lerp(targetPosition, 0.05);
}

function requestMotionPermission() {
    if (typeof DeviceMotionEvent !== 'undefined' && typeof DeviceMotionEvent.requestPermission === 'function') {
        DeviceMotionEvent.requestPermission()
            .then(permissionState => {
                if (permissionState === 'granted') {
                    window.addEventListener('devicemotion', handleDeviceMotion);
                }
            })
            .catch(console.error);
    } else {
        window.addEventListener('devicemotion', handleDeviceMotion);
    }
}


export function mount(rootEl) {
    root = rootEl;
    state = { isStarAnimating: false };

    root.innerHTML = `
        <div class="tapper-wrapper">
            <div class="tapper-balance-container">
                <span class="tapper-balance-icon">⭐</span>
                <div id="tapper-balance-counter" class="tapper-balance-counter"></div>
            </div>

            <div id="tapper-canvas-container" class="tapper-canvas-container"></div>

            <div id="tap-feedback-container" class="tap-feedback-container"></div>

            <div class="tapper-energy-info"></div>
        </div>
    `;

    elements = {
        balanceCounter: root.querySelector('#tapper-balance-counter'),
        canvasContainer: root.querySelector('#tapper-canvas-container'),
        feedbackContainer: root.querySelector('#tap-feedback-container'),
    };

    const threeCleanup = initThree();
    state.disposeThree = threeCleanup.dispose;

    updateFlipCounter(0, getBalance());
    animate();

    elements.canvasContainer.addEventListener('pointerdown', handleTap);

    requestMotionPermission();
}

export function unmount() {
    if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
    }

    if (state && state.disposeThree) {
        state.disposeThree();
    }

    if (three) {
        three.scene.traverse(object => {
            if (object.geometry) object.geometry.dispose();
            if (object.material) {
                if(Array.isArray(object.material)) {
                    object.material.forEach(m => m.dispose());
                } else {
                    object.material.dispose();
                }
            }
        });
        three.renderer.dispose();
    }

    window.removeEventListener('devicemotion', handleDeviceMotion);

    root = null;
    elements = null;
    state = null;
    three = null;
}
