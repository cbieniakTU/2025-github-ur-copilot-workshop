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
        
        // UI Elements
        this.timeDisplay = document.getElementById('timeRemaining');
        this.startBtn = document.getElementById('startBtn');
        this.resetBtn = document.getElementById('resetBtn');
        this.progressRingBar = document.querySelector('.progress-ring-bar');
        this.sessionsCount = document.getElementById('sessionsCount');
        this.focusMinutes = document.getElementById('focusMinutes');
        
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
    }
    
    resetTimer() {
        this.isRunning = false;
        this.isPaused = false;
        this.timeRemaining = this.duration;
        this.startBtn.textContent = 'Start';
        this.startBtn.classList.remove('timer-running');
        document.body.classList.remove('timer-running', 'timer-completed');
        
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