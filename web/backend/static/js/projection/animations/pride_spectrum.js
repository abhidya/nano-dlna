// Pride Spectrum Animation
class PrideSpectrumAnimation extends BaseAnimation {
    setup() {
        this.colors = [
            '#e40303', // Red
            '#ff8c00', // Orange  
            '#ffed00', // Yellow
            '#008026', // Green
            '#004dff', // Blue
            '#750787'  // Purple
        ];
        
        this.waveOffset = 0;
        this.barCount = 20;
    }
    
    draw() {
        const ctx = this.ctx;
        
        // Clear canvas
        ctx.fillStyle = '#000000';
        ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Update wave
        this.waveOffset += 0.02;
        
        const barWidth = this.canvas.width / this.barCount;
        
        for (let i = 0; i < this.barCount; i++) {
            const x = i * barWidth;
            const colorIndex = Math.floor((i / this.barCount) * this.colors.length);
            const color = this.colors[colorIndex % this.colors.length];
            
            // Calculate wave height
            const waveHeight = Math.sin((i / this.barCount) * Math.PI * 2 + this.waveOffset) * 50 + 100;
            const barHeight = this.canvas.height * 0.5 + waveHeight;
            
            // Draw bar with gradient
            const gradient = ctx.createLinearGradient(0, this.canvas.height - barHeight, 0, this.canvas.height);
            gradient.addColorStop(0, color + '00');
            gradient.addColorStop(0.5, color + 'aa');
            gradient.addColorStop(1, color);
            
            ctx.fillStyle = gradient;
            ctx.fillRect(x, this.canvas.height - barHeight, barWidth + 1, barHeight);
        }
    }
    
    onDataUpdate() {
        // Adjust based on data
    }
}

// Animation is automatically registered by AnimationEngine