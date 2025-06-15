// CodePen Animation Adapter
// This system transforms CodePen animations into autonomous BaseAnimation classes

class CodePenAdapter {
    constructor() {
        this.adaptations = {
            // Map of CodePen IDs to their adaptation strategies
            'vYwgrWv': this.adaptNeuralNoise,
            'poOMpzx': this.adaptWebGLFlowers,
            'oNOKYqr': this.adaptInteractiveGradients,
            'mdjWjaP': this.adaptMilkPhysics,
            'bNGExzZ': this.adaptRainstorm,
            'YzbppKJ': this.adapt7SegmentClock,
            'NWeqOVw': this.adaptMovingClouds,
            'MKEpqW': this.adaptPrideSpectrum,
            'nKKBra': this.adaptPipesAnimation,
            'rNqxNXW': this.adaptSkilletSwitch
        };
    }
    
    // Extract code from CodePen page HTML
    extractCode(html) {
        const result = {
            html: '',
            css: '',
            js: ''
        };
        
        // Extract HTML
        const htmlMatch = html.match(/id="html".*?<code>([\s\S]*?)<\/code>/);
        if (htmlMatch) {
            result.html = this.decodeHTML(htmlMatch[1]);
        }
        
        // Extract CSS
        const cssMatch = html.match(/id="css".*?<code>([\s\S]*?)<\/code>/);
        if (cssMatch) {
            result.css = this.decodeHTML(cssMatch[1]);
        }
        
        // Extract JavaScript
        const jsMatch = html.match(/id="js".*?<code>([\s\S]*?)<\/code>/);
        if (jsMatch) {
            result.js = this.decodeHTML(jsMatch[1]);
        }
        
        return result;
    }
    
    decodeHTML(str) {
        return str
            .replace(/<[^>]*>/g, '')
            .replace(/&quot;/g, '"')
            .replace(/&lt;/g, '<')
            .replace(/&gt;/g, '>')
            .replace(/&amp;/g, '&')
            .trim();
    }
    
    // Neural Noise adaptation
    adaptNeuralNoise(code) {
        // Already implemented - see neural_noise.js
        return {
            className: 'NeuralNoiseAnimation',
            dependencies: ['webgl'],
            dataInputs: ['weather']
        };
    }
    
    // WebGL Flowers adaptation
    adaptWebGLFlowers(code) {
        return {
            className: 'WebGLFlowersAnimation',
            setup: `
                // Flower parameters
                this.flowers = [];
                this.maxFlowers = 20;
                this.bloomFrequency = 0.02; // Base bloom rate
                
                // Data-driven parameters
                this.bloomMultiplier = 1.0;
                this.flowerTypes = ['rose', 'daisy', 'tulip', 'sunflower'];
                this.currentFlowerType = 0;
            `,
            methods: {
                createFlower: `
                    const flower = {
                        x: Math.random(),
                        y: Math.random(),
                        scale: 0,
                        targetScale: 0.5 + Math.random() * 0.5,
                        rotation: Math.random() * Math.PI * 2,
                        type: this.flowerTypes[this.currentFlowerType],
                        age: 0,
                        maxAge: 5000 + Math.random() * 5000
                    };
                    this.flowers.push(flower);
                    this.currentFlowerType = (this.currentFlowerType + 1) % this.flowerTypes.length;
                `,
                updateFlowers: `
                    // Random blooming
                    if (Math.random() < this.bloomFrequency * this.bloomMultiplier && 
                        this.flowers.length < this.maxFlowers) {
                        this.createFlower();
                    }
                    
                    // Update existing flowers
                    this.flowers = this.flowers.filter(flower => {
                        flower.age += 16;
                        
                        // Growth animation
                        if (flower.scale < flower.targetScale) {
                            flower.scale += 0.01;
                        }
                        
                        // Wilt animation
                        if (flower.age > flower.maxAge - 1000) {
                            flower.scale *= 0.95;
                        }
                        
                        return flower.age < flower.maxAge;
                    });
                `
            },
            dataInputs: ['weather', 'transit']
        };
    }
    
    // Generate BaseAnimation class from adaptation
    generateClass(adaptationResult) {
        const { className, setup, methods, draw, dataInputs } = adaptationResult;
        
        let classCode = `// ${className} - Auto-adapted from CodePen\n`;
        classCode += `class ${className} extends BaseAnimation {\n`;
        
        if (setup) {
            classCode += `    setup() {\n${setup}\n    }\n\n`;
        }
        
        if (methods) {
            for (const [name, code] of Object.entries(methods)) {
                classCode += `    ${name}() {\n${code}\n    }\n\n`;
            }
        }
        
        if (draw) {
            classCode += `    draw() {\n${draw}\n    }\n\n`;
        }
        
        classCode += `    onDataUpdate() {\n`;
        if (dataInputs.includes('weather')) {
            classCode += `        if (this.data.weather) {\n`;
            classCode += `            // Adapt animation based on weather\n`;
            classCode += `        }\n`;
        }
        if (dataInputs.includes('transit')) {
            classCode += `        if (this.data.transit) {\n`;
            classCode += `            // Adapt animation based on transit\n`;
            classCode += `        }\n`;
        }
        classCode += `    }\n`;
        
        classCode += `}\n`;
        
        return classCode;
    }
}