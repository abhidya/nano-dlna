// Skillet Switch Animation
class SkilletSwitchAnimation extends BaseAnimation {
    setup() {
        this.switches = [];
        this.switchCount = 6;
        
        // Initialize switches
        for (let i = 0; i < this.switchCount; i++) {
            this.switches.push({
                state: Math.random() > 0.5,
                animProgress: 0,
                lastToggle: Date.now() + Math.random() * 3000
            });
        }
    }
    
    drawSwitch(ctx, x, y, size, switchObj) {
        const trackWidth = size;
        const trackHeight = size * 0.4;
        const handleRadius = trackHeight * 0.35;
        
        // Track background
        ctx.fillStyle = switchObj.state ? '#3498db' : '#34495e';
        ctx.beginPath();
        ctx.roundRect(x - trackWidth/2, y - trackHeight/2, trackWidth, trackHeight, trackHeight/2);
        ctx.fill();
        
        // Handle position
        let handleX;
        if (switchObj.animProgress > 0) {
            const progress = switchObj.animProgress;
            handleX = x - trackWidth/2 + handleRadius + (trackWidth - 2*handleRadius) * progress;
        } else {
            handleX = switchObj.state ? x + trackWidth/2 - handleRadius : x - trackWidth/2 + handleRadius;
        }
        
        // Handle
        ctx.fillStyle = '#ecf0f1';
        ctx.beginPath();
        ctx.arc(handleX, y, handleRadius, 0, Math.PI * 2);
        ctx.fill();
        
        // Handle highlight
        ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';
        ctx.beginPath();
        ctx.arc(handleX, y - handleRadius * 0.3, handleRadius * 0.3, 0, Math.PI * 2);
        ctx.fill();
    }
    
    draw() {
        const ctx = this.ctx;
        
        // Background
        ctx.fillStyle = '#2c3e50';
        ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Calculate layout
        const cols = Math.ceil(Math.sqrt(this.switchCount));
        const rows = Math.ceil(this.switchCount / cols);
        const cellWidth = this.canvas.width / cols;
        const cellHeight = this.canvas.height / rows;
        const switchSize = Math.min(cellWidth, cellHeight) * 0.5;
        
        // Update and draw switches
        const now = Date.now();
        let switchIndex = 0;
        
        for (let row = 0; row < rows && switchIndex < this.switchCount; row++) {
            for (let col = 0; col < cols && switchIndex < this.switchCount; col++) {
                const x = cellWidth * (col + 0.5);
                const y = cellHeight * (row + 0.5);
                const switchObj = this.switches[switchIndex];
                
                // Auto-toggle logic
                if (now - switchObj.lastToggle > 2000 + Math.random() * 3000) {
                    switchObj.state = !switchObj.state;
                    switchObj.lastToggle = now;
                    switchObj.animProgress = 0;
                }
                
                // Animate toggle
                if (switchObj.animProgress < 1) {
                    switchObj.animProgress += 0.05;
                }
                
                this.drawSwitch(ctx, x, y, switchSize, switchObj);
                switchIndex++;
            }
        }
    }
    
    onDataUpdate() {
        // Transit data could affect toggle speed
        if (this.data.transit && this.data.transit.activeRoutes) {
            // More active routes = faster switching
            const speedMultiplier = Math.min(this.data.transit.activeRoutes.length, 3);
            // Update toggle timing based on activity
        }
    }
}

// Animation is automatically registered by AnimationEngine