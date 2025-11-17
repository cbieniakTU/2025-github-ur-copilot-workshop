/**
 * Pomodoro Timer JavaScript
 * Handles timer logic, UI updates, and API communication
 */

class PomodoroTimer {
    constructor() {
        this.duration = 25 * 60; // 25 minutes in seconds
        this.timeRemaining = this.duration;
        this.isRunning = false;
        this.isPaused = false;
        this.intervalId = null;
        this.particleIntervalId = null;
        
        // UI Elements
        this.timeDisplay = document.getElementById('timeRemaining');
        this.startBtn = document.getElementById('startBtn');
        this.resetBtn = document.getElementById('resetBtn');
        this.progressRingBar = document.querySelector('.progress-ring-bar');
        this.sessionsCount = document.getElementById('sessionsCount');
        this.focusMinutes = document.getElementById('focusMinutes');
        this.particlesContainer = document.getElementById('particlesContainer');
        
        // Progress ring calculations
        this.radius = 90;
        this.circumference = 2 * Math.PI * this.radius;
        
        this.initializeEventListeners();
        this.updateUI();
        this.loadTodayProgress();
    }
    
    initializeEventListeners() {
        this.startBtn.addEventListener('click', () => this.toggleTimer());
        this.resetBtn.addEventListener('click', () => this.resetTimer());
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
        
        // Start particle generation
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
        
        // Stop particle generation
        this.stopParticles();
        
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    }
    
    resetTimer() {
        this.isRunning = false;
        this.isPaused = false;
        this.timeRemaining = this.duration;
        this.startBtn.textContent = 'Start';
        this.startBtn.classList.remove('timer-running');
        document.body.classList.remove('timer-running', 'timer-completed');
        
        // Stop particle generation
        this.stopParticles();
        
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
        
        this.updateUI();
    }
    
    completeTimer() {
        this.isRunning = false;
        this.timeRemaining = 0;
        this.startBtn.textContent = 'Start';
        this.startBtn.classList.remove('timer-running');
        document.body.classList.remove('timer-running');
        document.body.classList.add('timer-completed');
        
        // Stop particle generation
        this.stopParticles();
        
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
        
        this.updateUI();
        this.logSession();
        
        // Show completion notification
        this.showCompletionMessage();
        
        // Auto-reset after a brief delay
        setTimeout(() => {
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
        
        // Update color based on time remaining (smooth gradient transition)
        // Blue (100%-67%) → Yellow (66%-34%) → Red (33%-0%)
        const percentRemaining = (this.timeRemaining / this.duration) * 100;
        let color;
        
        if (percentRemaining > 67) {
            // Blue phase (start of session)
            color = '#4a90e2'; // Blue
        } else if (percentRemaining > 34) {
            // Transition from blue to yellow
            const transitionProgress = (67 - percentRemaining) / 33;
            color = this.interpolateColor('#4a90e2', '#f5a623', transitionProgress);
        } else {
            // Transition from yellow to red
            const transitionProgress = (34 - percentRemaining) / 34;
            color = this.interpolateColor('#f5a623', '#e74c3c', transitionProgress);
        }
        
        this.progressRingBar.style.stroke = color;
    }
    
    interpolateColor(color1, color2, factor) {
        // Parse hex colors
        const c1 = {
            r: parseInt(color1.slice(1, 3), 16),
            g: parseInt(color1.slice(3, 5), 16),
            b: parseInt(color1.slice(5, 7), 16)
        };
        const c2 = {
            r: parseInt(color2.slice(1, 3), 16),
            g: parseInt(color2.slice(3, 5), 16),
            b: parseInt(color2.slice(5, 7), 16)
        };
        
        // Interpolate
        const r = Math.round(c1.r + (c2.r - c1.r) * factor);
        const g = Math.round(c1.g + (c2.g - c1.g) * factor);
        const b = Math.round(c1.b + (c2.b - c1.b) * factor);
        
        // Convert back to hex
        return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
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
        this.particlesContainer.innerHTML = '';
    }
    
    createParticle() {
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
        // You could add a toast notification or modal here
        console.log('Pomodoro session completed!');
        
        // Simple alert for now - can be enhanced with better UI
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification('Pomodoro Completed!', {
                body: 'Great job! Take a short break.',
                icon: '/static/favicon.ico'
            });
        }
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