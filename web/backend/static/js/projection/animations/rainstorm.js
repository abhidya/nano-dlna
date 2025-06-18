// Rainstorm Animation
class RainstormAnimation extends BaseAnimation {
    setup() {
        this.raindrops = [];
        this.maxDrops = 100;
        this.windSpeed = 0;
    }
    
    createRaindrop() {
        return {
            x: Math.random() * this.canvas.width,
            y: -10,
            speed: 5 + Math.random() * 10,
            length: 10 + Math.random() * 20,
            opacity: 0.3 + Math.random() * 0.5
        };
    }
    
    draw() {
        const ctx = this.ctx;
        
        // Dark stormy background
        const gradient = ctx.createLinearGradient(0, 0, 0, this.canvas.height);
        gradient.addColorStop(0, '#1a1a2e');
        gradient.addColorStop(1, '#16213e');
        
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Add new raindrops
        if (this.raindrops.length < this.maxDrops && Math.random() < 0.3) {
            this.raindrops.push(this.createRaindrop());
        }
        
        // Update and draw raindrops
        ctx.strokeStyle = '#6699ff';
        ctx.lineWidth = 1;
        
        for (let i = this.raindrops.length - 1; i >= 0; i--) {
            const drop = this.raindrops[i];
            
            // Update position
            drop.y += drop.speed;
            drop.x += this.windSpeed;
            
            // Draw raindrop
            ctx.save();
            ctx.globalAlpha = drop.opacity;
            ctx.beginPath();
            ctx.moveTo(drop.x, drop.y);
            ctx.lineTo(drop.x + this.windSpeed, drop.y + drop.length);
            ctx.stroke();
            ctx.restore();
            
            // Remove if off screen
            if (drop.y > this.canvas.height) {
                this.raindrops.splice(i, 1);
            }
        }
        
        // Lightning effect occasionally
        if (Math.random() < 0.01) {
            ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';
            ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        }
    }
    
    onDataUpdate() {
        if (this.data.weather) {
            if (this.data.weather.windSpeed) {
                this.windSpeed = this.data.weather.windSpeed / 10;
            }
            if (this.data.weather.precipitation) {
                this.maxDrops = 50 + this.data.weather.precipitation * 10;
            }
        }
    }
}

// Animation is automatically registered by AnimationEngine