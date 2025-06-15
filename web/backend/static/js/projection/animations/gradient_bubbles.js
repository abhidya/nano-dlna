// Gradient Bubbles Animation - Adapted from https://codepen.io/Hyperplexed/pen/MWXBRBp
// Autonomous version with data-driven movement instead of mouse tracking
class GradientBubblesAnimation extends BaseAnimation {
    setup() {
        // Create gradient background elements
        this.createGradientElements();
        
        // Animation parameters
        this.interactivePosition = { x: 0.5, y: 0.5 };
        this.targetPosition = { x: 0.5, y: 0.5 };
        this.movementSpeed = 0.02;
        this.wanderRadius = 0.3;
        this.lastDirectionChange = 0;
        this.directionChangeInterval = 3000; // Change direction every 3 seconds
        
        // Data-driven parameters
        this.speedMultiplier = 1.0;
        this.colorShift = 0;
    }
    
    createGradientElements() {
        // Create wrapper div
        this.wrapper = document.createElement('div');
        this.wrapper.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            overflow: hidden;
        `;
        
        // Inject CSS styles
        const style = document.createElement('style');
        style.textContent = `
            @import url('https://fonts.googleapis.com/css?family=Montserrat:400,700');
            
            .gradient-bg-canvas {
                width: 100%;
                height: 100%;
                position: relative;
                overflow: hidden;
                background: linear-gradient(40deg, rgb(8, 10, 15), rgb(0, 17, 32));
                top: 0;
                left: 0;
            }
            
            .gradient-bg-canvas .noiseBg {
                position: absolute;
                width: 100%;
                height: 100%;
                top: 0;
                left: 0;
                z-index: 1;
                mix-blend-mode: soft-light;
                opacity: 0.3;
            }
            
            .gradient-bg-canvas .gradients-container {
                filter: url(#goo) blur(40px);
                width: 100%;
                height: 100%;
            }
            
            .gradient-bg-canvas .g1,
            .gradient-bg-canvas .g2,
            .gradient-bg-canvas .g3,
            .gradient-bg-canvas .g4,
            .gradient-bg-canvas .g5 {
                position: absolute;
                mix-blend-mode: hard-light;
                width: 80%;
                height: 80%;
                top: calc(50% - 40%);
                left: calc(50% - 40%);
                opacity: 1;
            }
            
            .gradient-bg-canvas .g1 {
                background: radial-gradient(circle at center, rgba(18, 113, 255, 0.8) 0, rgba(18, 113, 255, 0) 50%) no-repeat;
                transform-origin: center center;
                animation: moveVertical 30s ease infinite;
            }
            
            .gradient-bg-canvas .g2 {
                background: radial-gradient(circle at center, rgba(107, 74, 255, 0.8) 0, rgba(107, 74, 255, 0) 50%) no-repeat;
                transform-origin: calc(50% - 400px);
                animation: moveInCircle 20s reverse infinite;
            }
            
            .gradient-bg-canvas .g3 {
                background: radial-gradient(circle at center, rgba(100, 100, 255, 0.8) 0, rgba(100, 100, 255, 0) 50%) no-repeat;
                top: calc(50% - 40% + 200px);
                left: calc(50% - 40% - 500px);
                transform-origin: calc(50% + 400px);
                animation: moveInCircle 40s linear infinite;
            }
            
            .gradient-bg-canvas .g4 {
                background: radial-gradient(circle at center, rgba(50, 160, 220, 0.8) 0, rgba(50, 160, 220, 0) 50%) no-repeat;
                transform-origin: calc(50% - 200px);
                animation: moveHorizontal 40s ease infinite;
                opacity: 0.7;
            }
            
            .gradient-bg-canvas .g5 {
                background: radial-gradient(circle at center, rgba(80, 47, 122, 0.8) 0, rgba(80, 47, 122, 0) 50%) no-repeat;
                width: 160%;
                height: 160%;
                top: calc(50% - 80%);
                left: calc(50% - 80%);
                transform-origin: calc(50% - 800px) calc(50% + 200px);
                animation: moveInCircle 20s ease infinite;
            }
            
            .gradient-bg-canvas .interactive {
                position: absolute;
                background: radial-gradient(circle at center, rgba(140, 100, 255, 0.8) 0, rgba(140, 100, 255, 0) 50%) no-repeat;
                mix-blend-mode: hard-light;
                width: 100%;
                height: 100%;
                top: -50%;
                left: -50%;
                opacity: 0.7;
                transition: none;
            }
            
            @keyframes moveInCircle {
                from { transform: rotate(0deg); }
                to { transform: rotate(360deg); }
            }
            
            @keyframes moveVertical {
                0% { transform: translateY(-50%); }
                50% { transform: translateY(50%); }
                100% { transform: translateY(-50%); }
            }
            
            @keyframes moveHorizontal {
                0% { transform: translateX(-50%) translateY(-10%); }
                50% { transform: translateX(50%) translateY(10%); }
                100% { transform: translateX(-50%) translateY(-10%); }
            }
        `;
        document.head.appendChild(style);
        
        // Create gradient background HTML
        this.wrapper.innerHTML = `
            <div class="gradient-bg-canvas">
                <svg viewBox="0 0 100vw 100vw" xmlns="http://www.w3.org/2000/svg" class="noiseBg">
                    <filter id="noiseFilterBg">
                        <feTurbulence type="fractalNoise" baseFrequency="0.6" stitchTiles="stitch" />
                    </filter>
                    <rect width="100%" height="100%" preserveAspectRatio="xMidYMid meet" filter="url(#noiseFilterBg)" />
                </svg>
                <svg xmlns="http://www.w3.org/2000/svg" style="display: none;">
                    <defs>
                        <filter id="goo">
                            <feGaussianBlur in="SourceGraphic" stdDeviation="10" result="blur" />
                            <feColorMatrix in="blur" mode="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 18 -8" result="goo" />
                            <feBlend in="SourceGraphic" in2="goo" />
                        </filter>
                    </defs>
                </svg>
                <div class="gradients-container">
                    <div class="g1"></div>
                    <div class="g2"></div>
                    <div class="g3"></div>
                    <div class="g4"></div>
                    <div class="g5"></div>
                    <div class="interactive"></div>
                </div>
            </div>
        `;
        
        // Append to canvas parent
        this.canvas.parentElement.appendChild(this.wrapper);
        
        // Get interactive element reference
        this.interactiveElement = this.wrapper.querySelector('.interactive');
    }
    
    updateTargetPosition() {
        const now = Date.now();
        
        // Change direction periodically
        if (now - this.lastDirectionChange > this.directionChangeInterval) {
            // Generate new target within wander radius
            const angle = Math.random() * Math.PI * 2;
            const radius = Math.random() * this.wanderRadius;
            
            this.targetPosition = {
                x: 0.5 + Math.cos(angle) * radius,
                y: 0.5 + Math.sin(angle) * radius
            };
            
            this.lastDirectionChange = now;
        }
    }
    
    draw() {
        // Clear canvas (not used for this CSS-based animation)
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Update target position
        this.updateTargetPosition();
        
        // Smoothly move towards target
        const dx = this.targetPosition.x - this.interactivePosition.x;
        const dy = this.targetPosition.y - this.interactivePosition.y;
        
        this.interactivePosition.x += dx * this.movementSpeed * this.speedMultiplier;
        this.interactivePosition.y += dy * this.movementSpeed * this.speedMultiplier;
        
        // Apply position to interactive element
        if (this.interactiveElement) {
            const x = (this.interactivePosition.x - 0.5) * this.canvas.width;
            const y = (this.interactivePosition.y - 0.5) * this.canvas.height;
            
            this.interactiveElement.style.transform = `translate(${x}px, ${y}px)`;
        }
        
        // Apply color shift based on data
        if (this.colorShift !== 0) {
            const hueRotate = this.colorShift * 30; // Max 30 degree hue rotation
            this.wrapper.style.filter = `hue-rotate(${hueRotate}deg)`;
        }
    }
    
    onDataUpdate() {
        if (this.data.weather) {
            // Movement speed based on wind
            const windSpeed = this.data.weather.wind_speed || 0;
            this.speedMultiplier = 1.0 + (windSpeed / 20); // Faster movement with wind
            
            // Color shift based on temperature
            const temp = this.data.weather.temperature || 20;
            if (temp < 10) {
                this.colorShift = 0.5; // Cooler colors
            } else if (temp > 25) {
                this.colorShift = -0.5; // Warmer colors
            } else {
                this.colorShift = 0;
            }
        }
        
        if (this.data.transit) {
            // More erratic movement when trains are near
            const minutes = parseInt(this.data.transit.nextArrival || '60');
            if (!isNaN(minutes) && minutes < 5) {
                this.directionChangeInterval = 1000; // Change direction more frequently
                this.wanderRadius = 0.5; // Larger movement radius
            } else {
                this.directionChangeInterval = 3000;
                this.wanderRadius = 0.3;
            }
        }
    }
    
    stop() {
        // Clean up DOM elements
        if (this.wrapper && this.wrapper.parentElement) {
            this.wrapper.parentElement.removeChild(this.wrapper);
        }
        super.stop();
    }
}