// Spectrum Bars Animation - Pride spectrum visualization with transit data influence
class SpectrumBarsAnimation extends BaseAnimation {
    setup() {
        this.numBars = 50; // Match the CodePen number of bars
        this.bars = [];
        this.barWidth = 6; // Width of each bar in pixels
        this.maxHeight = 150; // Max height in pixels
        this.animationDuration = 600; // Duration in ms (0.6s from CodePen)
        this.transitData = null;
        
        // Generate spectrum colors (full hue rotation)
        const hueStep = 360 / this.numBars;
        
        // Initialize bars with staggered animation delays
        for (let i = 0; i < this.numBars; i++) {
            const hue = (i * hueStep) % 360;
            const delay = -524 * (i + 1); // Staggered delay like in CodePen
            
            this.bars.push({
                color: this.hslToHex(hue, 100, 50),
                animationOffset: delay,
                currentHeight: Math.random() * this.maxHeight,
                baseAmplitude: 1,
                transitAmplitude: 0
            });
        }
        
        this.startTime = Date.now();
        this.start();
    }
    
    hslToHex(h, s, l) {
        h = h / 360;
        s = s / 100;
        l = l / 100;
        
        let r, g, b;
        
        if (s === 0) {
            r = g = b = l;
        } else {
            const hue2rgb = (p, q, t) => {
                if (t < 0) t += 1;
                if (t > 1) t -= 1;
                if (t < 1/6) return p + (q - p) * 6 * t;
                if (t < 1/2) return q;
                if (t < 2/3) return p + (q - p) * (2/3 - t) * 6;
                return p;
            };
            
            const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
            const p = 2 * l - q;
            r = hue2rgb(p, q, h + 1/3);
            g = hue2rgb(p, q, h);
            b = hue2rgb(p, q, h - 1/3);
        }
        
        return '#' + [r, g, b].map(x => {
            const hex = Math.round(x * 255).toString(16);
            return hex.length === 1 ? '0' + hex : hex;
        }).join('');
    }
    
    draw() {
        const width = this.canvas.width;
        const height = this.canvas.height;
        const currentTime = Date.now() - this.startTime;
        
        // Calculate scale factors to fit the animation in the canvas
        const scaleX = width / (this.numBars * this.barWidth);
        const scaleY = height / this.maxHeight;
        
        // Clear canvas with black background
        this.ctx.fillStyle = 'black';
        this.ctx.fillRect(0, 0, width, height);
        
        // Draw each bar
        this.bars.forEach((bar, i) => {
            // Calculate animation phase with offset
            const animationTime = currentTime + bar.animationOffset;
            const phase = (animationTime % this.animationDuration) / this.animationDuration;
            
            // Alternate between 0 and maxHeight like the CSS animation
            let heightFactor;
            if (Math.floor(animationTime / this.animationDuration) % 2 === 0) {
                heightFactor = 1 - phase; // Going down
            } else {
                heightFactor = phase; // Going up
            }
            
            // Apply transit data influence
            const transitInfluence = bar.transitAmplitude * Math.sin(currentTime * 0.001 + i * 0.1);
            heightFactor = Math.max(0, Math.min(1, heightFactor + transitInfluence));
            
            // Calculate actual bar dimensions
            const barHeight = heightFactor * this.maxHeight * scaleY * bar.baseAmplitude;
            const x = i * this.barWidth * scaleX;
            const y = height - barHeight;
            const scaledBarWidth = this.barWidth * scaleX * 0.8; // 80% width with gaps
            
            // Draw bar with gradient
            const gradient = this.ctx.createLinearGradient(x, y, x, height);
            gradient.addColorStop(0, bar.color);
            gradient.addColorStop(0.5, bar.color + 'CC');
            gradient.addColorStop(1, bar.color + '33');
            
            this.ctx.fillStyle = gradient;
            this.ctx.fillRect(x + (this.barWidth * scaleX * 0.1), y, scaledBarWidth, barHeight);
            
            // Add glow effect for tall bars
            if (heightFactor > 0.7) {
                this.ctx.save();
                this.ctx.shadowColor = bar.color;
                this.ctx.shadowBlur = 10;
                this.ctx.fillStyle = bar.color;
                this.ctx.fillRect(x + (this.barWidth * scaleX * 0.1), y, scaledBarWidth, 2);
                this.ctx.restore();
            }
        });
    }
    
    onDataUpdate() {
        if (this.data.transit) {
            this.transitData = this.data.transit;
            
            // Adjust bar amplitudes based on transit activity
            if (this.transitData.activity !== undefined) {
                const activity = this.transitData.activity;
                
                // Create wave effect across bars based on activity
                this.bars.forEach((bar, i) => {
                    // Base amplitude increases with activity
                    bar.baseAmplitude = 0.7 + (activity * 0.3);
                    
                    // Transit amplitude for additional movement
                    bar.transitAmplitude = activity * 0.2 * Math.sin(i * 0.2);
                });
            }
            
            // Adjust animation speed based on changeRate
            if (this.transitData.changeRate !== undefined) {
                // Modify animation duration based on change rate
                this.animationDuration = 600 * (1 - this.transitData.changeRate * 0.5);
                this.animationDuration = Math.max(300, Math.min(1200, this.animationDuration));
            }
        }
    }
}

// Register the animation
if (typeof window.animationEngine !== 'undefined') {
    window.animationEngine.animationClasses.set('spectrum_bars', SpectrumBarsAnimation);
}