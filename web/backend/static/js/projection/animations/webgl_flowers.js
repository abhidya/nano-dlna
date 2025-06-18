// WebGL Flowers Animation - Adapted from https://codepen.io/ksenia-k/pen/poOMpzx
// Note: This uses Three.js loaded from CDN - ensure it's available in production
class WebGLFlowersAnimation extends BaseAnimation {
    setup() {
        // Load Three.js if not already loaded
        this.threeLoaded = false;
        this.THREE = null;
        
        // Animation parameters
        this.flowers = [];
        this.maxFlowers = 10;
        this.bloomInterval = 2000; // Bloom every 2 seconds base rate
        this.lastBloomTime = 0;
        
        // Data-driven parameters
        this.bloomFrequencyMultiplier = 1.0;
        this.flowerColorShift = 0;
        
        // Initialize Three.js scene
        this.loadThreeJS();
    }
    
    async loadThreeJS() {
        // Check if Three.js is already loaded
        if (window.THREE) {
            this.THREE = window.THREE;
            this.initThreeScene();
            return;
        }
        
        // Load Three.js dynamically
        try {
            const module = await import('https://cdn.skypack.dev/three@0.139.1/build/three.module');
            this.THREE = module;
            this.threeLoaded = true;
            this.initThreeScene();
        } catch (error) {
            console.error('Failed to load Three.js:', error);
            // Fallback to canvas-based flowers
            this.useFallbackRenderer = true;
        }
    }
    
    initThreeScene() {
        const THREE = this.THREE;
        
        // Check if we can create a WebGL context
        try {
            // Create offscreen canvas for WebGL
            this.webglCanvas = document.createElement('canvas');
            this.webglCanvas.width = this.canvas.width;
            this.webglCanvas.height = this.canvas.height;
            
            // Setup renderer with offscreen canvas
            this.renderer = new THREE.WebGLRenderer({
                canvas: this.webglCanvas,
                alpha: true,
                preserveDrawingBuffer: true,
                antialias: false,
                powerPreference: "low-power"
            });
            this.renderer.setPixelRatio(1); // Use lower pixel ratio to save resources
            this.renderer.setSize(this.canvas.width, this.canvas.height);
        
        // Setup scenes
        this.sceneShader = new THREE.Scene();
        this.sceneBasic = new THREE.Scene();
        this.camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 10);
        this.clock = new THREE.Clock();
        
        // Setup render targets for trail effect
        this.renderTargets = [
            new THREE.WebGLRenderTarget(this.canvas.width, this.canvas.height),
            new THREE.WebGLRenderTarget(this.canvas.width, this.canvas.height)
        ];
        
        // Create shaders
        this.createShaders();
        
        // Create plane for rendering
        this.createPlane();
        } catch (error) {
            console.warn('WebGL context creation failed, using fallback:', error);
            this.useFallbackRenderer = true;
        }
    }
    
    createShaders() {
        const THREE = this.THREE;
        
        // Vertex shader
        this.vertexShader = `
            varying vec2 vUv;
            void main() {
                vUv = uv;
                gl_Position = vec4(position, 1.);
            }
        `;
        
        // Fragment shader - adapted for autonomous flowers
        this.fragmentShader = `
            #define PI 3.14159265359
            
            uniform float u_ratio;
            uniform float u_time;
            uniform sampler2D u_texture;
            uniform int u_flower_count;
            uniform vec2 u_flowers[10]; // x,y positions
            uniform float u_flower_ages[10]; // age of each flower
            uniform vec2 u_flower_params[10]; // random parameters
            
            varying vec2 vUv;
            
            float rand(vec2 n) {
                return fract(sin(dot(n, vec2(12.9898, 4.1414))) * 43758.5453);
            }
            
            float noise(vec2 n) {
                const vec2 d = vec2(0., 1.);
                vec2 b = floor(n), f = smoothstep(vec2(0.), vec2(1.), fract(n));
                return mix(mix(rand(b), rand(b + d.yx), f.x), mix(rand(b + d.xy), rand(b + d.yy), f.x), f.y);
            }
            
            float flower_shape(vec2 _point, float _age, vec2 _params) {
                float random_by_uv = noise(vUv + _params);
                
                float petals_number = 5. + floor(_params[0] * 4.);
                float angle_offset = _params[1] * PI;
                float flower_angle = atan(_point.y, _point.x);
                float flower_sectoral_shape = abs(sin(flower_angle * .5 * petals_number + angle_offset)) + 0.5;
                
                float flower_size = mix(0.01, 0.08, _params[0]) * (1.0 + _age);
                float flower_radial_shape = length(_point) / flower_size;
                
                float flower_grow = min(_age * 2.0, 1.0);
                float flower_fade = 1.0 - smoothstep(3.0, 5.0, _age);
                
                float shape = 1. - smoothstep(0., flower_sectoral_shape, flower_radial_shape / flower_grow);
                return shape * flower_fade;
            }
            
            void main() {
                vec3 base = texture2D(u_texture, vUv).xyz * 0.95; // Slight fade for trail effect
                vec3 color = base;
                
                // Draw each flower
                for (int i = 0; i < 10; i++) {
                    if (i >= u_flower_count) break;
                    
                    vec2 flower_pos = u_flowers[i];
                    vec2 cursor = vUv - flower_pos;
                    cursor.x *= u_ratio;
                    
                    float shape = flower_shape(cursor, u_flower_ages[i], u_flower_params[i]);
                    
                    // Color based on parameters and age
                    vec3 flower_color = vec3(
                        0.7 + u_flower_params[i].y * 0.3,
                        0.3 + u_flower_params[i].x * 0.5,
                        0.8 + sin(u_flower_ages[i]) * 0.2
                    );
                    
                    color = mix(color, flower_color, shape);
                }
                
                color = clamp(color, vec3(0.0, 0.0, 0.1), vec3(1.0));
                gl_FragColor = vec4(color, 1.);
            }
        `;
    }
    
    createPlane() {
        const THREE = this.THREE;
        
        // Create shader material
        this.shaderMaterial = new THREE.ShaderMaterial({
            uniforms: {
                u_ratio: { value: this.canvas.width / this.canvas.height },
                u_time: { value: 0 },
                u_texture: { value: null },
                u_flower_count: { value: 0 },
                u_flowers: { value: new Array(10).fill(new THREE.Vector2(0, 0)) },
                u_flower_ages: { value: new Float32Array(10) },
                u_flower_params: { value: new Array(10).fill(new THREE.Vector2(0, 0)) }
            },
            vertexShader: this.vertexShader,
            fragmentShader: this.fragmentShader
        });
        
        this.basicMaterial = new THREE.MeshBasicMaterial();
        
        // Create plane geometry
        const planeGeometry = new THREE.PlaneGeometry(2, 2);
        const planeBasic = new THREE.Mesh(planeGeometry, this.basicMaterial);
        const planeShader = new THREE.Mesh(planeGeometry, this.shaderMaterial);
        
        this.sceneBasic.add(planeBasic);
        this.sceneShader.add(planeShader);
    }
    
    updateFlowers(deltaTime) {
        // Update existing flowers
        this.flowers = this.flowers.filter(flower => {
            flower.age += deltaTime;
            return flower.age < 5.0; // Flowers last 5 seconds
        });
        
        // Check if we should bloom a new flower
        const now = Date.now();
        const timeSinceLastBloom = now - this.lastBloomTime;
        const adjustedInterval = this.bloomInterval / this.bloomFrequencyMultiplier;
        
        if (timeSinceLastBloom > adjustedInterval && this.flowers.length < this.maxFlowers) {
            this.bloomFlower();
            this.lastBloomTime = now;
        }
    }
    
    bloomFlower() {
        const flower = {
            x: Math.random(),
            y: Math.random(),
            age: 0,
            params: {
                x: Math.random(),
                y: Math.random()
            }
        };
        this.flowers.push(flower);
    }
    
    draw() {
        if (this.useFallbackRenderer) {
            this.drawFallback();
            return;
        }
        
        if (!this.threeLoaded || !this.renderer) return;
        
        const deltaTime = this.clock.getDelta();
        
        // Update flowers
        this.updateFlowers(deltaTime);
        
        // Update uniforms
        this.shaderMaterial.uniforms.u_time.value += deltaTime;
        this.shaderMaterial.uniforms.u_texture.value = this.renderTargets[0].texture;
        this.shaderMaterial.uniforms.u_flower_count.value = this.flowers.length;
        
        // Update flower positions and ages
        const THREE = this.THREE;
        this.flowers.forEach((flower, i) => {
            this.shaderMaterial.uniforms.u_flowers.value[i] = new THREE.Vector2(flower.x, 1 - flower.y);
            this.shaderMaterial.uniforms.u_flower_ages.value[i] = flower.age;
            this.shaderMaterial.uniforms.u_flower_params.value[i] = new THREE.Vector2(flower.params.x, flower.params.y);
        });
        
        // Render to texture
        this.renderer.setRenderTarget(this.renderTargets[1]);
        this.renderer.render(this.sceneShader, this.camera);
        
        // Update basic material
        this.basicMaterial.map = this.renderTargets[1].texture;
        
        // Render to WebGL canvas
        this.renderer.setRenderTarget(null);
        this.renderer.render(this.sceneBasic, this.camera);
        
        // Copy WebGL canvas to main canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.ctx.drawImage(this.webglCanvas, 0, 0);
        
        // Swap render targets
        const tmp = this.renderTargets[0];
        this.renderTargets[0] = this.renderTargets[1];
        this.renderTargets[1] = tmp;
    }
    
    drawFallback() {
        // Fallback canvas-based rendering if Three.js fails to load
        this.ctx.fillStyle = 'rgba(0, 0, 0, 0.02)';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Update flowers
        const deltaTime = 0.016; // Assume 60fps
        this.updateFlowers(deltaTime);
        
        // Draw each flower
        this.flowers.forEach(flower => {
            const x = flower.x * this.canvas.width;
            const y = flower.y * this.canvas.height;
            const size = 20 + flower.params.x * 30;
            const petals = Math.floor(5 + flower.params.x * 4);
            const opacity = Math.min(1, flower.age) * (1 - flower.age / 5);
            
            this.ctx.save();
            this.ctx.translate(x, y);
            this.ctx.globalAlpha = opacity;
            
            // Draw petals
            for (let i = 0; i < petals; i++) {
                const angle = (i / petals) * Math.PI * 2;
                const petalX = Math.cos(angle) * size;
                const petalY = Math.sin(angle) * size;
                
                const gradient = this.ctx.createRadialGradient(petalX/2, petalY/2, 0, petalX/2, petalY/2, size);
                gradient.addColorStop(0, `hsla(${300 + flower.params.y * 60}, 70%, 60%, 1)`);
                gradient.addColorStop(1, `hsla(${300 + flower.params.y * 60}, 70%, 40%, 0)`);
                
                this.ctx.fillStyle = gradient;
                this.ctx.beginPath();
                this.ctx.arc(petalX/2, petalY/2, size * 0.6, 0, Math.PI * 2);
                this.ctx.fill();
            }
            
            // Draw center
            this.ctx.fillStyle = `hsla(60, 80%, 50%, ${opacity})`;
            this.ctx.beginPath();
            this.ctx.arc(0, 0, size * 0.3, 0, Math.PI * 2);
            this.ctx.fill();
            
            this.ctx.restore();
        });
    }
    
    onDataUpdate() {
        if (this.data.transit) {
            // Blooming frequency tied to train arrivals
            const minutes = parseInt(this.data.transit.nextArrival || '60');
            if (!isNaN(minutes)) {
                if (minutes < 5) {
                    this.bloomFrequencyMultiplier = 3.0; // Bloom frequently when train is near
                } else if (minutes < 10) {
                    this.bloomFrequencyMultiplier = 2.0;
                } else {
                    this.bloomFrequencyMultiplier = 1.0;
                }
            }
        }
        
        if (this.data.weather) {
            // Flower types vary by weather
            // This affects the color shift in the shader
            if (this.data.weather.conditions === 'rain') {
                this.flowerColorShift = 0.3; // Bluer flowers in rain
            } else if (this.data.weather.conditions === 'clear') {
                this.flowerColorShift = -0.3; // Warmer flowers in sun
            } else {
                this.flowerColorShift = 0;
            }
        }
    }
    
    stop() {
        // Clean up Three.js resources
        if (this.renderer) {
            this.renderer.dispose();
        }
        if (this.renderTargets) {
            this.renderTargets.forEach(rt => rt.dispose());
        }
        super.stop();
    }
}