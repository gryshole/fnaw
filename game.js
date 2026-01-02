const AudioManager = {
    ctx: null,
    ambienceOsc: null,
    ambienceGain: null,
    fanOsc: null,
    fanGain: null,
    menuDroneOsc: null,
	rustleSource: null, 
    rustleGain: null,
    init: function() {
        if (!this.ctx) {
            this.ctx = new(window.AudioContext || window.webkitAudioContext)();
        }
        if (this.ctx.state === 'suspended') {
            this.ctx.resume();
        }
    },
    playMenuDrone: function() {
        this.init();
        if (this.menuDroneOsc) return;
        const t = this.ctx.currentTime;
        this.menuDroneOsc = this.ctx.createOscillator();
        this.menuDroneOsc.type = 'sawtooth';
        this.menuDroneOsc.frequency.setValueAtTime(40, t);
        const gain = this.ctx.createGain();
        gain.gain.setValueAtTime(0.05, t);
        const filter = this.ctx.createBiquadFilter();
        filter.type = 'lowpass';
        filter.frequency.setValueAtTime(200, t);
        this.menuDroneOsc.connect(filter);
        filter.connect(gain);
        gain.connect(this.ctx.destination);
        this.menuDroneOsc.start();
    },
    stopMenuDrone: function() {
        if (this.menuDroneOsc) {
            try {
                this.menuDroneOsc.stop();
            } catch (e) {}
            this.menuDroneOsc = null;
        }
    },
    startFanAmbience: function() {
        if (this.fanOsc) return;
        this.stopMenuDrone();
        const t = this.ctx.currentTime;
        const bufferSize = 2 * this.ctx.sampleRate;
        const noiseBuffer = this.ctx.createBuffer(1, bufferSize, this.ctx.sampleRate);
        const output = noiseBuffer.getChannelData(0);
        for (let i = 0; i < bufferSize; i++) output[i] = Math.random() * 2 - 1;
        this.fanOsc = this.ctx.createBufferSource();
        this.fanOsc.buffer = noiseBuffer;
        this.fanOsc.loop = true;
        this.fanGain = this.ctx.createGain();
        this.fanGain.gain.setValueAtTime(0.03, t);
        const noiseFilter = this.ctx.createBiquadFilter();
        noiseFilter.type = 'lowpass';
        noiseFilter.frequency.value = 400;
        this.fanOsc.connect(noiseFilter);
        noiseFilter.connect(this.fanGain);
        this.fanGain.connect(this.ctx.destination);
        this.fanOsc.start();
        this.ambienceOsc = this.ctx.createOscillator();
        this.ambienceOsc.type = 'sine';
        this.ambienceOsc.frequency.setValueAtTime(60, t);
        this.ambienceGain = this.ctx.createGain();
        this.ambienceGain.gain.setValueAtTime(0.02, t);
        this.ambienceOsc.connect(this.ambienceGain);
        this.ambienceGain.connect(this.ctx.destination);
        this.ambienceOsc.start();
    },
    stopFanAmbience: function() {
        if (this.fanOsc) {
            try {
                this.fanOsc.stop();
            } catch (e) {};
            this.fanOsc = null;
        }
        if (this.ambienceOsc) {
            try {
                this.ambienceOsc.stop();
            } catch (e) {};
            this.ambienceOsc = null;
        }
    },
	startLeftRustle: function() {
        this.init();
        if (this.rustleSource) return; // Вже грає, не дублюємо

        const t = this.ctx.currentTime;
        
        // 1. Генерація шуму (Buffer)
        const bufferSize = this.ctx.sampleRate * 2; // 2 секунди семплу
        const buffer = this.ctx.createBuffer(1, bufferSize, this.ctx.sampleRate);
        const data = buffer.getChannelData(0);
        for (let i = 0; i < bufferSize; i++) {
            data[i] = (Math.random() * 2 - 1) * 0.5; // Білий шум
        }

        this.rustleSource = this.ctx.createBufferSource();
        this.rustleSource.buffer = buffer;
        this.rustleSource.loop = true;

        // 2. Фільтр (Bandpass) - робимо звук схожим на шурхіт тканини
        const filter = this.ctx.createBiquadFilter();
        filter.type = 'bandpass';
        filter.frequency.value = 400; // Низька частота шурхоту
        filter.Q.value = 1.5;

        // 3. Панорама (ТІЛЬКИ ЛІВО)
        const panner = this.ctx.createStereoPanner();
        panner.pan.value = -0.9; // Майже повністю в лівому вусі

        // 4. Гучність (LFO для нерівномірності)
        this.rustleGain = this.ctx.createGain();
        this.rustleGain.gain.value = 0.15; // Тихий звук

        // З'єднання
        this.rustleSource.connect(filter);
        filter.connect(panner);
        panner.connect(this.rustleGain);
        this.rustleGain.connect(this.ctx.destination);

        this.rustleSource.start(0);
    },
    stopLeftRustle: function() {
        if (this.rustleSource) {
            try {
                this.rustleSource.stop();
                this.rustleSource.disconnect();
                this.rustleGain.disconnect();
            } catch (e) {}
            this.rustleSource = null;
            this.rustleGain = null;
        }
    },
    play: function(soundName) {
        if (!this.ctx) return;
        const t = this.ctx.currentTime;
        switch (soundName) {
            case 'blip':
                let osc = this.ctx.createOscillator();
                let gain = this.ctx.createGain();
                osc.type = 'sine';
                osc.frequency.setValueAtTime(800, t);
                gain.gain.setValueAtTime(0.1, t);
                gain.gain.exponentialRampToValueAtTime(0.001, t + 0.1);
                osc.connect(gain);
                gain.connect(this.ctx.destination);
                osc.start(t);
                osc.stop(t + 0.1);
                break;
            case 'door':
                let dOsc = this.ctx.createOscillator();
                let dGain = this.ctx.createGain();
                dOsc.type = 'square';
                dOsc.frequency.setValueAtTime(100, t);
                dOsc.frequency.exponentialRampToValueAtTime(0.01, t + 0.3);
                dGain.gain.setValueAtTime(0.2, t);
                dGain.gain.exponentialRampToValueAtTime(0.001, t + 0.3);
                dOsc.connect(dGain);
                dGain.connect(this.ctx.destination);
                dOsc.start(t);
                dOsc.stop(t + 0.3);
                break;
            case 'error':
                let eOsc = this.ctx.createOscillator();
                let eGain = this.ctx.createGain();
                eOsc.type = 'sawtooth';
                eOsc.frequency.setValueAtTime(150, t);
                eGain.gain.setValueAtTime(0.15, t);
                eGain.gain.exponentialRampToValueAtTime(0.001, t + 0.2);
                eOsc.connect(eGain);
                eGain.connect(this.ctx.destination);
                eOsc.start(t);
                eOsc.stop(t + 0.2);
                break;
            case 'scream':
                // ВАРІАТИВНІСТЬ СКРИМЕРІВ
                // Вибираємо один з 3-х варіантів крику
                const variant = Math.floor(Math.random() * 3);
                
                // Створюємо Master Gain для крику (щоб був гучним!)
                let mGain = this.ctx.createGain();
                mGain.gain.setValueAtTime(1.0, t); // Максимальна гучність
                mGain.gain.exponentialRampToValueAtTime(0.01, t + 2.5);
                mGain.connect(this.ctx.destination);

                if (variant === 0) {
                    // ВАРІАНТ 1: "The Classic" (FM-синтез, схожий на оригінал FNAF 1)
                    // Carrier (Основний тон - пронизливий)
                    let carrier = this.ctx.createOscillator();
                    carrier.type = 'sawtooth';
                    carrier.frequency.setValueAtTime(400, t);
                    carrier.frequency.linearRampToValueAtTime(100, t + 2); // Падає вниз

                    // Modulator (Вібрація - створює "хрип")
                    let mod = this.ctx.createOscillator();
                    mod.type = 'square';
                    mod.frequency.setValueAtTime(50, t); // Швидка вібрація
                    
                    let modGain = this.ctx.createGain();
                    modGain.gain.setValueAtTime(1000, t); // Сила модуляції

                    // З'єднання: Modulator -> ModGain -> Carrier.frequency
                    mod.connect(modGain);
                    modGain.connect(carrier.frequency);
                    carrier.connect(mGain);

                    carrier.start(t);
                    mod.start(t);
                    carrier.stop(t + 2.5);
                    mod.stop(t + 2.5);
                } 
                else if (variant === 1) {
                    // ВАРІАНТ 2: "The Banshee" (Високий писк + Білий шум)
                    let osc1 = this.ctx.createOscillator();
                    osc1.type = 'sawtooth';
                    osc1.frequency.setValueAtTime(800, t);
                    osc1.frequency.exponentialRampToValueAtTime(1200, t + 0.5); // Вгору!
                    osc1.frequency.linearRampToValueAtTime(200, t + 2); // Потім різко вниз

                    // Додаємо шум для бруду
                    const bSize = this.ctx.sampleRate * 2;
                    const bBuf = this.ctx.createBuffer(1, bSize, this.ctx.sampleRate);
                    const bData = bBuf.getChannelData(0);
                    for(let i=0; i<bSize; i++) bData[i] = Math.random() * 2 - 1;
                    
                    let noise = this.ctx.createBufferSource();
                    noise.buffer = bBuf;
                    
                    // Фільтр для шуму (щоб був різким)
                    let nFilter = this.ctx.createBiquadFilter();
                    nFilter.type = 'highpass';
                    nFilter.frequency.value = 1000;

                    osc1.connect(mGain);
                    noise.connect(nFilter);
                    nFilter.connect(mGain);

                    osc1.start(t);
                    noise.start(t);
                    osc1.stop(t + 2.5);
                    noise.stop(t + 2.5);
                } 
                else {
                    // ВАРІАНТ 3: "The Beast" (Низький, глибокий гуркіт)
                    let osc1 = this.ctx.createOscillator();
                    let osc2 = this.ctx.createOscillator();
                    
                    osc1.type = 'square';
                    osc2.type = 'sawtooth';

                    // Диссонанс (Detune)
                    osc1.frequency.setValueAtTime(150, t);
                    osc2.frequency.setValueAtTime(155, t); // Трохи зсунуто
                    
                    osc1.frequency.linearRampToValueAtTime(50, t + 2);
                    osc2.frequency.linearRampToValueAtTime(55, t + 2);

                    osc1.connect(mGain);
                    osc2.connect(mGain);

                    osc1.start(t);
                    osc2.start(t);
                    osc1.stop(t + 2.5);
                    osc2.stop(t + 2.5);
                }
                break;
            case 'win':
                let wOsc = this.ctx.createOscillator();
                let wGain = this.ctx.createGain();
                wOsc.type = 'triangle';
                wOsc.frequency.setValueAtTime(523.25, t);
                wOsc.frequency.setValueAtTime(659.25, t + 0.2);
                wOsc.frequency.setValueAtTime(783.99, t + 0.4);
                wOsc.frequency.setValueAtTime(1046.50, t + 0.6);
                wGain.gain.setValueAtTime(0.3, t);
                wGain.gain.linearRampToValueAtTime(0, t + 2);
                wOsc.connect(wGain);
                wGain.connect(this.ctx.destination);
                wOsc.start(t);
                wOsc.stop(t + 2);
                break;
        }
    },
	playFootstep: function(panValue) { // panValue: -1 (ліво) ... 0 (центр) ... 1 (право)
        if (!this.ctx) return;
        const t = this.ctx.currentTime;

        // 1. Джерело звуку (Шум для текстури "удару об бетон/метал")
        const bufferSize = this.ctx.sampleRate * 0.15; // короткий звук
        const buffer = this.ctx.createBuffer(1, bufferSize, this.ctx.sampleRate);
        const data = buffer.getChannelData(0);
        for (let i = 0; i < bufferSize; i++) {
            data[i] = (Math.random() * 2 - 1);
        }
        const noise = this.ctx.createBufferSource();
        noise.buffer = buffer;

        // 2. Фільтр (Lowpass), щоб зробити звук глухим і важким
        const filter = this.ctx.createBiquadFilter();
        filter.type = 'lowpass';
        filter.frequency.setValueAtTime(100, t); // Дуже низька частота (бас)
        filter.frequency.exponentialRampToValueAtTime(10, t + 0.15);

        // 3. Гучність (Envelope)
        const gain = this.ctx.createGain();
        gain.gain.setValueAtTime(0.4, t); // Гучність кроків
        gain.gain.exponentialRampToValueAtTime(0.001, t + 0.15);

        // 4. Панорама (Stereo Panner) - ЦЕ ГОЛОВНЕ
        const panner = this.ctx.createStereoPanner();
        panner.pan.setValueAtTime(panValue, t);

        // З'єднання: Noise -> Filter -> Gain -> Panner -> Destination
        noise.connect(filter);
        filter.connect(gain);
        gain.connect(panner);
        panner.connect(this.ctx.destination);

        noise.start(t);
    }
};

const GAME_CONFIG = {
    hourLength: 60,
    startPower: 100,
    // Це конфіг для HARD MODE (збалансований під 94%)
    baseDrainRate: 0.075, 
    usagePenalty: 0.05
};

const NIGHT_LEVELS = {
    1: { sparky: 2, clanker: 0, runner: 0, boss: 0 },
    2: { sparky: 6, clanker: 3, runner: 1, boss: 0 },
    3: { sparky: 8, clanker: 6, runner: 4, boss: 1 },
    4: { sparky: 12, clanker: 10, runner: 7, boss: 3 },
    // НІЧ 5 (HARD): Збалансована для проходження "на межі"
    5: { sparky: 12, clanker: 11, runner: 8, boss: 4 }
};

const paths = {
    sparky: ['1A', '1B', '2A'],
    clanker: ['1A', '1B', '4A'],
    boss: ['1A', '1B', '4A']
};

let state = {
    isPlaying: false,
    hardMode: true, // За замовчуванням Hard
    currentNight: 1,
    time: 0,
    power: 100,
    usage: 1,
    doors: { left: false, right: false },
    lights: { left: false, right: false },
    camera: { active: false, current: '1A' },
    gameOver: false,
	ai: {
        sparky: { level: 0, location: '1A', arrivalTime: 0 },
        clanker: { level: 0, location: '1A', arrivalTime: 0 },
        boss: { level: 0, location: '1A', arrivalTime: 0 },
        runner: { level: 0, stage: 0, timer: 0, baseTimer: 0 }
    }
};

let gameInterval, aiInterval;

// --- МЕНЮ ТА ІНІЦІАЛІЗАЦІЯ ---

window.onload = function() {
    const savedNight = localStorage.getItem('fnaf_night');
    const savedDiff = localStorage.getItem('fnaf_difficulty'); // "true" або "false"
    const continueBtn = document.getElementById('btn-continue');
    
    // Ініціалізація аудіо при кліку
    document.body.addEventListener('click', () => {
        AudioManager.playMenuDrone();
    }, { once: true });

    // Відновлення стану перемикача складності
    if (savedDiff === 'false') {
        toggleDifficulty(); // Якщо було збережено Easy, перемикаємо на Easy
    }

    if (savedNight) {
        continueBtn.classList.remove('disabled');
        let modeText = (savedDiff === 'true' || savedDiff === null) ? "HARD" : "EASY";
        continueBtn.innerText = `CONTINUE (Night ${savedNight} - ${modeText})`;
        continueBtn.onclick = () => {
            // При продовженні використовуємо збережену складність
            state.hardMode = (savedDiff === 'true' || savedDiff === null);
            initGame(parseInt(savedNight));
        };
    }
    
    updateDiffDisplay();
	
	// --- ЕФЕКТ НЕСТАБІЛЬНОГО ЗОБРАЖЕННЯ (GLITCH LOOP) ---
	(function startStaticGlitch() {
		const overlays = document.querySelectorAll('.static-overlay');
		
		function glitchLoop() {
			// Випадковий час до наступного "глюку" (від 50мс до 150мс)
			// Це робить шум "живим", а не циклічним
			let nextTimeout = 50 + Math.random() * 100;
			
			// Базова прозорість (трохи плаває)
			let baseOp = 0.08 + (Math.random() * 0.04); 
			
			// Шанс сильного стрибка (Glitch Spike) - 5%
			if (Math.random() > 0.95) {
				baseOp = 0.25 + (Math.random() * 0.2); // Різкий стрибок до 0.45
				// Якщо сильний глюк, наступний кадр буде швидше
				nextTimeout = 30; 
			}

			// Застосовуємо до всіх шарів статики (меню + гра)
			overlays.forEach(el => {
				el.style.opacity = baseOp;
			});

			setTimeout(glitchLoop, nextTimeout);
		}

		// Запускаємо петлю
		glitchLoop();
	})();
};

function toggleDifficulty() {
    state.hardMode = !state.hardMode;
    updateDiffDisplay();
}

function updateDiffDisplay() {
    const el = document.getElementById('diff-val');
    if (el) {
        el.innerText = state.hardMode ? "HARD" : "EASY";
        el.style.color = state.hardMode ? "red" : "#0f0";
        el.style.textShadow = state.hardMode ? "0 0 5px red" : "0 0 5px #0f0";
    }
}

// Функція для старту з меню (бере поточну вибрану складність)
function startSelected(night) {
    initGame(night);
}

function initGame(night) {
    AudioManager.stopMenuDrone();
    AudioManager.play('blip');
    
    // Зберігаємо вибір
    localStorage.setItem('fnaf_difficulty', state.hardMode);
    
    startGame(night);
}

function startGame(night) {
    document.getElementById('main-menu').classList.add('hidden');
    state.currentNight = night;
    let transition = document.getElementById('night-transition');
    document.getElementById('transition-time').innerText = "12:00 AM";
    
    let modeLabel = state.hardMode ? "" : "(Easy Mode)";
    document.getElementById('transition-night').innerText = `Night ${night} ${modeLabel}`;
    
    transition.classList.remove('hidden');
    setTimeout(() => {
        transition.classList.add('hidden');
        document.getElementById('in-game-interface').classList.remove('hidden');
        setupNight(night);
    }, 3000);
}

function setupNight(nightNum) {
    clearInterval(gameInterval);
    clearInterval(aiInterval);
    AudioManager.startFanAmbience();

    state.isPlaying = true;
    state.gameOver = false;
    state.time = 0;
    state.power = GAME_CONFIG.startPower;
    state.doors = { left: false, right: false };
    state.lights = { left: false, right: false };
    state.camera = { active: false, current: '1A' };
    
    // Скидаємо UI планшета
    document.getElementById('camera-screen').classList.remove('monitor-open');

    // Отримуємо рівні для HARD MODE
    let levels = NIGHT_LEVELS[nightNum] || NIGHT_LEVELS[5];
    
    // Налаштовуємо AI залежно від режиму
    if (state.hardMode) {
		console.log('Hard Night');
        // HARD MODE (Оригінальні розрахунки)
        state.ai.sparky.level = levels.sparky;
        state.ai.clanker.level = levels.clanker;
        state.ai.boss.level = levels.boss;
        state.ai.runner.level = levels.runner;
        
        let difficultyTime = Math.max(13, 35 - (nightNum * 5));
        state.ai.runner.timer = difficultyTime;
        state.ai.runner.baseTimer = difficultyTime;
    } else {
		console.log('Easy Night');
        // EASY MODE (Полегшення)
        // Зменшуємо рівні на 30% (або мінімум на 2 одиниці)
        const ease = (lvl) => Math.floor(lvl * 0.7);
        
        state.ai.sparky.level = ease(levels.sparky);
        state.ai.clanker.level = ease(levels.clanker);
        state.ai.boss.level = ease(levels.boss);
        state.ai.runner.level = Math.max(0, levels.runner - 2); // Бігун менш агресивний
        
        // Таймер Бігуна повільніший на 5 секунд
        let difficultyTime = Math.max(18, 35 - (nightNum * 5) + 5);
        state.ai.runner.timer = difficultyTime;
        state.ai.runner.baseTimer = difficultyTime;
    }

    // Скидаємо локації
    state.ai.sparky.location = '1A';
    state.ai.clanker.location = '1A';
    state.ai.boss.location = '1A';
    state.ai.runner.stage = 0;

    updateOfficeVisuals();

    gameInterval = setInterval(gameLoop, 1000);
    aiInterval = setInterval(aiLogic, 4000);
}

function gameLoop() {
    if (state.gameOver || !state.isPlaying) return;
    state.time += 1 / GAME_CONFIG.hourLength;

    if (state.time >= 6) {
        winNight();
        return;
    }

    let displayHour = Math.floor(state.time) === 0 ? 12 : Math.floor(state.time);
    document.getElementById('time-display').innerHTML = `${displayHour} AM <br> Night ${state.currentNight}`;

    calculateUsage();
    
    // РОЗРАХУНОК СПОЖИВАННЯ
    let baseDrain = state.hardMode ? GAME_CONFIG.baseDrainRate : 0.05; // 0.075 vs 0.05
    let currentDrain = baseDrain + (state.usage * GAME_CONFIG.usagePenalty);
    state.power -= currentDrain;

    // Оновлюємо логіку Бігуна щосекунди
    updateRunner();

    if (state.power <= 0) {
        state.power = 0;
        powerOutage();
    }
    document.getElementById('power-val').innerText = Math.floor(state.power);
}

function updateRunner() {
    if (state.ai.runner.level === 0) return;

    // --- ЛОГІКА ІНДИКАТОРІВ (НОВЕ) ---
    const officeView = document.getElementById('office-view');
    
    // Якщо стадія 3 - вмикаємо ефекти
    if (state.ai.runner.stage === 3 && state.isPlaying && !state.gameOver) {
        AudioManager.startLeftRustle();
        officeView.classList.add('flicker-warning');
    } else {
        // У всіх інших випадках (стадія 0, 1, 2, 4 або атака) - вимикаємо
        AudioManager.stopLeftRustle();
        officeView.classList.remove('flicker-warning');
    }
    // ---------------------------------

    if (state.camera.active && state.camera.current === '1C') {
        if (Math.random() > 0.7) state.ai.runner.timer += 1;
        return;
    }

    state.ai.runner.timer -= 1;

    if (state.ai.runner.timer <= 0) {
        state.ai.runner.stage++;
        
        // Звук кроку (залишаємо як було)
        if (state.ai.runner.stage <= 3) {
             AudioManager.playFootstep(-0.3); 
        }

        if (state.ai.runner.stage === 3) {
            state.ai.runner.timer = 10; 
            console.log("Runner is preparing... 10 seconds!");
            // Тут ефекти увімкнуться автоматично на наступному виклику updateRunner
        } else if (state.ai.runner.stage > 3) {
            runnerAttack();
            // Тут ефекти вимкнуться, бо стадія стане 4
        } else {
            state.ai.runner.timer = state.ai.runner.baseTimer;
        }
    }
    if (state.camera.active && state.camera.current === '1C') updateCamVisuals();
}

function calculateUsage() {
    let u = 0;
    if (state.doors.left) u++;
    if (state.doors.right) u++;
    if (state.lights.left) u++;
    if (state.lights.right) u++;
    if (state.camera.active) u++;
    state.usage = u;
    let bars = "|".repeat(u + 1);
    document.getElementById('usage-bar').innerHTML = `<span style="color:${u > 3 ? 'red' : 'green'}">${bars}</span>`;
}

function toggleDoor(side) {
    if (state.power <= 0 || isBlocked(side)) {
        AudioManager.play('error');
        return;
    }
    state.doors[side] = !state.doors[side];
    document.getElementById(`btn-door-${side.charAt(0)}`).classList.toggle('active', state.doors[side]);
    if (state.doors[side]) {
        AudioManager.play('door');
        // Штраф за двері менший в Easy Mode
        state.power -= state.hardMode ? 0.5 : 0.25;
    }
    updateOfficeVisuals();
}

function toggleLight(side, status) {
    if (state.power <= 0 || (isBlocked(side) && status)) {
        AudioManager.play('error');
        return;
    }
    state.lights[side] = status;
    document.getElementById(`btn-light-${side.charAt(0)}`).classList.toggle('active', status);
    if (status) state.power -= 0.2;
    updateOfficeVisuals();
}

function isBlocked(side) {
    return (side === 'left' && state.ai.sparky.location === 'OFFICE') || (side === 'right' && state.ai.clanker.location === 'OFFICE');
}

function toggleMonitor() {
    if (state.power <= 0 || state.gameOver) {
        if (state.camera.active) {
            state.camera.active = false;
            document.getElementById('camera-screen').classList.remove('monitor-open');
        }
        return;
    }
    
    state.camera.active = !state.camera.active;
    const camScreen = document.getElementById('camera-screen');
    
    if (state.camera.active) {
        camScreen.classList.add('monitor-open');
        state.power -= 0.5;
        updateCamVisuals();
    } else {
        camScreen.classList.remove('monitor-open');
    }
    AudioManager.play('blip');
}

function switchCam(cam) {
    if (state.camera.current !== cam) AudioManager.play('blip');
    state.camera.current = cam;
    document.querySelectorAll('.cam-btn').forEach(b => b.classList.remove('active'));
    event.target.classList.add('active');
    updateCamVisuals();
}

function aiLogic() {
    if (state.gameOver) return;

    const checkAI = (animatronicName, path, side) => {
        const anim = state.ai[animatronicName];
        let chance = anim.level;
        
		// Анти-кемпінг: +5 (було +10)
        // Це дає шанс 85% на 4-й ночі замість 110%
        if (anim.location === 'BLIND_SPOT') {
			// Якщо з моменту прибуття пройшло менше 4000 мс (4 секунди) - ІГНОРУЄМО ХІД
            if (Date.now() - anim.arrivalTime < 4000) {
                return; // Монстр гарантовано чекає
            }
            chance += 5; 
        }
		
		// --- ДОДАТИ ЦЕЙ РЯДОК ---
		// Обмежуємо шанс максимум 18 з 20 (90%)
		if (chance > 18) chance = 18; 
		// ------------------------

        if (Math.random() * 20 < chance) {
            moveAI(animatronicName, path, side);
        }
    };

    checkAI('sparky', paths.sparky, 'left');
    checkAI('clanker', paths.clanker, 'right');
    
    if (state.time > 2) {
         checkAI('boss', paths.boss, 'right');
    }

    if (state.camera.active) updateCamVisuals();
    updateOfficeVisuals();
}

function moveAI(name, path, side) {
    let curr = state.ai[name].location;
    
    // Якщо монстр вже в офісі - нічого не робимо (або чекаємо скримера)
    if (curr === 'OFFICE') {
        jumpscare(name);
        return;
    }

    // Логіка атаки (Blind Spot -> Office)
    if (curr === 'BLIND_SPOT') {
        if (state.doors[side]) {
            state.ai[name].location = path[0]; // Повертається на початок
            state.power -= state.hardMode ? 0.5 : 0.2;
            AudioManager.play('door'); // Звук удару у двері
            console.log(name + " BLOCKED");
            
            // НОВЕ: Звук швидкого відступу (трохи тихіший)
            let pan = (side === 'left') ? -0.8 : 0.8;
            AudioManager.playFootstep(pan); 
        } else {
            state.ai[name].location = 'OFFICE';
            console.log(name + " ENTERED!");
            // Тут звук не граємо, бо це "тихе проникнення" перед скримером
			// НОВЕ: Примусово опускаємо планшет, якщо він відкритий
            // Це класична фішка FNaF - монстр опускає твій планшет перед скримером
            if (state.camera.active) {
                toggleMonitor(); 
                // Блокуємо можливість відкрити його знову (можна додати прапорець state.gameOver, але jumpscare це зробить)
            }
        }
		state.ai[name].arrivalTime = 0;
        return;
    }

    // Звичайний рух по кімнатах
    let idx = path.indexOf(curr);
    if (idx === path.length - 1) {
		state.ai[name].location = 'BLIND_SPOT';
        state.ai[name].arrivalTime = Date.now(); // Записуємо час прибуття!
        state.ai[name].location = 'BLIND_SPOT';
    } else {
        state.ai[name].location = path[idx + 1];
    }

    // --- НОВА ЛОГІКА ЗВУКУ ---
    // Визначаємо панораму: 
    // Sparky (ліво) = -0.7
    // Clanker/Boss (право) = 0.7
    // Чим ближче до 1 або -1, тим сильніше звук в одному вусі.
    let panVal = (side === 'left') ? -0.7 : 0.7;

    // Boss важчий, тому його кроки можна зробити трохи гучнішими 
    // або просто грати той самий звук.
    // Якщо монстр далеко (наприклад 1A), можна було б робити звук тихішим,
    // але для геймплею краще чути все чітко.
    
    AudioManager.playFootstep(panVal);
    // -------------------------
}

function runnerAttack() {
    // Встановлюємо стадію 4 (БІГ!)
    state.ai.runner.stage = 4; 
    
    console.log("RUNNER IS COMING! 2 SECONDS!");
    
    // Якщо гравець прямо зараз дивиться камеру 2A - оновлюємо картинку миттєво
    if (state.camera.active && state.camera.current === '2A') {
        updateCamVisuals();
    }

    setTimeout(() => {
        if (state.gameOver) return;

        if (state.doors.left) {
            // Успішний захист
            state.ai.runner.stage = 0;
            state.ai.runner.timer = state.ai.runner.baseTimer;
            state.power -= state.hardMode ? 3 : 1;
            
            // Звук удару + кроки зупинки
            AudioManager.play('door');
            // Якщо у тебе вже є функція playFootstep з попереднього кроку:
            if (AudioManager.playFootstep) AudioManager.playFootstep(-0.8); 
            
            console.log("Runner blocked!");
        } else {
            // Скример
            jumpscare("Runner");
        }
    }, 2000); // 2 секунди на реакцію
}

function updateOfficeVisuals() {
    let doorL = document.getElementById('img-door-l');
    doorL.style.display = state.doors.left ? 'block' : 'none';
    doorL.style.zIndex = 10;

    let doorR = document.getElementById('img-door-r');
    doorR.style.display = state.doors.right ? 'block' : 'none';
    doorR.style.zIndex = 10;

    let l = document.getElementById('img-light-l');
    l.style.zIndex = 5;
    if (state.lights.left) {
        l.style.display = 'block';
        if (state.ai.sparky.location === 'BLIND_SPOT') {
            if (state.doors.left) {
                l.src = 'assets/light_left_closed_sparky.png';
                l.style.zIndex = 11;
            } else {
                l.src = 'assets/light_left_sparky.png';
            }
        } else {
            l.src = 'assets/light_left_on.png';
        }
    } else l.style.display = 'none';

    let r = document.getElementById('img-light-r');
    r.style.zIndex = 5;
    if (state.lights.right) {
        r.style.display = 'block';
        let monsterHere = null;
        if (state.ai.clanker.location === 'BLIND_SPOT') monsterHere = 'clanker';
        else if (state.ai.boss.location === 'BLIND_SPOT') monsterHere = 'boss';

        if (monsterHere) {
            if (state.doors.right) {
                r.src = `assets/light_right_closed_${monsterHere}.png`;
                r.style.zIndex = 11;
            } else {
                r.src = monsterHere === 'boss' ? 'assets/light_right_boss.png' : 'assets/light_right_clanker.png';
            }
        } else {
            r.src = 'assets/light_right_on.png';
        }
    } else r.style.display = 'none';
}

function updateCamVisuals() {
    const cam = state.camera.current;
    const feedImg = document.getElementById('cam-feed-img');
    document.getElementById('cam-name-overlay').innerText = "CAM " + cam;
    let filename = `cam_${cam}.png`;
    const isActive = (loc) => loc !== 'OFFICE' && loc !== 'BLIND_SPOT';

    if (cam === '1A') {
        let occ = [];
        if (isActive(state.ai.sparky.location) && state.ai.sparky.location === '1A') occ.push('sparky');
        if (isActive(state.ai.clanker.location) && state.ai.clanker.location === '1A') occ.push('clanker');
        if (isActive(state.ai.boss.location) && state.ai.boss.location === '1A') occ.push('boss');
        if (occ.length === 3) filename = 'cam_1A.png';
        else if (occ.length === 0) filename = 'cam_1A_empty.png';
        else {
            if (!occ.includes('sparky') && occ.includes('clanker')) filename = 'cam_1A_sparky.png'; 
            else if (!occ.includes('clanker') && occ.includes('sparky')) filename = 'cam_1A_clanker.png';
            else if (occ.length === 1 && occ[0] === 'boss') filename = 'cam_1A_boss.png';
            else filename = 'cam_1A_empty.png';
        }
    }
    if (cam === '1B') {
        if (state.ai.sparky.location === '1B') filename = 'cam_1B_sparky.png';
        else if (state.ai.clanker.location === '1B') filename = 'cam_1B_clanker.png';
        else if (state.ai.boss.location === '1B') filename = 'cam_1B_boss.png';
    }
	if (cam === '2A') {
        // Пріоритет 1: Бігун (Критична загроза)
        if (state.ai.runner.stage === 4) {
            filename = 'cam_2A_runner.png';
        }
        // Пріоритет 2: Спаркі
        else if (state.ai.sparky.location === '2A') {
            filename = 'cam_2A_sparky.png';
        }
        // Порожній коридор
        else {
            filename = 'cam_2A.png';
        }
    }
	if (cam === '4A') {
        // Перевіряємо, чи вони обоє там
        if (state.ai.clanker.location === '4A' && state.ai.boss.location === '4A') {
            filename = 'cam_4A_boss_clanker.png';
        } else {
            // Стандартна перевірка по одному
            if (state.ai.clanker.location === '4A') filename = 'cam_4A_clanker.png';
            if (state.ai.boss.location === '4A') filename = 'cam_4A_boss.png';
        }
    }
    if (cam === '1C') {
        let stage = Math.min(state.ai.runner.stage, 3);
        filename = `cam_1C_stage${stage}.png`;
    }
    if (cam === '6') filename = 'cam_6.png';
    feedImg.src = `assets/${filename}`;
}

function jumpscare(who) {
    state.gameOver = true;
    clearInterval(gameInterval);
    clearInterval(aiInterval);
    AudioManager.stopFanAmbience();
	AudioManager.stopLeftRustle();
    AudioManager.play('scream');
    document.getElementById('in-game-interface').classList.add('hidden');
    const jumpscareImg = document.getElementById('jumpscare-img');
    let charName = who.toLowerCase();
    const validChars = ['sparky', 'clanker', 'runner', 'boss'];
    if (!validChars.includes(charName)) charName = 'boss';
    jumpscareImg.src = `assets/jumpscare_${charName}.png`;
    document.getElementById('jumpscare-screen').classList.remove('hidden');
    setTimeout(() => location.reload(), 5000);
}

function powerOutage() {
    state.gameOver = true;
	// --- ДОДАТИ ЦЕ ---
    if (state.camera.active) {
        state.camera.active = false;
        document.getElementById('camera-screen').classList.remove('monitor-open');
    }
    // -----------------
    document.getElementById('office-view').style.background = '#000';
    document.querySelectorAll('.office-layer').forEach(el => el.style.display = 'none');
    AudioManager.stopFanAmbience();
	AudioManager.stopLeftRustle();
    setTimeout(() => jumpscare("Boss"), 6000);
}

function winNight() {
    state.gameOver = true;
    clearInterval(gameInterval);
    clearInterval(aiInterval);
    AudioManager.stopFanAmbience();
	AudioManager.stopLeftRustle();
    AudioManager.play('win');
    let transition = document.getElementById('night-transition');
    document.getElementById('transition-time').innerText = "6:00 AM";
    document.getElementById('transition-night').innerText = "YAY!";
    transition.classList.remove('hidden');
    document.getElementById('in-game-interface').classList.add('hidden');
    const nextNight = state.currentNight + 1;
    localStorage.setItem('fnaf_night', nextNight);
    setTimeout(() => {
        if (nextNight <= 5) {
            startSelected(nextNight);
        } else {
            alert("YOU COMPLETED ALL 5 NIGHTS! GOOD JOB!");
            localStorage.setItem('fnaf_night', 1);
            location.reload();
        }
    }, 6000);
}