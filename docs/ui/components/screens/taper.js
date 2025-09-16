import { addBalance, getBalance } from '../../../core/state.js';
import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';

export const title = 'Главная';

// --- Константы ---
const STARS_PER_TAP = 1;

// --- Переменные модуля ---
let root, elements, state;
let three, animationFrameId;

// --- Шейдеры для плазмы (Новая, более надёжная версия) ---
const plasmaVertexShader = `
  varying vec2 vUv;
  void main() {
    vUv = uv;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

const plasmaFragmentShader = `
  precision mediump float;
  uniform float time;
  uniform vec3 color1;
  uniform vec3 color2;
  varying vec2 vUv;

  void main() {
    // Более простой и надёжный эффект плазмы на основе синусоид
    float v1 = sin(vUv.x * 8.0 + time * 0.5);
    float v2 = sin(vUv.y * 10.0 - time * 0.8);
    float v3 = sin(length(vUv - 0.5) * 20.0 + time);
    float value = (v1 + v2 + v3) / 3.0;

    vec3 finalColor = mix(color1, color2, (value + 1.0) * 0.5);

    // Плавное затухание по краям для создания объёма
    float alpha = 1.0 - (length(vUv - 0.5) * 2.0);
    gl_FragColor = vec4(finalColor, alpha);
  }
`;

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
    const directionalLight = new THREE.DirectionalLight(0xffffff, 1.5);
    directionalLight.position.set(5, 5, 5);
    scene.add(directionalLight);

    // Star Group (for easier animation)
    const starGroup = new THREE.Group();
    scene.add(starGroup);

    // 1. Outer Crystal (Новый, более надёжный материал)
    const crystalGeom = new THREE.IcosahedronGeometry(1.2, 1);
    const crystalMat = new THREE.MeshPhongMaterial({
        color: 0xffffff,
        shininess: 100,
        specular: 0xeeeeff,
        transparent: true,
        opacity: 0.4,
    });
    const crystal = new THREE.Mesh(crystalGeom, crystalMat);
    starGroup.add(crystal);

    // 2. Inner Plasma
    const plasmaGeom = new THREE.SphereGeometry(0.8, 32, 32);
    const plasmaMat = new THREE.ShaderMaterial({
        uniforms: {
            time: { value: 0 },
            color1: { value: new THREE.Color(0x8A7CFF) }, // violet
            color2: { value: new THREE.Color(0xF92B75) }  // pink
        },
        vertexShader: plasmaVertexShader,
        fragmentShader: plasmaFragmentShader,
        transparent: true,
        blending: THREE.AdditiveBlending,
    });
    const plasma = new THREE.Mesh(plasmaGeom, plasmaMat);
    starGroup.add(plasma);

    // 3. Background Starfield
    const starVertices = [];
    for (let i = 0; i < 8000; i++) {
        const x = THREE.MathUtils.randFloatSpread(100);
        const y = THREE.MathUtils.randFloatSpread(100);
        const z = THREE.MathUtils.randFloatSpread(100);
        if (new THREE.Vector3(x, y, z).length() > 20) { // Keep them in the distance
             starVertices.push(x, y, z);
        }
    }
    const starGeometry = new THREE.BufferGeometry();
    starGeometry.setAttribute('position', new THREE.Float32BufferAttribute(starVertices, 3));
    const starMaterial = new THREE.PointsMaterial({ color: 0x555555, size: 0.1 });
    const starfield = new THREE.Points(starGeometry, starMaterial);
    scene.add(starfield);


    // Post-processing (Glow Effect)
    const composer = new EffectComposer(renderer);
    composer.addPass(new RenderPass(scene, camera));
    const bloomPass = new UnrealBloomPass(new THREE.Vector2(width, height), 0.8, 0.4, 0.6);
    composer.addPass(bloomPass);

    three = { scene, camera, renderer, composer, starGroup, plasmaMat, starfield };

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
        // Анимация в состоянии покоя
        three.starGroup.rotation.y = elapsedTime * 0.2;
        three.starGroup.rotation.x = Math.sin(elapsedTime * 0.5) * 0.1;
        three.plasmaMat.uniforms.time.value = elapsedTime;
        three.starfield.rotation.y = elapsedTime * 0.02;

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

    // 1. Создаём "+1"
    const text = document.createElement('div');
    text.className = 'floating-text-new';
    text.textContent = `+${STARS_PER_TAP}`;
    container.appendChild(text);

    text.style.left = `${x}px`;
    text.style.top = `${y}px`;

    // Задаём конечную точку анимации (координаты счётчика)
    const counterRect = elements.balanceCounter.getBoundingClientRect();
    const endX = counterRect.left + counterRect.width / 2;
    const endY = counterRect.top + counterRect.height / 2;

    text.style.setProperty('--fly-to-x', `translateX(${endX - x}px)`);
    text.style.setProperty('--fly-to-y', `translateY(${endY - y}px)`);

    // 2. Создаём взрыв частиц
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

    // 1. Обновляем баланс
    const oldBalance = getBalance();
    addBalance(STARS_PER_TAP);
    const newBalance = getBalance();

    updateFlipCounter(oldBalance, newBalance);

    // 2. Эффекты
    showTapEffects(tapX, tapY);

    // 3. Анимация звезды ("сжатие-разжатие")
    if (three && !state.isStarAnimating) {
        state.isStarAnimating = true;
        const group = three.starGroup;
        const startScale = 1;
        group.scale.set(startScale, startScale, startScale); // Сброс на случай
        let elapsed = 0;
        const duration = 300; // 0.3s

        function squeeze() {
            elapsed += 16.67; // ~60fps
            const progress = Math.min(elapsed / duration, 1);
            // Пружинистая анимация
            const scale = 1 - 0.2 * Math.sin(progress * Math.PI) * Math.exp(-progress * 2);
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

    // 4. Звук и вибрация
    window.ManiacGames.playSound('crystalClick');
    window.ManiacGames.hapticFeedback('light');
}

/**
 * Обработчик наклона устройства (гироскоп)
 */
function handleDeviceMotion(event) {
    if (!three || !event.gamma || !event.beta) return;

    // Плавное вращение вместо резкого смещения
    const gamma = THREE.MathUtils.degToRad(event.gamma) * 0.1; // наклон влево-вправо
    const beta = THREE.MathUtils.degToRad(event.beta) * 0.1;   // наклон вперед-назад

    // Плавное движение к целевому вращению
    const targetRotation = new THREE.Quaternion().setFromEuler(new THREE.Euler(beta, gamma, 0, 'XYZ'));
    three.starGroup.quaternion.slerp(targetRotation, 0.05);
}

function requestMotionPermission() {
    if (typeof DeviceOrientationEvent !== 'undefined' && typeof DeviceOrientationEvent.requestPermission === 'function') {
        DeviceOrientationEvent.requestPermission()
            .then(permissionState => {
                if (permissionState === 'granted') {
                    window.addEventListener('deviceorientation', handleDeviceMotion);
                }
            })
            .catch(console.error);
    } else {
        // Для устройств без необходимости запрашивать разрешение
        window.addEventListener('deviceorientation', handleDeviceMotion);
    }
}


export function mount(rootEl) {
    root = rootEl;
    state = {
        isStarAnimating: false,
    };

    root.innerHTML = `
        <div class="tapper-wrapper">
            <div class="tapper-balance-container">
                <span class="tapper-balance-icon">⭐</span>
                <div id="tapper-balance-counter" class="tapper-balance-counter"></div>
            </div>

            <div id="tapper-canvas-container" class="tapper-canvas-container">
                <!-- Сюда будет вставлен canvas -->
            </div>

            <div id="tap-feedback-container" class="tap-feedback-container"></div>

            <div class="tapper-energy-info">
                <!-- Место для полосы энергии, если понадобится -->
            </div>
        </div>
    `;

    elements = {
        balanceCounter: root.querySelector('#tapper-balance-counter'),
        canvasContainer: root.querySelector('#tapper-canvas-container'),
        feedbackContainer: root.querySelector('#tap-feedback-container'),
    };

    // Инициализация
    const threeCleanup = initThree();
    state.disposeThree = threeCleanup.dispose;

    updateFlipCounter(0, getBalance());
    animate();

    elements.canvasContainer.addEventListener('pointerdown', handleTap);

    // Запрашиваем доступ к гироскопу
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
        // Очистка памяти Three.js
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

    window.removeEventListener('deviceorientation', handleDeviceMotion);

    root = null;
    elements = null;
    state = null;
    three = null;
}
