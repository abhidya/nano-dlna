// Milk Physics Animation - Adapted from https://codepen.io/rudtjd2548/pen/mdjWjaP
class MilkPhysicsAnimation extends BaseAnimation {
    setup() {
        this.particles = [];
        this.maxParticles = 100;
        this.gravity = 0.3;
        this.bounce = 0.7;
        this.friction = 0.99;
        
        // Spawn points (will be randomized within mask)
        this.spawnPoints = [];
        this.lastSpawnTime = 0;
        this.spawnInterval = 50; // milliseconds
        
        // Glass/container simulation
        this.containers = [];
        this.containerCount = 3;
        
        // Data-driven parameters
        this.flowRate = 1.0;
        this.viscosity = 1.0;
        
        // Initialize spawn points and containers
        this.initializeSpawnPoints();
        this.initializeContainers();
    }
    
    initializeSpawnPoints() {
        // Create 3-5 spawn points distributed across the top of the canvas
        const spawnCount = 3 + Math.floor(Math.random() * 3);
        for (let i = 0; i < spawnCount; i++) {
            this.spawnPoints.push({
                x: (this.canvas.width / (spawnCount + 1)) * (i + 1),
                y: 20,
                active: true
            });
        }
    }
    
    initializeContainers() {
        // Create invisible containers at different positions
        for (let i = 0; i < this.containerCount; i++) {
            const container = {
                x: (this.canvas.width / (this.containerCount + 1)) * (i + 1),
                y: this.canvas.height * 0.7,
                width: 80,
                height: 100,
                angle: (Math.random() - 0.5) * 0.3 // Slight random tilt
            };
            this.containers.push(container);
        }
    }
    
    createParticle(spawnPoint) {
        if (this.particles.length >= this.maxParticles) return;
        
        const particle = {
            x: spawnPoint.x + (Math.random() - 0.5) * 10,
            y: spawnPoint.y,
            vx: (Math.random() - 0.5) * 2,
            vy: Math.random() * 2,
            radius: 4 + Math.random() * 4,
            life: 1.0,
            stuck: false
        };
        
        this.particles.push(particle);
    }
    
    updateParticle(particle, index) {
        if (!particle.stuck) {
            // Apply gravity
            particle.vy += this.gravity * this.viscosity;
            
            // Apply friction
            particle.vx *= this.friction;
            particle.vy *= this.friction;
            
            // Update position
            particle.x += particle.vx;
            particle.y += particle.vy;
            
            // Check container collisions
            for (let container of this.containers) {
                if (this.checkContainerCollision(particle, container)) {
                    this.handleContainerCollision(particle, container);
                }
            }
            
            // Check boundaries
            if (particle.x - particle.radius < 0 || particle.x + particle.radius > this.canvas.width) {
                particle.vx *= -this.bounce;
                particle.x = Math.max(particle.radius, Math.min(this.canvas.width - particle.radius, particle.x));
            }
            
            if (particle.y + particle.radius > this.canvas.height) {
                particle.vy *= -this.bounce;
                particle.y = this.canvas.height - particle.radius;
                
                // Reduce velocity to simulate liquid settling
                if (Math.abs(particle.vy) < 0.5) {
                    particle.vy = 0;
                    particle.vx *= 0.9;
                }
            }
            
            // Particle-to-particle collision (simplified)
            for (let other of this.particles) {
                if (other !== particle) {
                    const dx = other.x - particle.x;
                    const dy = other.y - particle.y;
                    const distance = Math.sqrt(dx * dx + dy * dy);
                    const minDistance = particle.radius + other.radius;
                    
                    if (distance < minDistance) {
                        // Push particles apart
                        const angle = Math.atan2(dy, dx);
                        const overlap = minDistance - distance;
                        
                        particle.x -= Math.cos(angle) * overlap * 0.5;
                        particle.y -= Math.sin(angle) * overlap * 0.5;
                        other.x += Math.cos(angle) * overlap * 0.5;
                        other.y += Math.sin(angle) * overlap * 0.5;
                        
                        // Exchange velocities (simplified)
                        const tempVx = particle.vx;
                        const tempVy = particle.vy;
                        particle.vx = other.vx * 0.8;
                        particle.vy = other.vy * 0.8;
                        other.vx = tempVx * 0.8;
                        other.vy = tempVy * 0.8;
                    }
                }
            }
        }
        
        // Age particle
        particle.life -= 0.002;
        
        // Remove old particles
        if (particle.life <= 0 || particle.y > this.canvas.height + particle.radius) {
            this.particles.splice(index, 1);
        }
    }
    
    checkContainerCollision(particle, container) {
        // Simple rectangular collision (could be improved with rotation)
        const left = container.x - container.width / 2;
        const right = container.x + container.width / 2;
        const top = container.y - container.height / 2;
        const bottom = container.y + container.height / 2;
        
        return particle.x + particle.radius > left &&
               particle.x - particle.radius < right &&
               particle.y + particle.radius > top &&
               particle.y - particle.radius < bottom;
    }
    
    handleContainerCollision(particle, container) {
        // Simplified container collision
        const left = container.x - container.width / 2;
        const right = container.x + container.width / 2;
        const top = container.y - container.height / 2;
        
        // Check which side of container was hit
        if (particle.y < top + 20) {
            // Hit from top - bounce or contain
            if (Math.abs(particle.vx) < 0.5 && Math.abs(particle.vy) < 0.5) {
                particle.stuck = true;
            } else {
                particle.vy *= -this.bounce * 0.5;
                particle.y = top - particle.radius;
            }
        } else {
            // Hit from side
            if (particle.x < container.x) {
                particle.vx = -Math.abs(particle.vx) * this.bounce;
                particle.x = left - particle.radius;
            } else {
                particle.vx = Math.abs(particle.vx) * this.bounce;
                particle.x = right + particle.radius;
            }
        }
    }
    
    draw(timestamp) {
        const ctx = this.ctx;
        
        // Clear canvas
        ctx.fillStyle = 'rgba(0, 0, 0, 0.1)';
        ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Spawn new particles
        if (timestamp - this.lastSpawnTime > this.spawnInterval / this.flowRate) {
            for (let spawnPoint of this.spawnPoints) {
                if (spawnPoint.active && Math.random() < 0.7) {
                    this.createParticle(spawnPoint);
                }
            }
            this.lastSpawnTime = timestamp;
        }
        
        // Update and draw particles
        for (let i = this.particles.length - 1; i >= 0; i--) {
            this.updateParticle(this.particles[i], i);
        }
        
        // Apply gooey effect using multiple passes
        // First pass - draw all particles with blur
        ctx.save();
        ctx.filter = 'blur(8px)';
        ctx.globalCompositeOperation = 'screen';
        
        for (let particle of this.particles) {
            const gradient = ctx.createRadialGradient(
                particle.x, particle.y, 0,
                particle.x, particle.y, particle.radius * 2
            );
            gradient.addColorStop(0, `rgba(255, 255, 255, ${particle.life})`);
            gradient.addColorStop(1, 'rgba(255, 255, 255, 0)');
            
            ctx.fillStyle = gradient;
            ctx.beginPath();
            ctx.arc(particle.x, particle.y, particle.radius * 2, 0, Math.PI * 2);
            ctx.fill();
        }
        
        ctx.restore();
        
        // Second pass - draw sharp particles
        ctx.globalCompositeOperation = 'source-over';
        for (let particle of this.particles) {
            ctx.fillStyle = `rgba(255, 255, 255, ${particle.life * 0.9})`;
            ctx.beginPath();
            ctx.arc(particle.x, particle.y, particle.radius, 0, Math.PI * 2);
            ctx.fill();
        }
        
        // Debug: Draw containers (invisible in production)
        if (false) { // Set to true for debugging
            ctx.strokeStyle = 'rgba(255, 0, 0, 0.3)';
            ctx.lineWidth = 2;
            for (let container of this.containers) {
                ctx.save();
                ctx.translate(container.x, container.y);
                ctx.rotate(container.angle);
                ctx.strokeRect(
                    -container.width / 2,
                    -container.height / 2,
                    container.width,
                    container.height
                );
                ctx.restore();
            }
        }
    }
    
    onDataUpdate() {
        // Weather affects viscosity
        if (this.data.weather) {
            if (this.data.weather.temperature) {
                // Higher temperature = lower viscosity
                this.viscosity = 1.5 - (this.data.weather.temperature / 50);
                this.viscosity = Math.max(0.5, Math.min(1.5, this.viscosity));
            }
            
            if (this.data.weather.humidity) {
                // Higher humidity = more particles
                this.flowRate = 0.5 + (this.data.weather.humidity / 100);
            }
        }
        
        // Transit data affects spawn points
        if (this.data.transit && this.data.transit.activeRoutes) {
            // Activate/deactivate spawn points based on transit activity
            const activeCount = Math.min(this.data.transit.activeRoutes.length, this.spawnPoints.length);
            for (let i = 0; i < this.spawnPoints.length; i++) {
                this.spawnPoints[i].active = i < activeCount;
            }
        }
    }
}

// Animation is automatically registered by AnimationEngine