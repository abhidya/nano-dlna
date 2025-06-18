// 7-Segment Clock Animation - Adapted from https://codepen.io/VicioBonura/pen/YzbppKJ
class SegmentClockAnimation extends BaseAnimation {
    setup() {
        // CSS for 7-segment display
        this.segmentMap = {
            '0': [1, 1, 1, 0, 1, 1, 1],
            '1': [0, 0, 1, 0, 0, 1, 0],
            '2': [1, 0, 1, 1, 1, 0, 1],
            '3': [1, 0, 1, 1, 0, 1, 1],
            '4': [0, 1, 1, 1, 0, 1, 0],
            '5': [1, 1, 0, 1, 0, 1, 1],
            '6': [1, 1, 0, 1, 1, 1, 1],
            '7': [1, 0, 1, 0, 0, 1, 0],
            '8': [1, 1, 1, 1, 1, 1, 1],
            '9': [1, 1, 1, 1, 0, 1, 1]
        };
        
        this.segmentColor = '#00ff00';
        this.offColor = '#003300';
        this.backgroundColor = '#000000';
    }
    
    drawSegment(ctx, x, y, width, height, horizontal, active) {
        ctx.fillStyle = active ? this.segmentColor : this.offColor;
        ctx.beginPath();
        
        if (horizontal) {
            ctx.moveTo(x + 5, y);
            ctx.lineTo(x + width - 5, y);
            ctx.lineTo(x + width, y + height/2);
            ctx.lineTo(x + width - 5, y + height);
            ctx.lineTo(x + 5, y + height);
            ctx.lineTo(x, y + height/2);
        } else {
            ctx.moveTo(x, y + 5);
            ctx.lineTo(x + width/2, y);
            ctx.lineTo(x + width, y + 5);
            ctx.lineTo(x + width, y + height - 5);
            ctx.lineTo(x + width/2, y + height);
            ctx.lineTo(x, y + height - 5);
        }
        
        ctx.closePath();
        ctx.fill();
    }
    
    drawDigit(ctx, digit, x, y, size) {
        const segments = this.segmentMap[digit];
        const thickness = size * 0.15;
        
        // Top
        this.drawSegment(ctx, x + thickness, y, size - 2*thickness, thickness, true, segments[0]);
        
        // Top right
        this.drawSegment(ctx, x + size - thickness, y + thickness, thickness, size/2 - 1.5*thickness, false, segments[2]);
        
        // Bottom right
        this.drawSegment(ctx, x + size - thickness, y + size/2 + 0.5*thickness, thickness, size/2 - 1.5*thickness, false, segments[5]);
        
        // Bottom
        this.drawSegment(ctx, x + thickness, y + size - thickness, size - 2*thickness, thickness, true, segments[6]);
        
        // Bottom left
        this.drawSegment(ctx, x, y + size/2 + 0.5*thickness, thickness, size/2 - 1.5*thickness, false, segments[4]);
        
        // Top left
        this.drawSegment(ctx, x, y + thickness, thickness, size/2 - 1.5*thickness, false, segments[1]);
        
        // Middle
        this.drawSegment(ctx, x + thickness, y + size/2 - thickness/2, size - 2*thickness, thickness, true, segments[3]);
    }
    
    draw() {
        const ctx = this.ctx;
        
        // Clear background
        ctx.fillStyle = this.backgroundColor;
        ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Get current time
        const d = new Date();
        const time = {
            h: ("0" + d.getHours()).slice(-2),
            m: ("0" + d.getMinutes()).slice(-2),
            s: ("0" + d.getSeconds()).slice(-2),
            ms: ("0" + d.getMilliseconds()).slice(-3)
        };
        
        // Calculate digit size based on canvas size
        const digitSize = Math.min(this.canvas.width / 8, this.canvas.height / 2);
        const spacing = digitSize * 0.3;
        const colonWidth = digitSize * 0.2;
        
        // Calculate starting position
        const totalWidth = 6 * digitSize + 5 * spacing + 2 * colonWidth;
        let x = (this.canvas.width - totalWidth) / 2;
        const y = (this.canvas.height - digitSize) / 2;
        
        // Draw hours
        this.drawDigit(ctx, time.h[0], x, y, digitSize);
        x += digitSize + spacing;
        this.drawDigit(ctx, time.h[1], x, y, digitSize);
        x += digitSize + spacing;
        
        // Draw colon
        ctx.fillStyle = this.segmentColor;
        ctx.beginPath();
        ctx.arc(x + colonWidth/2, y + digitSize * 0.3, digitSize * 0.05, 0, Math.PI * 2);
        ctx.fill();
        ctx.beginPath();
        ctx.arc(x + colonWidth/2, y + digitSize * 0.7, digitSize * 0.05, 0, Math.PI * 2);
        ctx.fill();
        x += colonWidth + spacing;
        
        // Draw minutes
        this.drawDigit(ctx, time.m[0], x, y, digitSize);
        x += digitSize + spacing;
        this.drawDigit(ctx, time.m[1], x, y, digitSize);
        x += digitSize + spacing;
        
        // Draw second colon
        const blinkOn = d.getMilliseconds() < 500;
        if (blinkOn) {
            ctx.fillStyle = this.segmentColor;
            ctx.beginPath();
            ctx.arc(x + colonWidth/2, y + digitSize * 0.3, digitSize * 0.05, 0, Math.PI * 2);
            ctx.fill();
            ctx.beginPath();
            ctx.arc(x + colonWidth/2, y + digitSize * 0.7, digitSize * 0.05, 0, Math.PI * 2);
            ctx.fill();
        }
        x += colonWidth + spacing;
        
        // Draw seconds
        this.drawDigit(ctx, time.s[0], x, y, digitSize);
        x += digitSize + spacing;
        this.drawDigit(ctx, time.s[1], x, y, digitSize);
        
        // Weather-based color changes
        if (this.data.weather && this.data.weather.temperature) {
            const temp = this.data.weather.temperature;
            if (temp > 30) {
                this.segmentColor = '#ff0000';
                this.offColor = '#330000';
            } else if (temp > 20) {
                this.segmentColor = '#ffaa00';
                this.offColor = '#332200';
            } else if (temp > 10) {
                this.segmentColor = '#00ff00';
                this.offColor = '#003300';
            } else {
                this.segmentColor = '#00aaff';
                this.offColor = '#002233';
            }
        }
    }
    
    onDataUpdate() {
        // Color changes handled in draw method
    }
}

// Animation is automatically registered by AnimationEngine