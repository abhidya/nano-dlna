// Pipes Flow Animation - Adapted from https://codepen.io/sinthetyc/pen/nKKBra
class PipesFlowAnimation extends BaseAnimation {
    setup() {
        this.twoPI = Math.PI * 2;
        this.pipes = [];
        
        // Define pipe colors (from original)
        this.pipeColors = [
            {r: 105, g: 210, b: 231}, // Light blue
            {r: 167, g: 219, b: 219}, // Pale blue
            {r: 224, g: 228, b: 204}, // Light green
            {r: 243, g: 134, b: 48},  // Orange
            {r: 250, g: 105, b: 0}    // Dark orange
        ];
        
        // Data-driven parameters
        this.speedMultiplier = 1.0;
        this.maxPipes = 5;
        
        // Initialize pipes
        for (let i = 0; i < this.maxPipes; i++) {
            this.pipes.push(this.createPipe(this.pipeColors[i % this.pipeColors.length]));
        }
        
        // Add clear prototype if not exists
        if (!CanvasRenderingContext2D.prototype.clear) {
            CanvasRenderingContext2D.prototype.clear = function() {
                this.save();
                this.clearRect(0, 0, this.canvas.width, this.canvas.height);
                this.restore();
            };
        }
    }
    
    createPipe(colour) {
        const pipe = {
            rad: 5,
            maxRad: 30,
            fill: null,
            colour: {...colour, a: 0},
            position: { x: 0, y: 0 },
            target: { x: 0, y: 0 },
            direction: {x: 1, y: 0},
            speed: 1
        };
        
        this.initializePipe(pipe);
        return pipe;
    }
    
    initializePipe(pipe) {
        pipe.rad = 5;
        pipe.position.x = Math.floor(Math.random() * this.canvas.width);
        pipe.position.y = Math.floor(Math.random() * this.canvas.height);
        
        do {
            pipe.target.x = pipe.position.x + Math.floor((Math.random() * 200) - 100);
        } while (pipe.target.x < pipe.rad || pipe.target.x > this.canvas.width - pipe.rad);
        
        pipe.target.y = pipe.position.y;
        pipe.direction.x = (pipe.position.x > pipe.target.x) ? -1 : 1;
        pipe.direction.y = 0;
        pipe.colour.a = 0;
    }
    
    movePipe(pipe) {
        pipe.position.x += pipe.direction.x * this.speedMultiplier;
        pipe.position.y += pipe.direction.y * this.speedMultiplier;
        
        // Check horizontal movement
        if ((pipe.direction.x > 0 && pipe.position.x > pipe.target.x) || 
            (pipe.direction.x < 0 && pipe.position.x < pipe.target.x)) {
            pipe.target.x = pipe.position.x;
            
            do {
                pipe.target.y = pipe.position.y + Math.floor((Math.random() * 200) - 100);
            } while (pipe.target.y < pipe.rad || pipe.target.y > this.canvas.height - pipe.rad);
            
            pipe.direction.x = 0;
            pipe.direction.y = pipe.position.y > pipe.target.y ? -1 : 1;
        }
        
        // Check vertical movement
        if ((pipe.direction.y > 0 && pipe.position.y > pipe.target.y) || 
            (pipe.direction.y < 0 && pipe.position.y < pipe.target.y)) {
            pipe.target.y = pipe.position.y;
            
            do {
                pipe.target.x = pipe.position.x + Math.floor((Math.random() * 200) - 100);
            } while (pipe.target.x < pipe.rad || pipe.target.x > this.canvas.width - pipe.rad);
            
            pipe.direction.y = 0;
            pipe.direction.x = pipe.position.x > pipe.target.x ? -1 : 1;
        }
        
        // Grow the pipe
        pipe.rad += 0.005;
        
        // Reset if too large
        if (pipe.rad > pipe.maxRad) {
            this.initializePipe(pipe);
            this.ctx.clear();
        }
        
        // Fade in
        if (pipe.colour.a < 1) {
            pipe.colour.a += 0.005;
        }
    }
    
    setFill(pipe) {
        const ctx = this.ctx;
        const halfRad = pipe.rad / 2;
        
        pipe.fill = ctx.createLinearGradient(
            pipe.position.x - halfRad,
            pipe.position.y - halfRad,
            pipe.position.x + halfRad,
            pipe.position.y + halfRad
        );
        
        const startColor = `rgba(${pipe.colour.r}, ${pipe.colour.g}, ${pipe.colour.b}, ${pipe.colour.a})`;
        const endColor = `rgba(${Math.floor(pipe.colour.r * 0.2)}, ${Math.floor(pipe.colour.g * 0.2)}, ${Math.floor(pipe.colour.b * 0.2)}, ${pipe.colour.a})`;
        
        pipe.fill.addColorStop(0, startColor);
        pipe.fill.addColorStop(1, endColor);
    }
    
    drawPipe(pipe) {
        const ctx = this.ctx;
        
        // Set the gradient fill
        this.setFill(pipe);
        ctx.fillStyle = pipe.fill;
        
        // Draw outer circle
        ctx.beginPath();
        ctx.arc(pipe.position.x, pipe.position.y, pipe.rad, 0, this.twoPI, true);
        ctx.closePath();
        ctx.fill();
        
        // Draw inner circle for hollow effect
        ctx.save();
        ctx.fillStyle = "rgba(0, 0, 0, 0.75)";
        ctx.beginPath();
        ctx.arc(pipe.position.x, pipe.position.y, pipe.rad - 2, 0, this.twoPI, true);
        ctx.closePath();
        ctx.fill();
        ctx.restore();
    }
    
    draw() {
        // Move and draw all pipes
        for (let pipe of this.pipes) {
            this.movePipe(pipe);
            this.drawPipe(pipe);
        }
    }
    
    onDataUpdate() {
        // Weather affects speed
        if (this.data.weather) {
            if (this.data.weather.windSpeed) {
                // Wind speed affects pipe movement speed
                this.speedMultiplier = 1 + (this.data.weather.windSpeed / 50);
                this.speedMultiplier = Math.max(0.5, Math.min(2, this.speedMultiplier));
            }
            
            if (this.data.weather.temperature) {
                // Temperature affects pipe colors slightly
                const tempEffect = (this.data.weather.temperature - 20) / 50;
                // Could modify pipe colors based on temperature
            }
        }
        
        // Transit data affects number of active pipes
        if (this.data.transit && this.data.transit.activeRoutes) {
            const targetPipes = Math.min(this.data.transit.activeRoutes.length, 8);
            
            // Add or remove pipes based on transit activity
            while (this.pipes.length < targetPipes && this.pipes.length < 8) {
                const colorIndex = this.pipes.length % this.pipeColors.length;
                this.pipes.push(this.createPipe(this.pipeColors[colorIndex]));
            }
            
            while (this.pipes.length > targetPipes && this.pipes.length > 2) {
                this.pipes.pop();
            }
        }
    }
}

// Animation is automatically registered by AnimationEngine