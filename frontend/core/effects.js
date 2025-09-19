/**
 * A simple confetti effect on a specified element.
 * @param {HTMLElement} targetElement - The element to overlay the confetti on.
 */
export function showConfetti(targetElement) {
    const canvas = document.createElement('canvas');
    canvas.id = 'confetti-canvas';
    const container = targetElement || document.body;
    // Make sure the container can house a positioned element
    if (getComputedStyle(container).position === 'static') {
        container.style.position = 'relative';
    }
    container.appendChild(canvas);

    const ctx = canvas.getContext('2d');
    canvas.width = container.clientWidth;
    canvas.height = container.clientHeight;

    const confettiCount = 150;
    const confetti = [];
    const colors = ['#f94144', '#f3722c', '#f8961e', '#f9c74f', '#90be6d', '#43aa8b', '#577590'];

    for (let i = 0; i < confettiCount; i++) {
        confetti.push({
            x: canvas.width / 2,
            y: canvas.height / 2,
            r: Math.random() * 5 + 2, // radius
            d: Math.random() * confettiCount, // density
            color: colors[Math.floor(Math.random() * colors.length)],
            tilt: Math.floor(Math.random() * 10) - 10,
            tiltAngleIncrement: Math.random() * 0.07 + 0.05,
            tiltAngle: 0,
            angle: Math.random() * 2 * Math.PI,
            speed: Math.random() * 4 + 2
        });
    }

    function draw() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        for (let i = 0; i < confetti.length; i++) {
            const c = confetti[i];
            ctx.beginPath();
            ctx.lineWidth = c.r / 2;
            ctx.strokeStyle = c.color;
            ctx.moveTo(c.x + c.tilt + c.r, c.y);
            ctx.lineTo(c.x + c.tilt, c.y + c.tilt + c.r);
            ctx.stroke();
        }
        update();
    }

    let frame = 0;
    function update() {
        for (let i = 0; i < confetti.length; i++) {
            const c = confetti[i];
            c.tiltAngle += c.tiltAngleIncrement;
            // Move confetti outwards from the center
            c.y += Math.cos(c.angle + c.d) * c.speed + 1;
            c.x += Math.sin(c.angle) * c.speed;
            c.tilt = Math.sin(c.tiltAngle - (i / 3)) * 15;

            if (c.y > canvas.height || c.x < -10 || c.x > canvas.width + 10) {
                 // Reset if it goes too far off-screen
                if (i % 5 === 0) { // Respawn only some
                    confetti[i] = { ...confetti[i], x: canvas.width/2, y: canvas.height/2, speed: Math.random() * 4 + 2 };
                }
            }
        }
        frame++;
        if (frame < 200) { // Run for a limited time
            requestAnimationFrame(draw);
        } else {
            canvas.remove();
        }
    }

    draw();
}

/**
 * Animates a number counting up or down inside an element.
 * @param {HTMLElement} element - The element whose textContent will be updated.
 * @param {number} start - The starting number.
 * @param {number} end - The final number.
 * @param {number} duration - The animation duration in milliseconds.
 */
export function animateBalance(element, start, end, duration = 1500) {
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        const current = Math.floor(progress * (end - start) + start);
        element.textContent = current.toLocaleString('en-US'); // Format with commas
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };
    window.requestAnimationFrame(step);
}
