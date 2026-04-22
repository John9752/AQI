/**
 * AQIAnimator - High-Fidelity Vector Environment Controller
 * Uses GSAP and layered SVG graphics for volumetric shading.
 */

gsap.registerPlugin(MotionPathPlugin);

class AQIAnimator {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) return;
        
        this.currentLevel = 1;

        // Scene Generation
        this.initDOM();
        this.spawnClouds();
        this.spawnBirds();
        this.spawnTrees();
        this.spawnFlora();
        
        this.initParallax();
        this.initAudio();
        
        this.applySmokePhysics();
        this.applyWindPhysics(this.currentLevel);

        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                gsap.globalTimeline.pause();
                if(this.audioBirds) this.audioBirds.pause();
                if(this.audioWind) this.audioWind.pause();
            } else {
                gsap.globalTimeline.play();
                this.updateAudioForLevel(this.currentLevel);
            }
        });
    }

    initDOM() {
        this.container.innerHTML = '';
        this.container.className = 'env-scene aqi-state-1';

        this.mountainLayer = this.createLayer('layer-mountains env-layer');
        this.cloudLayer = this.createLayer('layer-clouds env-layer');
        this.birdLayer = this.createLayer('layer-birds env-layer');
        this.smokeLayer = this.createLayer('layer-smoke env-layer');
        this.treeLayer = this.createLayer('layer-trees env-layer');
        
        // Grass architecture
        this.grassLayer = this.createLayer('layer-grass env-layer');
        // Cracked Earth Pattern
        this.groundTexture = document.createElement('div');
        this.groundTexture.className = 'layer-ground-texture';
        const p = `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M54.627 0l.83.83-20.916 20.916.326.327 20.59 20.59-1.25 1.25-20.59-20.59-.327.326-17.16 17.16-1.25-1.25 17.16-17.16-.326-.327-14.896-14.896 1.25-1.25 14.896 14.896.327-.326zM22.5 0l2.5 2.5-2.5 2.5-2.5-2.5 2.5-2.5zm0-5l7.5 7.5-7.5 7.5-7.5-7.5 7.5-7.5zM0 22.5l2.5 2.5-2.5 2.5-2.5-2.5 2.5-2.5z' fill='%231c1917' fill-opacity='0.15' fill-rule='evenodd'/%3E%3C/svg%3E")`;
        this.groundTexture.style.background = p;
        this.grassLayer.appendChild(this.groundTexture);

        this.floraLayer = this.createLayer('layer-flora');
        
        this.container.append(this.mountainLayer, this.cloudLayer, this.birdLayer, this.smokeLayer, this.treeLayer, this.grassLayer, this.floraLayer);
    }

    createLayer(className) {
        const div = document.createElement('div');
        div.className = className;
        return div;
    }

    /* --- Spawners --- */
    spawnFlora() {
        // High fidelity vector Bushes
        const bushSVG = `
            <svg viewBox="0 0 100 60" preserveAspectRatio="xMidYMax meet" style="width: 100%; height: 100%; filter: drop-shadow(0px 5px 5px rgba(0,0,0,0.3));">
                <radialGradient id="bush-grad" cx="40%" cy="30%" r="60%">
                    <stop offset="0%" stop-color="#16a34a" class="flora-stop-1" />
                    <stop offset="100%" stop-color="#064e3b" class="flora-stop-2" />
                </radialGradient>
                <g class="canopy-layer bush-cluster">
                    <circle cx="50" cy="30" r="30" fill="url(#bush-grad)" />
                    <circle cx="25" cy="40" r="20" fill="url(#bush-grad)" />
                    <circle cx="75" cy="40" r="20" fill="url(#bush-grad)" />
                </g>
            </svg>
        `;
        
        // Detailed vector grass tufts
        const grassTuftSVG = `
            <svg viewBox="0 0 40 40" preserveAspectRatio="xMidYMax meet" style="width: 100%; height: 100%;">
                <g fill="none" stroke="#22c55e" stroke-linecap="round" class="flora-stroke">
                    <path class="grass-blade blade-1" d="M20,40 Q15,20 10,10" stroke-width="3" />
                    <path class="grass-blade blade-2" d="M20,40 Q25,15 30,5" stroke-width="2" />
                    <path class="grass-blade blade-3" d="M20,40 L20,15" stroke-width="4" />
                </g>
            </svg>
        `;

        // Spawn 10 Bushes randomly
        for(let i=0; i<10; i++) {
            const bush = document.createElement('div');
            bush.className = 'flora-element bush flora-instance';
            bush.innerHTML = bushSVG;
            bush.style.left = `${Math.random() * 95}vw`;
            const scale = Math.random() * 0.5 + 0.8;
            bush.style.width = `${100 * scale}px`;
            bush.style.height = `${60 * scale}px`;
            this.floraLayer.appendChild(bush);
        }

        // Spawn 20 Grass Tufts
        for(let i=0; i<20; i++) {
            const tuft = document.createElement('div');
            tuft.className = 'flora-element grass-tuft flora-instance';
            tuft.innerHTML = grassTuftSVG;
            tuft.style.left = `${Math.random() * 98}vw`;
            const scale = Math.random() * 0.5 + 0.5;
            tuft.style.width = `${40 * scale}px`;
            tuft.style.height = `${40 * scale}px`;
            this.floraLayer.appendChild(tuft);
        }
    }

    spawnTrees() {
        // High-fidelity vector tree with radial gradients for volume and depth, and bare branches hidden beneath.
        const treeSVG = `
            <svg class="tree-svg" viewBox="0 0 200 300" preserveAspectRatio="xMidYMax meet" style="filter: drop-shadow(0px 10px 10px rgba(0,0,0,0.3));">
                <defs>
                    <!-- Leaf Shading Gradients -->
                    <radialGradient id="canopy-grad-dark" cx="40%" cy="30%" r="60%">
                        <stop offset="0%" stop-color="#16a34a" class="leaf-stop-1" />
                        <stop offset="100%" stop-color="#14532d" class="leaf-stop-2" />
                    </radialGradient>
                    <radialGradient id="canopy-grad-light" cx="30%" cy="20%" r="50%">
                        <stop offset="0%" stop-color="#22c55e" class="leaf-stop-1" />
                        <stop offset="100%" stop-color="#15803d" class="leaf-stop-2" />
                    </radialGradient>
                    <radialGradient id="canopy-grad-mid" cx="50%" cy="25%" r="55%">
                        <stop offset="0%" stop-color="#15803d" class="leaf-stop-1" />
                        <stop offset="100%" stop-color="#064e3b" class="leaf-stop-2" />
                    </radialGradient>
                    <!-- Trunk Texture Gradient -->
                    <linearGradient id="trunk-grad" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" stop-color="#451a03" />
                        <stop offset="50%" stop-color="#78350f" />
                        <stop offset="100%" stop-color="#292524" />
                    </linearGradient>
                </defs>

                <!-- Dead Branches (Visible only when canopy fades) -->
                <g class="dead-branches" stroke="#292524" stroke-width="8" stroke-linecap="round" fill="none">
                    <path d="M100,280 Q90,140 100,100" />
                    <path d="M100,180 Q60,150 40,110 M40,110 Q30,90 20,100" stroke-width="6"/>
                    <path d="M100,160 Q140,130 160,90 M160,90 Q170,70 180,80" stroke-width="6"/>
                    <path d="M100,120 Q80,80 70,50 M100,110 Q120,70 140,40" stroke-width="4"/>
                </g>

                <!-- Main Trunk -->
                <path class="trunk" d="M80,300 L120,300 C110,250 115,200 105,150 L95,150 C85,200 90,250 80,300 Z" fill="url(#trunk-grad)" />
                
                <!-- Lush Volumetric Canopy Layers -->
                <g class="canopy-back canopy-layer" style="transform-origin: 50% 60%;">
                    <circle cx="100" cy="110" r="80" fill="url(#canopy-grad-dark)" />
                </g>
                <g class="canopy-left canopy-layer" style="transform-origin: 30% 70%;">
                    <circle cx="50" cy="140" r="50" fill="url(#canopy-grad-mid)" />
                    <circle cx="40" cy="90" r="45" fill="url(#canopy-grad-mid)" />
                </g>
                <g class="canopy-right canopy-layer" style="transform-origin: 70% 70%;">
                    <circle cx="150" cy="140" r="50" fill="url(#canopy-grad-dark)" />
                    <circle cx="160" cy="90" r="45" fill="url(#canopy-grad-dark)" />
                </g>
                <g class="canopy-top canopy-layer" style="transform-origin: 50% 40%;">
                    <circle cx="100" cy="60" r="60" fill="url(#canopy-grad-light)" />
                    <path d="M60,60 C40,40 60,0 100,0 C140,0 160,40 140,60 Z" fill="url(#canopy-grad-light)" />
                </g>
            </svg>
        `;

        for (let i = 0; i < 5; i++) {
            const tree = document.createElement('div');
            tree.className = 'tree-container';
            tree.innerHTML = treeSVG;
            this.treeLayer.appendChild(tree);
        }
    }

    spawnClouds() {
        const cloudSVG = `<svg viewBox="0 0 100 50"><path d="M20,30 Q10,30 10,20 Q10,10 20,10 Q30,0 45,10 Q60,-5 75,10 Q90,10 90,20 Q90,30 80,30 Z" /></svg>`;
        for (let i = 0; i < 6; i++) {
            const cloud = document.createElement('div');
            cloud.className = 'cloud';
            cloud.innerHTML = cloudSVG;
            cloud.style.top = `${Math.random() * 30 + 5}vh`;
            cloud.style.transform = `scale(${Math.random() * 0.8 + 0.4})`;
            
            const startX = -300 - Math.random() * 500;
            const endX = window.innerWidth + 300;
            
            gsap.fromTo(cloud, 
                { x: startX },
                { 
                    x: endX, 
                    duration: "random(40, 80)", 
                    ease: "none", 
                    repeat: -1,
                    delay: "random(0, -40)"
                }
            );
            this.cloudLayer.appendChild(cloud);
        }
    }

    spawnBirds() {
        const birdSVG = `<svg viewBox="0 0 100 50"><path class="wing wing-left" d="M50,25 Q30,5 10,10 Q30,20 50,25" fill="none" stroke="currentColor" stroke-width="4"/><path class="wing wing-right" d="M50,25 Q70,5 90,10 Q70,20 50,25" fill="none" stroke="currentColor" stroke-width="4"/></svg>`;
        for (let i = 0; i < 7; i++) {
            const bird = document.createElement('div');
            bird.className = 'bird bird-instance';
            bird.innerHTML = birdSVG;
            this.birdLayer.appendChild(bird);

            const wings = bird.querySelectorAll('.wing');
            gsap.to(wings, {
                attr: { d: (index) => index === 0 ? "M50,25 Q30,45 10,40 Q30,30 50,25" : "M50,25 Q70,45 90,40 Q70,30 50,25" },
                duration: "random(0.15, 0.3)",
                yoyo: true,
                repeat: -1,
                ease: "sine.inOut"
            });
            this.animateBirdFlight(bird);
        }
    }

    animateBirdFlight(bird) {
        const path = [];
        let curX = -100;
        let curY = Math.random() * window.innerHeight * 0.4;
        for(let i=0; i<4; i++) {
            curX += (window.innerWidth + 200) / 4;
            curY += (Math.random() - 0.5) * 300;
            path.push({x: curX, y: curY});
        }
        gsap.fromTo(bird, 
            { x: -100, y: Math.random() * 200, opacity: 1, scale: "random(0.4, 0.8)" },
            {
                duration: "random(15, 25)",
                motionPath: { path: path, curviness: 1.5, autoRotate: true },
                ease: "power1.inOut",
                onComplete: () => {
                    if (this.currentLevel <= 3) this.animateBirdFlight(bird); 
                    else gsap.set(bird, { opacity: 0 }); 
                }
            }
        );
    }

    /* --- GSAP Physics Engine --- */
    applyWindPhysics(level) {
        if (this.windTimeline) this.windTimeline.kill();
        this.windTimeline = gsap.timeline();

        // If dead (level 6), trees are bare rigid branches
        if (level === 6) {
            gsap.to('.tree-container', { rotation: 0, duration: 2 });
            gsap.to('.canopy-layer', { rotation: 0, duration: 2 });
            gsap.to('.grass-blade', { rotation: 0, duration: 2 });
            return;
        }

        const swayAmp = level === 1 ? 2 : (level * 1.5); 
        const speed = level === 1 ? 1 : (level * 0.5);

        // Entire Trunk Sway
        this.windTimeline.to('.tree-container', {
            rotation: () => Math.random() * swayAmp * (Math.random()>0.5?1:-1),
            duration: () => Math.random() * 2 + 3,
            ease: "sine.inOut", yoyo: true, repeat: -1, stagger: { amount: 2, from: "random" }
        });

        // Independent, organic canopy layer jiggling
        gsap.to('.canopy-top', { rotation: swayAmp * 1.2, duration: 3.5 / speed, ease: "sine.inOut", yoyo: true, repeat: -1 });
        gsap.to('.canopy-left', { rotation: -swayAmp * 0.8, duration: 2.8 / speed, ease: "sine.inOut", yoyo: true, repeat: -1 });
        gsap.to('.canopy-right', { rotation: swayAmp * 0.9, duration: 3.1 / speed, ease: "sine.inOut", yoyo: true, repeat: -1 });
        
        // Flora Sway (Grass and Bushes catching low wind)
        gsap.to('.grass-blade', {
            rotation: swayAmp * 2,
            duration: 1.5 / speed,
            ease: "sine.inOut", yoyo: true, repeat: -1,
            stagger: { amount: 3, from: "left" } // Rolling wind effect across the monitor!
        });
        
        gsap.to('.bush-cluster', {
            rotation: swayAmp * 0.5,
            duration: 2.5 / speed,
            ease: "power1.inOut", yoyo: true, repeat: -1,
            stagger: { amount: 2, from: "random" }
        });
    }

    applySmokePhysics() {
        gsap.to(this.smokeLayer, { x: "-50%", duration: 60, ease: "none", repeat: -1 });
        gsap.to(this.smokeLayer, { scale: 1.1, duration: 15, yoyo: true, repeat: -1, ease: "sine.inOut" });
    }

    /* --- AQI Dynamic Visual Binding --- */
    setAQILevel(level) {
        if (this.currentLevel === level) return;
        
        for (let i = 1; i <= 6; i++) {
            this.container.classList.remove(`aqi-state-${i}`);
        }
        this.currentLevel = level;
        this.container.classList.add(`aqi-state-${level}`);
        
        this.applyWindPhysics(level);

        // Map AQI to Foliage Health via GSAP manipulating Gradient Stops
        const foliageHealth = [
            { c1: '#22c55e', c2: '#14532d', op: 1, g_op: 0 }, // L1 Lush Green
            { c1: '#65a30d', c2: '#3f6212', op: 0.9, g_op: 0 }, // L2 Slight fade
            { c1: '#ca8a04', c2: '#854d0e', op: 0.7, g_op: 0.2 }, // L3 Yellowish
            { c1: '#b45309', c2: '#78350f', op: 0.4, g_op: 0.4 }, // L4 Brown
            { c1: '#451a03', c2: '#292524', op: 0.1, g_op: 0.7 }, // L5 Dead/sparse
            { c1: '#1c1917', c2: '#0c0a09', op: 0, g_op: 1 }    // L6 Bare branches, purely cracked earth
        ];
        
        const target = foliageHealth[level - 1];

        // Animate color shifts in Tree SVG gradients
        gsap.to('.leaf-stop-1', { attr: { "stop-color": target.c1 }, duration: 2 });
        gsap.to('.leaf-stop-2', { attr: { "stop-color": target.c2 }, duration: 2 });
        // Animate color shifts in Bush SVG gradients
        gsap.to('.flora-stop-1', { attr: { "stop-color": target.c1 }, duration: 2 });
        gsap.to('.flora-stop-2', { attr: { "stop-color": target.c2 }, duration: 2 });
        // Animate color shifts in Grass stroke
        gsap.to('.flora-stroke', { attr: { "stroke": target.c1 }, duration: 2 });
        
        // At high AQI, canopy fades to reveal dead branches underneath
        gsap.to(['.canopy-layer', '.grass-blade'], { opacity: target.op, duration: 2 });
        // Ground Texture fades in to show cracked earth
        gsap.to(this.groundTexture, { opacity: target.g_op, duration: 2 });

        // Resurrect birds if AQI returns to healthy
        if (level <= 3) {
            const deadBirds = document.querySelectorAll('.bird-instance');
            deadBirds.forEach(bird => {
                if(gsap.getProperty(bird, "opacity") === 0) {
                    this.animateBirdFlight(bird);
                }
            });
        }
        this.updateAudioForLevel(level);
    }

    /* --- Parallax & Audio --- */
    initParallax() {
        document.addEventListener('mousemove', (e) => {
            const x = (e.clientX / window.innerWidth - 0.5) * 2; 
            const y = (e.clientY / window.innerHeight - 0.5) * 2;
            gsap.to(this.mountainLayer, { x: x * 10, y: y * 5, duration: 1, ease: "power2.out" });
            gsap.to(this.cloudLayer, { y: y * -10, duration: 1, ease: "power2.out" }); 
            gsap.to(this.treeLayer, { x: x * 30, duration: 0.5, ease: "power2.out" }); 
        });
    }

    initAudio() {
        this.audioEnabled = false;
        this.audioBirds = new Audio('https://upload.wikimedia.org/wikipedia/commons/4/4e/Birds_singing_in_spring.ogg');
        this.audioBirds.loop = true; this.audioBirds.volume = 0.3;
        this.audioWind = new Audio('https://upload.wikimedia.org/wikipedia/commons/e/ec/Wind-noise.ogg');
        this.audioWind.loop = true; this.audioWind.volume = 0.5;

        let btn = document.getElementById('audioToggleBtn');
        if (!btn) {
            btn = document.createElement('button');
            btn.id = 'audioToggleBtn';
            btn.className = 'audio-control-btn';
            btn.innerHTML = `🔇 Unmute Environment`;
            document.body.appendChild(btn);
        }

        btn.addEventListener('click', () => {
            this.audioEnabled = !this.audioEnabled;
            if (this.audioEnabled) {
                btn.innerHTML = `🔊 Mute Environment`;
                this.updateAudioForLevel(this.currentLevel);
            } else {
                btn.innerHTML = `🔇 Unmute Environment`;
                this.audioBirds.pause();
                this.audioWind.pause();
            }
        });
    }

    updateAudioForLevel(level) {
        if (!this.audioEnabled) return;
        if (level <= 2) {
            if (this.audioBirds.paused) this.audioBirds.play().catch(()=>{});
            if (this.audioWind.paused) this.audioWind.play().catch(()=>{});
            gsap.to(this.audioBirds, {volume: 0.4, duration: 2});
            gsap.to(this.audioWind, {volume: 0.2, duration: 2});
        } else if (level <= 4) {
            gsap.to(this.audioBirds, {volume: 0, duration: 2, onComplete: () => this.audioBirds.pause()});
            if (this.audioWind.paused) this.audioWind.play().catch(()=>{});
            gsap.to(this.audioWind, {volume: 0.6, duration: 2});
        } else {
            this.audioBirds.pause();
            if (this.audioWind.paused) this.audioWind.play().catch(()=>{});
            gsap.to(this.audioWind, {volume: 1.0, duration: 2}); 
        }
    }
}

window.aqiAnimator = null;
document.addEventListener('DOMContentLoaded', () => {
    const oldCanvas = document.getElementById('tree-canvas');
    if (oldCanvas) oldCanvas.remove();
    
    window.aqiAnimator = new AQIAnimator('dynamic-bg-container');
    if (window.aqiAnimator) window.aqiAnimator.setAQILevel(1);
    document.dispatchEvent(new Event('environmentReady'));
});
