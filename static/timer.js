/**
 * Pomodoro Timer JavaScript
 * Handles timer logic, UI updates, and API communication
 */

class PomodoroTimer {
    constructor() {
        // Default settings
        this.settings = {
            focusDuration: 25 * 60, // 25 minutes in seconds
            breakDuration: 5 * 60,  // 5 minutes in seconds
            soundStart: true,
            soundEnd: true,
            soundTick: false,
            theme: 'light'
        };
        
        // Load saved settings
        this.loadSettings();
        
        this.duration = this.settings.focusDuration;
        this.timeRemaining = this.duration;
        this.isRunning = false;
        this.isPaused = false;
        this.isBreak = false;
        this.intervalId = null;
        this.tickAudioInterval = null;
        this.particleIntervalId = null;
        
        // UI Elements
        this.timeDisplay = document.getElementById('timeRemaining');
        this.timerLabel = document.getElementById('timerLabel');
        this.startBtn = document.getElementById('startBtn');
        this.resetBtn = document.getElementById('resetBtn');
        this.progressRingBar = document.querySelector('.progress-ring-bar');
        this.sessionsCount = document.getElementById('sessionsCount');
        this.focusMinutes = document.getElementById('focusMinutes');
        this.particlesContainer = document.getElementById('particlesContainer');
        
        // Settings UI Elements
        this.settingsBtn = document.getElementById('settingsBtn');
        this.settingsPanel = document.getElementById('settingsPanel');
        this.closeSettingsBtn = document.getElementById('closeSettings');
        this.themeBtn = document.getElementById('themeBtn');
        this.focusDurationSelect = document.getElementById('focusDuration');
        this.breakDurationSelect = document.getElementById('breakDuration');
        this.soundStartCheckbox = document.getElementById('soundStart');
        this.soundEndCheckbox = document.getElementById('soundEnd');
        this.soundTickCheckbox = document.getElementById('soundTick');
        
        // Progress ring calculations
        this.radius = 90;
        this.circumference = 2 * Math.PI * this.radius;
        
        // Initialize audio contexts
        this.initializeAudio();
        
        this.initializeEventListeners();
        this.applySavedSettings();
        this.updateUI();
        this.loadTodayProgress();
    }
    
    initializeAudio() {
        // Create audio context for generating beep sounds
        this.audioContext = null;
        if (typeof AudioContext !== 'undefined' || typeof webkitAudioContext !== 'undefined') {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        }
    }
    
    playSound(type) {
        if (!this.audioContext) return;
        
        const settings = {
            start: { enabled: this.settings.soundStart, frequency: 800, duration: 0.1 },
            end: { enabled: this.settings.soundEnd, frequency: 600, duration: 0.3 },
            tick: { enabled: this.settings.soundTick, frequency: 400, duration: 0.05 }
        };
        
        const sound = settings[type];
        if (!sound || !sound.enabled) return;
        
        try {
            const oscillator = this.audioContext.createOscillator();
            const gainNode = this.audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(this.audioContext.destination);
            
            oscillator.frequency.value = sound.frequency;
            oscillator.type = 'sine';
            
            gainNode.gain.setValueAtTime(0.3, this.audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + sound.duration);
            
            oscillator.start(this.audioContext.currentTime);
            oscillator.stop(this.audioContext.currentTime + sound.duration);
        } catch (error) {
            console.error('Error playing sound:', error);
        }
    }
    
    loadSettings() {
        try {
            const saved = localStorage.getItem('pomodoroSettings');
            if (saved) {
                const parsed = JSON.parse(saved);
                this.settings = { ...this.settings, ...parsed };
            }
        } catch (error) {
            console.error('Error loading settings:', error);
        }
    }
    
    saveSettings() {
        try {
            localStorage.setItem('pomodoroSettings', JSON.stringify(this.settings));
        } catch (error) {
            console.error('Error saving settings:', error);
        }
    }
    
    applySavedSettings() {
        // Apply theme
        document.body.className = '';
        if (this.settings.theme !== 'light') {
            document.body.classList.add(`theme-${this.settings.theme}`);
        }
        
        // Set UI values
        this.focusDurationSelect.value = this.settings.focusDuration.toString();
        this.breakDurationSelect.value = this.settings.breakDuration.toString();
        this.soundStartCheckbox.checked = this.settings.soundStart;
        this.soundEndCheckbox.checked = this.settings.soundEnd;
        this.soundTickCheckbox.checked = this.settings.soundTick;
    }
    
    initializeEventListeners() {
        this.startBtn.addEventListener('click', () => this.toggleTimer());
        this.resetBtn.addEventListener('click', () => this.resetTimer());
        
        // Settings panel
        this.settingsBtn.addEventListener('click', () => this.toggleSettings());
        this.closeSettingsBtn.addEventListener('click', () => this.toggleSettings());
        
        // Theme button
        this.themeBtn.addEventListener('click', () => this.cycleTheme());
        
        // Settings changes
        this.focusDurationSelect.addEventListener('change', (e) => {
            this.settings.focusDuration = parseInt(e.target.value);
            this.saveSettings();
            if (!this.isBreak && !this.isRunning) {
                this.duration = this.settings.focusDuration;
                this.timeRemaining = this.duration;
                this.updateUI();
            }
        });
        
        this.breakDurationSelect.addEventListener('change', (e) => {
            this.settings.breakDuration = parseInt(e.target.value);
            this.saveSettings();
        });
        
        this.soundStartCheckbox.addEventListener('change', (e) => {
            this.settings.soundStart = e.target.checked;
            this.saveSettings();
        });
        
        this.soundEndCheckbox.addEventListener('change', (e) => {
            this.settings.soundEnd = e.target.checked;
            this.saveSettings();
        });
        
        this.soundTickCheckbox.addEventListener('change', (e) => {
            this.settings.soundTick = e.target.checked;
            this.saveSettings();
        });
    }
    
    toggleSettings() {
        this.settingsPanel.classList.toggle('hidden');
    }
    
    cycleTheme() {
        const themes = ['light', 'dark', 'focus'];
        const currentIndex = themes.indexOf(this.settings.theme);
        const nextIndex = (currentIndex + 1) % themes.length;
        this.settings.theme = themes[nextIndex];
        this.saveSettings();
        this.applySavedSettings();
    }
    
    toggleTimer() {
        if (this.isRunning) {
            this.pauseTimer();
        } else {
            this.startTimer();
        }
    }
    
    startTimer() {
        this.isRunning = true;
        this.isPaused = false;
        this.startBtn.textContent = 'Pause';
        this.startBtn.classList.add('timer-running');
        document.body.classList.add('timer-running');
        
        // Play start sound
        this.playSound('start');
        
        // Start ticking sound interval if enabled
        if (this.settings.soundTick) {
            this.tickAudioInterval = setInterval(() => {
                this.playSound('tick');
            }, 1000);
        }
        
        // Start particle effects
        this.startParticles();
        
        this.intervalId = setInterval(() => {
            this.timeRemaining--;
            this.updateUI();
            
            if (this.timeRemaining <= 0) {
                this.completeTimer();
            }
        }, 1000);
    }
    
    pauseTimer() {
        this.isRunning = false;
        this.isPaused = true;
        this.startBtn.textContent = 'Resume';
        this.startBtn.classList.remove('timer-running');
        document.body.classList.remove('timer-running');
        
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
        
        if (this.tickAudioInterval) {
            clearInterval(this.tickAudioInterval);
            this.tickAudioInterval = null;
        }
        
        // Stop particle effects
        this.stopParticles();
    }
    
    resetTimer() {
        this.isRunning = false;
        this.isPaused = false;
        
        // Reset to appropriate duration based on current mode
        if (this.isBreak) {
            this.isBreak = false;
            this.duration = this.settings.focusDuration;
            this.timerLabel.textContent = 'Focus Time';
        } else {
            this.duration = this.settings.focusDuration;
        }
        
        this.timeRemaining = this.duration;
        this.startBtn.textContent = 'Start';
        this.startBtn.classList.remove('timer-running');
        document.body.classList.remove('timer-running', 'timer-completed');
        
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
        
        if (this.tickAudioInterval) {
            clearInterval(this.tickAudioInterval);
            this.tickAudioInterval = null;
        }
        
        // Stop particle effects
        this.stopParticles();
        
        this.updateUI();
    }
    
    completeTimer() {
        this.isRunning = false;
        this.timeRemaining = 0;
        this.startBtn.textContent = 'Start';
        this.startBtn.classList.remove('timer-running');
        document.body.classList.remove('timer-running');
        document.body.classList.add('timer-completed');
        
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
        
        if (this.tickAudioInterval) {
            clearInterval(this.tickAudioInterval);
            this.tickAudioInterval = null;
        }
        
        // Stop particle effects
        this.stopParticles();
        
        // Play completion sound
        this.playSound('end');
        
        this.updateUI();
        
        // Log session only if it was a focus session (not a break)
        if (!this.isBreak) {
            this.logSession();
        }
        
        // Show completion notification
        this.showCompletionMessage();
        
        // Switch to break mode or back to focus
        setTimeout(() => {
            if (!this.isBreak) {
                // Start a break
                this.isBreak = true;
                this.duration = this.settings.breakDuration;
                this.timerLabel.textContent = 'Break Time';
            } else {
                // Return to focus
                this.isBreak = false;
                this.duration = this.settings.focusDuration;
                this.timerLabel.textContent = 'Focus Time';
            }
            this.resetTimer();
        }, 3000);
    }
    
    updateUI() {
        // Update time display
        const minutes = Math.floor(this.timeRemaining / 60);
        const seconds = this.timeRemaining % 60;
        this.timeDisplay.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        
        // Update progress ring
        const progress = (this.duration - this.timeRemaining) / this.duration;
        const offset = this.circumference - (progress * this.circumference);
        this.progressRingBar.style.strokeDashoffset = offset;
    }
    
    formatTime(seconds) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
    }
    
    async logSession() {
        try {
            const response = await fetch('/api/session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    timestamp: new Date().toISOString(),
                    duration: this.duration
                })
            });
            
            if (response.ok) {
                console.log('Session logged successfully');
                this.loadTodayProgress();
            } else {
                console.error('Failed to log session');
            }
        } catch (error) {
            console.error('Error logging session:', error);
        }
    }
    
    async loadTodayProgress() {
        try {
            const response = await fetch('/api/progress');
            if (response.ok) {
                const progress = await response.json();
                this.sessionsCount.textContent = progress.count || 0;
                this.focusMinutes.textContent = progress.minutes || 0;
            } else {
                console.error('Failed to load progress');
            }
        } catch (error) {
            console.error('Error loading progress:', error);
        }
    }
    
    showCompletionMessage() {
        const message = this.isBreak ? 'Break completed! Ready to focus?' : 'Pomodoro completed! Time for a break!';
        console.log(message);
        
        // Simple alert for now - can be enhanced with better UI
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification(this.isBreak ? 'Break Completed!' : 'Pomodoro Completed!', {
                body: message,
                icon: '/static/favicon.ico'
            });
        }
    }
    
    startParticles() {
        // Generate particles periodically
        this.particleIntervalId = setInterval(() => {
            this.createParticle();
        }, 200); // Create a new particle every 200ms
    }
    
    stopParticles() {
        if (this.particleIntervalId) {
            clearInterval(this.particleIntervalId);
            this.particleIntervalId = null;
        }
        // Clear existing particles
        if (this.particlesContainer) {
            this.particlesContainer.innerHTML = '';
        }
    }
    
    createParticle() {
        if (!this.particlesContainer) return;
        
        const particle = document.createElement('div');
        particle.className = 'particle';
        
        // Random position
        particle.style.left = Math.random() * 100 + '%';
        
        // Random animation duration
        const duration = 4 + Math.random() * 4; // 4-8 seconds
        particle.style.animationDuration = duration + 's';
        
        // Random size
        const size = 2 + Math.random() * 4; // 2-6px
        particle.style.width = size + 'px';
        particle.style.height = size + 'px';
        
        this.particlesContainer.appendChild(particle);
        
        // Remove particle after animation completes
        setTimeout(() => {
            particle.remove();
        }, duration * 1000);
    }
}

// Initialize timer when page loads
document.addEventListener('DOMContentLoaded', () => {
    const timer = new PomodoroTimer();
    
    // Request notification permission
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }
});

// Export for testing purposes (if needed)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PomodoroTimer;
}
