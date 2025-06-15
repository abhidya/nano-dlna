// Moving Clouds Animation - Adapted from https://codepen.io/a7rarpress/pen/NWeqOVw
class MovingCloudsAnimation extends BaseAnimation {
    setup() {
        // Cloud parameters
        this.clouds = [];
        this.baseSpeed = 20; // Base animation duration in seconds
        
        // Data-driven parameters
        this.windSpeedMultiplier = 1.0;
        
        // Create cloud layers
        this.createClouds();
    }
    
    createClouds() {
        // Cloud image URLs from the original CodePen
        const cloudImages = [
            'https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEhhtiwNp_GGXVBTIBHgwcU1iQfvBwGcNpEWws17jURxLgsTocyKGMzAWZK5-mNe3XprsjDz36yis19PmnSKvpEtg_Lbwto3pgFoOSTxCqcwp_v5OsNqRl23bzqssv8epDnNQazhL2AB1OuITxdhlqfv_YsXirU0W_mbfLYisiFPYgR1G0cpo9RumyNMq5M/s1600/cloud-03.png',
            'https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEjgpQUDtHjzt5ERnQ41HOOChn4ruWGjmY72CqEtryfk_IOvHn9rrcf_JNlvREpx0tLcc2vPbThJfuKRcDDE1sVBVism3kDKSL3EqPoPqy3z09gCfjcw3UzCpoeGCHj5O397FDzu-4tVI7R36f-zd73bFw_C3k4N_2bR5wRl-D-Ae1_wJZMMe2aPp3qmWLk/s1600/cloud-01.png',
            'https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEisGYgS3dB3vT_wI4DB4anTvu5KWnSpvx5QkkPtLkWZ2LGm64TkWFQs8nqevH5KeFi3bfE7BO4Cny8hwr_9jiBycBsoQq7T1qS_2WuCI0uYbjE0Kn7y5PxtapKiaf4VQHBoVeLrxjjm78Cx8CpiZG16IkJ6Skd17BD0J-IpgWo_MT8TE3qiQCxsQAdWJ6U/s1600/cloud-02.png',
            'https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEgtF2ldV1Z-0zEQa0NUSzO7bLUVRXyaAXBiWGcXQrl4dQC2fCoMHaxSblPg57hTZlR5j16VEVpvmAA0k_hmo45uSdDu5q1bL7jQOaJqFJjeb_B62tgepM6Rig8uQNey1WojLy4zvbUKmPlDbcL_hzhHiX0nhIwJEefJ1XLfRNi1_yuMI08XzDPVOa_ds0U/s1600/cloud-04.png'
        ];
        
        // Create cloud layers with different speeds
        const speedMultipliers = [1, 2, 3, 4]; // Original uses 20s, 40s, 60s, 80s
        
        cloudImages.forEach((imgSrc, index) => {
            const img = new Image();
            img.crossOrigin = 'anonymous';
            img.src = imgSrc;
            
            const cloud = {
                image: img,
                loaded: false,
                x: this.canvas.width,
                speedMultiplier: speedMultipliers[index],
                opacity: 0.7 - (index * 0.1), // Vary opacity for depth
                scale: 1.0 - (index * 0.1) // Vary scale for depth
            };
            
            img.onload = () => {
                cloud.loaded = true;
            };
            
            img.onerror = () => {
                console.warn(`Failed to load cloud image ${index + 1}`);
                // Create a procedural cloud as fallback
                cloud.loaded = true;
                cloud.useCanvas = true;
                cloud.canvas = this.createProceduralCloud();
            };
            
            this.clouds.push(cloud);
        });
    }
    
    createProceduralCloud() {
        // Create a simple procedural cloud using canvas
        const cloudCanvas = document.createElement('canvas');
        cloudCanvas.width = 400;
        cloudCanvas.height = 200;
        const ctx = cloudCanvas.getContext('2d');
        
        // Draw cloud shape with multiple circles
        ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
        
        // Main body
        for (let i = 0; i < 6; i++) {
            const x = 80 + i * 40;
            const y = 100 + Math.sin(i) * 20;
            const r = 40 + Math.random() * 20;
            ctx.beginPath();
            ctx.arc(x, y, r, 0, Math.PI * 2);
            ctx.fill();
        }
        
        // Top puffs
        for (let i = 0; i < 4; i++) {
            const x = 120 + i * 40;
            const y = 60 + Math.sin(i * 2) * 10;
            const r = 30 + Math.random() * 15;
            ctx.beginPath();
            ctx.arc(x, y, r, 0, Math.PI * 2);
            ctx.fill();
        }
        
        return cloudCanvas;
    }
    
    draw() {
        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw sky gradient background
        const gradient = this.ctx.createLinearGradient(0, 0, 0, this.canvas.height);
        gradient.addColorStop(0, '#87CEEB'); // Sky blue
        gradient.addColorStop(1, '#E0F6FF'); // Light blue
        this.ctx.fillStyle = gradient;
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw clouds
        this.clouds.forEach((cloud, index) => {
            if (!cloud.loaded) return;
            
            // Calculate speed based on data
            const speed = (this.baseSpeed * cloud.speedMultiplier) / this.windSpeedMultiplier;
            const pixelsPerFrame = this.canvas.width / (speed * 60); // 60 FPS
            
            // Update position
            cloud.x -= pixelsPerFrame;
            
            // Reset position when cloud goes off screen
            if (cloud.x < -this.canvas.width) {
                cloud.x = this.canvas.width;
            }
            
            // Draw cloud
            this.ctx.save();
            this.ctx.globalAlpha = cloud.opacity;
            
            const img = cloud.useCanvas ? cloud.canvas : cloud.image;
            const width = this.canvas.width * cloud.scale;
            const height = (this.canvas.height * 0.6) * cloud.scale;
            const y = (this.canvas.height * 0.1) + (index * this.canvas.height * 0.05);
            
            this.ctx.drawImage(img, cloud.x, y, width, height);
            
            // Draw a second copy for seamless looping
            if (cloud.x < 0) {
                this.ctx.drawImage(img, cloud.x + this.canvas.width * 2, y, width, height);
            }
            
            this.ctx.restore();
        });
    }
    
    onDataUpdate() {
        if (this.data.weather) {
            // Wind speed affects cloud movement
            // Map wind speed (0-50 km/h) to speed multiplier (0.5-3.0)
            this.windSpeedMultiplier = 0.5 + (this.data.weather.windSpeed / 50) * 2.5;
            
            // Weather conditions affect cloud opacity
            if (this.data.weather.conditions === 'clear') {
                // Fewer, lighter clouds
                this.clouds.forEach((cloud, index) => {
                    cloud.opacity = 0.3 - (index * 0.05);
                });
            } else if (this.data.weather.conditions === 'cloudy' || this.data.weather.conditions === 'rain') {
                // More, denser clouds
                this.clouds.forEach((cloud, index) => {
                    cloud.opacity = 0.9 - (index * 0.05);
                });
            } else {
                // Default opacity
                this.clouds.forEach((cloud, index) => {
                    cloud.opacity = 0.7 - (index * 0.1);
                });
            }
        }
    }
}