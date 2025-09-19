let canvas, ctx;

const particleColors = ["#C373F2", "#8A2BE2", "#FFFFFF", "#DDA0DD"];

function initParticleCanvas() {
    if (document.getElementById('particle-canvas')) return;

    canvas = document.createElement('canvas');
    canvas.id = 'particle-canvas';
    canvas.className = 'particles';
    document.getElementById('app').prepend(canvas);
    ctx = canvas.getContext('2d');

    const resizeCanvas = () => {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    };

    window.addEventListener('resize', resizeCanvas);
    resizeCanvas();
}


let particles = [];

class Particle {
    constructor(x, y) {
        this.x = x;
        this.y = y;
        this.size = Math.random() * 5 + 2; // size between 2 and 7
        this.speedX = Math.random() * 4 - 2; // -2 to 2
        this.speedY = Math.random() * 4 - 2; // -2 to 2
        this.color = particleColors[Math.floor(Math.random() * particleColors.length)];
        this.life = 1; // 100%
        this.decay = Math.random() * 0.04 + 0.01; // decay rate
    }

    update() {
        this.x += this.speedX;
        this.y += this.speedY;
        this.life -= this.decay;
        this.size *= 0.98; // shrink
    }

    draw() {
        ctx.globalAlpha = this.life;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fillStyle = this.color;
        ctx.fill();
        ctx.globalAlpha = 1;
    }
}

function animateParticles() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    for (let i = particles.length - 1; i >= 0; i--) {
        const p = particles[i];
        p.update();
        p.draw();
        if (p.life <= 0 || p.size <= 0.5) {
            particles.splice(i, 1);
        }
    }
    requestAnimationFrame(animateParticles);
}

export function createParticles(x, y, count = 10) {
    if (!ctx) return;
    for (let i = 0; i < count; i++) {
        particles.push(new Particle(x, y));
    }
}

// Ensure canvas is ready and animation loop starts
document.addEventListener('DOMContentLoaded', () => {
    initParticleCanvas();
    animateParticles();
});
