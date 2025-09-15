import * as THREE from 'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.module.js';
import { UnrealBloomPass } from 'https://cdn.jsdelivr.net/npm/three@0.128.0/examples/jsm/postprocessing/UnrealBloomPass.js';
import { EffectComposer } from 'https://cdn.jsdelivr.net/npm/three@0.128.0/examples/jsm/postprocessing/EffectComposer.js';
import { RenderPass } from 'https://cdn.jsdelivr.net/npm/three@0.128.0/examples/jsm/postprocessing/RenderPass.js';
import { getBalance, subBalance, addBalance, updateStats } from '../lib/balance.js';
import { applyPayout } from '../lib/houseedge.js';
import { randomInt } from '../lib/rng.js';

export const title = '3D Кости';

// --- Game Payouts ---
const PAYOUT_EVEN_ODD = 1.9;
const PAYOUT_EXACT = 5.5;

// --- State ---
let root, elements, state;
let renderer, scene, camera, composer, dice;
let animationFrameId;

function resetState() {
    state = {
        isRolling: false,
        betAmount: 10,
        betType: null, // 'even', 'odd', or a number 1-6
        targetFace: null,
    };
}

function initScene(container) {
    try {
        scene = new THREE.Scene();
        const width = container.clientWidth;
        const height = container.clientHeight;

        // --- Camera ---
        camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
        camera.position.z = 5;

        // --- Renderer ---
        renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.setSize(width, height);
        container.appendChild(renderer.domElement);

        // --- Lighting ---
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
        scene.add(ambientLight);
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(5, 10, 7.5);
        scene.add(directionalLight);

        // --- Post-processing (Bloom) ---
        const renderScene = new RenderPass(scene, camera);
        const bloomPass = new UnrealBloomPass(new THREE.Vector2(width, height), 1.0, 0.6, 0.2);
        composer = new EffectComposer(renderer);
        composer.addPass(renderScene);
        composer.addPass(bloomPass);

        // --- Dice ---
        dice = createDice();
        scene.add(dice);

        animate();

        // --- Mouse Controls ---
        let isDragging = false;
        let previousMousePosition = { x: 0, y: 0 };
        container.onmousedown = (e) => isDragging = true;
        container.onmouseup = (e) => isDragging = false;
        container.onmouseleave = (e) => isDragging = false;
        container.onmousemove = (e) => {
            if (!isDragging) return;
            const deltaMove = {
                x: e.offsetX - previousMousePosition.x,
                y: e.offsetY - previousMousePosition.y
            };
            dice.rotation.y += deltaMove.x * 0.01;
            dice.rotation.x += deltaMove.y * 0.01;
            previousMousePosition = { x: e.offsetX, y: e.offsetY };
        };

        return true;
    } catch (error) {
        console.error("WebGL initialization failed:", error);
        return false;
    }
}

function createDice() {
    const group = new THREE.Group();

    // Main cube
    const geometry = new THREE.BoxGeometry(2, 2, 2);
    // Rounded edges can be complex, using a simple box for now.
    // For real rounded edges, one would use a RoundedBoxGeometry helper.
    const material = new THREE.MeshStandardMaterial({
        color: 0x2a2a3a,
        roughness: 0.4,
        metalness: 0.1,
    });
    const cube = new THREE.Mesh(geometry, material);
    group.add(cube);

    // Dots (Pips)
    const dotGeo = new THREE.CircleGeometry(0.15, 16);
    const dotMat = new THREE.MeshBasicMaterial({ color: 0x9f50ff, toneMapped: false });

    const dotPositions = {
        1: [[0, 0, 1.01]],
        2: [[0.5, 0.5, 1.01], [-0.5, -0.5, 1.01]],
        3: [[0.5, 0.5, 1.01], [0, 0, 1.01], [-0.5, -0.5, 1.01]],
        4: [[0.5, 0.5, 1.01], [-0.5, -0.5, 1.01], [0.5, -0.5, 1.01], [-0.5, 0.5, 1.01]],
        5: [[0.5, 0.5, 1.01], [-0.5, -0.5, 1.01], [0.5, -0.5, 1.01], [-0.5, 0.5, 1.01], [0, 0, 1.01]],
        6: [[0.5, 0.5, 1.01], [-0.5, -0.5, 1.01], [0.5, -0.5, 1.01], [-0.5, 0.5, 1.01], [0.5, 0, 1.01], [-0.5, 0, 1.01]]
    };

    const rotations = [
        { face: 1, rot: [0, 0, 0] }, // front
        { face: 6, rot: [Math.PI, 0, 0] }, // back
        { face: 2, rot: [Math.PI / 2, 0, 0] }, // bottom
        { face: 5, rot: [-Math.PI / 2, 0, 0] }, // top
        { face: 3, rot: [0, Math.PI / 2, 0] }, // right
        { face: 4, rot: [0, -Math.PI / 2, 0] }, // left
    ];

    rotations.forEach(({face, rot}) => {
        dotPositions[face].forEach(pos => {
            const dot = new THREE.Mesh(dotGeo, dotMat);
            dot.position.set(pos[0], pos[1], pos[2]);
            dot.rotation.set(rot[0], rot[1], rot[2]);
            // This is a simplified way to place dots; a correct way would be creating faces and applying textures or decals.
            // For this demo, we'll just rotate the whole die to the target face.
            group.add(dot);
        });
    });

    return group;
}

const faceRotations = [
    new THREE.Quaternion().setFromEuler(new THREE.Euler(0, 0, 0)), // 1
    new THREE.Quaternion().setFromEuler(new THREE.Euler(-Math.PI / 2, 0, 0)), // 2
    new THREE.Quaternion().setFromEuler(new THREE.Euler(0, -Math.PI / 2, 0)), // 3
    new THREE.Quaternion().setFromEuler(new THREE.Euler(0, Math.PI / 2, 0)), // 4
    new THREE.Quaternion().setFromEuler(new THREE.Euler(Math.PI / 2, 0, 0)), // 5
    new THREE.Quaternion().setFromEuler(new THREE.Euler(Math.PI, 0, 0)), // 6
];

async function rollDice(targetFace) {
    state.isRolling = true;
    window.ManiacGames.playSound('whoosh');
    window.ManiacGames.hapticFeedback('medium');

    const startRotation = dice.quaternion.clone();
    const randomRotation = new THREE.Quaternion().setFromEuler(
        new THREE.Euler(
            Math.random() * Math.PI * 4,
            Math.random() * Math.PI * 4,
            Math.random() * Math.PI * 4
        )
    );
    const targetRotation = faceRotations[targetFace - 1].clone();

    const duration = 1800;
    const startTime = performance.now();

    return new Promise(resolve => {
        function animateRoll() {
            const elapsed = performance.now() - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const easedProgress = 1 - Math.pow(1 - progress, 3); // Ease out cubic

            const tempQuaternion = new THREE.Quaternion();
            THREE.Quaternion.slerp(startRotation, randomRotation, tempQuaternion, easedProgress);
            THREE.Quaternion.slerp(tempQuaternion, targetRotation, tempQuaternion, easedProgress);

            dice.quaternion.copy(tempQuaternion);

            if (progress < 1) {
                requestAnimationFrame(animateRoll);
            } else {
                dice.quaternion.copy(targetRotation); // Ensure it ends perfectly
                state.isRolling = false;
                resolve();
            }
        }
        animateRoll();
    });
}

function animate() {
    animationFrameId = requestAnimationFrame(animate);
    if(composer) composer.render();
}

async function playGame() {
    if (state.isRolling) return;
    if (getBalance() < state.betAmount) {
        window.ManiacGames.showNotification('Недостаточно средств', 'error');
        return;
    }

    subBalance(state.betAmount);
    window.ManiacGames.updateBalance();

    const result = randomInt(1, 6);
    elements.resultText.textContent = '...';

    await rollDice(result);

    let isWin = false;
    let payoutMultiplier = 0;

    if (state.betType === 'even' && result % 2 === 0) {
        isWin = true;
        payoutMultiplier = PAYOUT_EVEN_ODD;
    } else if (state.betType === 'odd' && result % 2 !== 0) {
        isWin = true;
        payoutMultiplier = PAYOUT_EVEN_ODD;
    } else if (typeof state.betType === 'number' && state.betType === result) {
        isWin = true;
        payoutMultiplier = PAYOUT_EXACT;
    }

    if (isWin) {
        const payout = applyPayout(state.betAmount * payoutMultiplier);
        addBalance(payout);
        updateStats({ wins: 1, topWin: payout });
        elements.resultText.textContent = `Выигрыш +${payout} ⭐`;
        elements.resultText.style.color = 'var(--success)';
        window.ManiacGames.playSound('win');
        window.ManiacGames.hapticFeedback('success');
    } else {
        updateStats({ losses: 1 });
        elements.resultText.textContent = `Проигрыш -${state.betAmount} ⭐`;
        elements.resultText.style.color = 'var(--danger)';
        window.ManiacGames.hapticFeedback('error');
    }
    window.ManiacGames.updateBalance();
}

function bindEvents() {
    elements.betInput.addEventListener('change', e => {
        state.betAmount = parseInt(e.target.value, 10) || 10;
    });

    elements.betControls.addEventListener('click', e => {
        const button = e.target.closest('button');
        if (!button) return;

        const betType = button.dataset.bet;
        if (isNaN(betType)) {
            state.betType = betType;
        } else {
            state.betType = parseInt(betType, 10);
        }
        playGame();
    });
}


export function mount(rootEl) {
    root = rootEl;
    resetState();
    root.innerHTML = `
        <div id="dice3d-canvas-container"></div>
        <div class="card">
             <div id="dice-result" style="text-align:center; font-weight:bold; min-height: 1.2em; margin-bottom:15px;">Сделайте ставку</div>
             <input type="number" id="dice-bet-input" class="input-field" value="${state.betAmount}">
             <div id="dice-bet-controls" class="chip-controls" style="grid-template-columns: 1fr 1fr; margin-top:15px;">
                <button class="btn" data-bet="even">Чёт (x${PAYOUT_EVEN_ODD})</button>
                <button class="btn" data-bet="odd">Нечет (x${PAYOUT_EVEN_ODD})</button>
             </div>
             <div id="dice-exact-controls" class="chip-controls" style="grid-template-columns: repeat(3, 1fr);">
                <button class="btn chip" data-bet="1">1</button>
                <button class="btn chip" data-bet="2">2</button>
                <button class="btn chip" data-bet="3">3</button>
                <button class="btn chip" data-bet="4">4</button>
                <button class="btn chip" data-bet="5">5</button>
                <button class="btn chip" data-bet="6">6</button>
             </div>
             <p style="text-align:center; font-size:0.8rem; color: var(--muted); margin-top:10px;">Ставка на точное число (x${PAYOUT_EXACT})</p>
        </div>
    `;

    elements = {
        container: root.querySelector('#dice3d-canvas-container'),
        betInput: root.querySelector('#dice-bet-input'),
        betControls: root.querySelector('#dice-bet-controls'),
        exactControls: root.querySelector('#dice-exact-controls'),
        resultText: root.querySelector('#dice-result'),
    };

    // Also listen on exact controls
    elements.exactControls.addEventListener('click', elements.betControls.dispatchEvent.bind(elements.betControls));


    if (!initScene(elements.container)) {
        // WebGL failed, show fallback
        window.ManiacGames.showNotification('3D не поддерживается, открыта 2D версия', 'warning');
        window.location.hash = '#/dice';
        return;
    }

    bindEvents();
}

export function unmount() {
    if (animationFrameId) cancelAnimationFrame(animationFrameId);
    if(renderer) {
        renderer.dispose();
        const canvas = renderer.domElement;
        canvas.parentElement.removeChild(canvas);
    }
    root = null;
    renderer = scene = camera = composer = dice = null;
}
