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
        
        // Gamification manager
        this.gamificationManager = null;
        
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
                const data = await response.json();
                
                // Update progress
                this.loadTodayProgress();
                
                // Handle gamification updates
                if (this.gamificationManager && data.gamification) {
                    this.gamificationManager.handleSessionComplete(data.gamification);
                }
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


/**
 * Gamification Manager
 * Handles XP, levels, achievements, streaks, and statistics
 */
class GamificationManager {
    constructor() {
        // UI Elements
        this.levelNumber = document.getElementById('levelNumber');
        this.currentXP = document.getElementById('currentXP');
        this.nextLevelXP = document.getElementById('nextLevelXP');
        this.xpBar = document.getElementById('xpBar');
        this.streakCount = document.getElementById('streakCount');
        this.longestStreak = document.getElementById('longestStreak');
        this.achievementsGrid = document.getElementById('achievementsGrid');
        
        // Stats elements
        this.statTotal = document.getElementById('statTotal');
        this.statAverage = document.getElementById('statAverage');
        this.statCompletionRate = document.getElementById('statCompletionRate');
        this.statsChart = document.getElementById('statsChart');
        
        // Modals
        this.achievementModal = document.getElementById('achievementModal');
        this.levelUpModal = document.getElementById('levelUpModal');
        
        // Current stats period
        this.currentPeriod = 'weekly';
        
        this.initializeEventListeners();
        this.loadGamificationData();
        this.loadStats();
    }
    
    initializeEventListeners() {
        // Stats tabs
        const statsTabs = document.querySelectorAll('.stats-tab');
        statsTabs.forEach(tab => {
            tab.addEventListener('click', (e) => {
                statsTabs.forEach(t => t.classList.remove('active'));
                e.target.classList.add('active');
                this.currentPeriod = e.target.dataset.period;
                this.loadStats();
            });
        });
        
        // Close modals on click
        [this.achievementModal, this.levelUpModal].forEach(modal => {
            if (modal) {
                modal.addEventListener('click', () => {
                    modal.classList.remove('show');
                });
            }
        });
    }
    
    async loadGamificationData() {
        try {
            const response = await fetch('/api/gamification');
            if (response.ok) {
                const data = await response.json();
                this.updateGamificationUI(data);
            }
        } catch (error) {
            console.error('Error loading gamification data:', error);
        }
    }
    
    updateGamificationUI(data) {
        // Update level and XP
        this.levelNumber.textContent = data.level;
        this.currentXP.textContent = data.xp;
        this.nextLevelXP.textContent = data.xp_needed + data.xp_progress;
        this.xpBar.style.width = `${data.xp_percentage}%`;
        
        // Update streak
        this.streakCount.textContent = data.current_streak;
        this.longestStreak.textContent = data.longest_streak;
        
        // Update achievements
        this.renderAchievements(data.achievements);
    }
    
    renderAchievements(achievements) {
        this.achievementsGrid.innerHTML = '';
        
        achievements.forEach(achievement => {
            const card = document.createElement('div');
            card.className = `achievement-card ${achievement.unlocked ? 'unlocked' : 'locked'}`;
            card.innerHTML = `
                <div class="achievement-icon">${achievement.icon}</div>
                <div class="achievement-name">${achievement.name}</div>
                <div class="achievement-description">${achievement.description}</div>
            `;
            
            // Add tooltip on hover
            card.title = achievement.description;
            
            this.achievementsGrid.appendChild(card);
        });
    }
    
    async loadStats() {
        try {
            const response = await fetch('/api/stats');
            if (response.ok) {
                const data = await response.json();
                this.updateStatsUI(data);
            }
        } catch (error) {
            console.error('Error loading stats:', error);
        }
    }
    
    updateStatsUI(data) {
        const periodData = data[this.currentPeriod];
        
        // Update stats values
        this.statTotal.textContent = periodData.total;
        this.statAverage.textContent = periodData.average.toFixed(1);
        this.statCompletionRate.textContent = `${periodData.completion_rate.toFixed(0)}%`;
        
        // Draw chart
        this.drawChart(periodData.data);
    }
    
    drawChart(data) {
        const canvas = this.statsChart;
        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;
        
        // Clear canvas
        ctx.clearRect(0, 0, width, height);
        
        // Convert data to array
        const dates = Object.keys(data).sort();
        const values = dates.map(date => data[date]);
        const maxValue = Math.max(...values, 1);
        
        // Draw bars
        const barWidth = width / dates.length;
        const padding = 2;
        
        values.forEach((value, index) => {
            const barHeight = (value / maxValue) * (height - 20);
            const x = index * barWidth + padding;
            const y = height - barHeight - 10;
            
            // Draw bar
            const gradient = ctx.createLinearGradient(0, y, 0, height);
            gradient.addColorStop(0, '#667eea');
            gradient.addColorStop(1, '#764ba2');
            
            ctx.fillStyle = gradient;
            ctx.fillRect(x, y, barWidth - padding * 2, barHeight);
            
            // Draw value on top if > 0
            if (value > 0) {
                ctx.fillStyle = '#333';
                ctx.font = '10px sans-serif';
                ctx.textAlign = 'center';
                ctx.fillText(value, x + (barWidth - padding * 2) / 2, y - 5);
            }
        });
    }
    
    handleSessionComplete(gamificationData) {
        // Reload gamification data
        this.loadGamificationData();
        this.loadStats();
        
        // Show level up modal if leveled up
        if (gamificationData.leveled_up) {
            this.showLevelUpModal(gamificationData.level);
        }
        
        // Show achievement modal if new achievements
        if (gamificationData.new_achievements && gamificationData.new_achievements.length > 0) {
            this.showAchievementModal(gamificationData.new_achievements);
        }
    }
    
    showLevelUpModal(level) {
        const details = document.getElementById('levelUpDetails');
        details.innerHTML = `
            <p style="font-size: 3rem; margin: 1rem 0;">🎊</p>
            <p style="font-size: 2rem; font-weight: bold;">Level ${level}</p>
            <p style="margin-top: 1rem;">Keep up the great work!</p>
        `;
        
        this.levelUpModal.classList.add('show');
        
        // Auto-close after 3 seconds
        setTimeout(() => {
            this.levelUpModal.classList.remove('show');
        }, 3000);
    }
    
    showAchievementModal(achievements) {
        const details = document.getElementById('achievementDetails');
        
        const achievementHTML = achievements.map(ach => `
            <div style="margin: 1rem 0;">
                <div style="font-size: 3rem;">${ach.icon}</div>
                <div style="font-size: 1.5rem; font-weight: bold; margin-top: 0.5rem;">${ach.name}</div>
                <div style="font-size: 1rem; margin-top: 0.5rem;">${ach.description}</div>
            </div>
        `).join('');
        
        details.innerHTML = achievementHTML;
        
        this.achievementModal.classList.add('show');
        
        // Auto-close after 4 seconds
        setTimeout(() => {
            this.achievementModal.classList.remove('show');
        }, 4000);
    }
}


// Initialize timer when page loads
document.addEventListener('DOMContentLoaded', () => {
    const timer = new PomodoroTimer();
    const gamification = new GamificationManager();
    
    // Connect timer with gamification
    timer.gamificationManager = gamification;
    
    // Request notification permission
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }
});

// Export for testing purposes (if needed)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PomodoroTimer;
}