"""
Pomodoro Timer Flask Application

A simple web application for managing Pomodoro timer sessions.
Provides a web interface and REST API for session tracking.
"""

from flask import Flask, render_template, request, jsonify
import os
import json
from datetime import datetime, date, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# App configuration
app.config['DEBUG'] = True
app.config['JSON_SORT_KEYS'] = False

# Session storage file
POMODORO_LOG_FILE = 'pomodoro.log'
GAMIFICATION_DATA_FILE = 'gamification.json'


class SessionLogger:
    """Handles reading and writing Pomodoro session data to a log file."""
    
    def __init__(self, log_file=POMODORO_LOG_FILE):
        self.log_file = log_file
    
    def log_session(self, timestamp=None, duration=1500):
        """
        Log a completed Pomodoro session.
        
        Args:
            timestamp: ISO format timestamp (defaults to current time)
            duration: Session duration in seconds (default: 25 minutes)
        """
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        session_data = {
            'timestamp': timestamp,
            'duration': duration,
            'date': datetime.fromisoformat(timestamp).date().isoformat()
        }
        
        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(session_data) + '\n')
            logger.info(f"Session logged: {session_data}")
        except Exception as e:
            logger.error(f"Failed to log session: {e}")
            raise
    
    def get_today_progress(self):
        """
        Get today's progress statistics.
        
        Returns:
            dict: {'count': int, 'minutes': int}
        """
        today = date.today().isoformat()
        count = 0
        total_minutes = 0
        
        if not os.path.exists(self.log_file):
            return {'count': 0, 'minutes': 0}
        
        try:
            with open(self.log_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        session = json.loads(line)
                        if session.get('date') == today:
                            count += 1
                            total_minutes += session.get('duration', 1500) // 60
        except Exception as e:
            logger.error(f"Failed to read progress: {e}")
            return {'count': 0, 'minutes': 0}
        
        return {'count': count, 'minutes': total_minutes}
    
    def get_all_sessions(self):
        """
        Get all sessions from the log file.
        
        Returns:
            list: List of session dictionaries
        """
        sessions = []
        
        if not os.path.exists(self.log_file):
            return sessions
        
        try:
            with open(self.log_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        sessions.append(json.loads(line))
        except Exception as e:
            logger.error(f"Failed to read sessions: {e}")
            
        return sessions


class GamificationManager:
    """Handles gamification features: XP, levels, achievements, and streaks."""
    
    # XP required for each level (exponential growth)
    # Index represents the level (level 1 = 0 XP, level 2 = 100 XP, etc.)
    XP_PER_LEVEL = [0, 100, 250, 450, 700, 1000, 1350, 1750, 2200, 2700, 3250]
    
    # XP rewards
    XP_PER_SESSION = 25
    
    # Achievement definitions
    ACHIEVEMENTS = {
        'first_session': {
            'name': 'First Steps',
            'description': 'Complete your first Pomodoro session',
            'icon': '🎯'
        },
        'streak_3': {
            'name': '3-Day Warrior',
            'description': 'Complete sessions for 3 consecutive days',
            'icon': '🔥'
        },
        'streak_7': {
            'name': 'Week Champion',
            'description': 'Complete sessions for 7 consecutive days',
            'icon': '⭐'
        },
        'week_10': {
            'name': 'Weekly Master',
            'description': 'Complete 10 Pomodoros in a week',
            'icon': '💪'
        },
        'week_25': {
            'name': 'Focus Legend',
            'description': 'Complete 25 Pomodoros in a week',
            'icon': '👑'
        },
        'total_50': {
            'name': 'Half Century',
            'description': 'Complete 50 total Pomodoros',
            'icon': '🎖️'
        },
        'total_100': {
            'name': 'Century Club',
            'description': 'Complete 100 total Pomodoros',
            'icon': '🏆'
        }
    }
    
    def __init__(self, data_file=GAMIFICATION_DATA_FILE, session_logger=None):
        self.data_file = data_file
        self.session_logger = session_logger
        self.data = self._load_data()
    
    def _load_data(self):
        """Load gamification data from file."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load gamification data: {e}")
        
        # Default data structure
        return {
            'xp': 0,
            'level': 1,
            'achievements': [],
            'last_session_date': None,
            'current_streak': 0,
            'longest_streak': 0
        }
    
    def _save_data(self):
        """Save gamification data to file."""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save gamification data: {e}")
            raise
    
    def get_level_from_xp(self, xp):
        """Calculate level from XP."""
        # Find the highest level where XP requirement is met
        level = 1
        for i in range(1, len(self.XP_PER_LEVEL)):
            if xp >= self.XP_PER_LEVEL[i]:
                level = i + 1
            else:
                break
        return level
    
    def get_xp_for_next_level(self, current_level):
        """Get XP required for next level."""
        if current_level >= len(self.XP_PER_LEVEL):
            return self.XP_PER_LEVEL[-1] + 500  # Cap at max level
        return self.XP_PER_LEVEL[current_level]
    
    def add_session_xp(self):
        """Add XP for completing a session and check for level up."""
        old_level = self.data['level']
        self.data['xp'] += self.XP_PER_SESSION
        new_level = self.get_level_from_xp(self.data['xp'])
        self.data['level'] = new_level
        
        leveled_up = new_level > old_level
        self._save_data()
        
        return {
            'xp_gained': self.XP_PER_SESSION,
            'total_xp': self.data['xp'],
            'level': new_level,
            'leveled_up': leveled_up
        }
    
    def update_streak(self, session_date):
        """Update the streak counter based on session date."""
        if isinstance(session_date, str):
            session_date = datetime.fromisoformat(session_date).date()
        
        last_date = self.data.get('last_session_date')
        
        if last_date is None:
            # First session ever
            self.data['current_streak'] = 1
            self.data['last_session_date'] = session_date.isoformat()
        else:
            if isinstance(last_date, str):
                last_date = datetime.fromisoformat(last_date).date()
            
            days_diff = (session_date - last_date).days
            
            if days_diff == 0:
                # Same day, no change
                pass
            elif days_diff == 1:
                # Consecutive day
                self.data['current_streak'] += 1
            else:
                # Streak broken
                self.data['current_streak'] = 1
            
            self.data['last_session_date'] = session_date.isoformat()
        
        # Update longest streak
        if self.data['current_streak'] > self.data['longest_streak']:
            self.data['longest_streak'] = self.data['current_streak']
        
        self._save_data()
    
    def check_achievements(self):
        """Check and unlock new achievements."""
        if not self.session_logger:
            return []
        
        sessions = self.session_logger.get_all_sessions()
        total_sessions = len(sessions)
        newly_unlocked = []
        
        # Get weekly sessions
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        weekly_sessions = [s for s in sessions if datetime.fromisoformat(s['timestamp']).date() >= week_start]
        weekly_count = len(weekly_sessions)
        
        # Achievement conditions
        achievements_to_check = {
            'first_session': total_sessions >= 1,
            'streak_3': self.data['current_streak'] >= 3,
            'streak_7': self.data['current_streak'] >= 7,
            'week_10': weekly_count >= 10,
            'week_25': weekly_count >= 25,
            'total_50': total_sessions >= 50,
            'total_100': total_sessions >= 100
        }
        
        for achievement_id, condition in achievements_to_check.items():
            if condition and achievement_id not in self.data['achievements']:
                self.data['achievements'].append(achievement_id)
                newly_unlocked.append({
                    'id': achievement_id,
                    **self.ACHIEVEMENTS[achievement_id]
                })
        
        if newly_unlocked:
            self._save_data()
        
        return newly_unlocked
    
    def get_stats(self):
        """Get statistics for weekly/monthly view."""
        if not self.session_logger:
            return {}
        
        sessions = self.session_logger.get_all_sessions()
        today = date.today()
        
        # Weekly stats (last 7 days)
        weekly_data = {}
        for i in range(7):
            day = today - timedelta(days=i)
            weekly_data[day.isoformat()] = 0
        
        # Monthly stats (last 30 days)
        monthly_data = {}
        for i in range(30):
            day = today - timedelta(days=i)
            monthly_data[day.isoformat()] = 0
        
        # Count sessions per day
        for session in sessions:
            session_date = datetime.fromisoformat(session['timestamp']).date().isoformat()
            if session_date in weekly_data:
                weekly_data[session_date] += 1
            if session_date in monthly_data:
                monthly_data[session_date] += 1
        
        # Calculate averages
        weekly_sessions = list(weekly_data.values())
        monthly_sessions = list(monthly_data.values())
        
        return {
            'weekly': {
                'data': weekly_data,
                'total': sum(weekly_sessions),
                'average': sum(weekly_sessions) / len(weekly_sessions) if weekly_sessions else 0,
                'completion_rate': (sum(1 for x in weekly_sessions if x > 0) / len(weekly_sessions) * 100) if weekly_sessions else 0
            },
            'monthly': {
                'data': monthly_data,
                'total': sum(monthly_sessions),
                'average': sum(monthly_sessions) / len(monthly_sessions) if monthly_sessions else 0,
                'completion_rate': (sum(1 for x in monthly_sessions if x > 0) / len(monthly_sessions) * 100) if monthly_sessions else 0
            }
        }
    
    def get_gamification_data(self):
        """Get all gamification data for display."""
        xp_for_next = self.get_xp_for_next_level(self.data['level'])
        xp_for_current = self.get_xp_for_next_level(self.data['level'] - 1) if self.data['level'] > 1 else 0
        xp_progress = self.data['xp'] - xp_for_current
        xp_needed = xp_for_next - xp_for_current
        
        unlocked_achievements = [
            {'id': aid, **self.ACHIEVEMENTS[aid]}
            for aid in self.data['achievements']
        ]
        
        all_achievements = [
            {
                'id': aid,
                'unlocked': aid in self.data['achievements'],
                **achievement_data
            }
            for aid, achievement_data in self.ACHIEVEMENTS.items()
        ]
        
        return {
            'xp': self.data['xp'],
            'level': self.data['level'],
            'xp_progress': xp_progress,
            'xp_needed': xp_needed,
            'xp_percentage': (xp_progress / xp_needed * 100) if xp_needed > 0 else 0,
            'current_streak': self.data['current_streak'],
            'longest_streak': self.data['longest_streak'],
            'achievements': all_achievements,
            'unlocked_achievements': unlocked_achievements,
            'total_achievements': len(self.ACHIEVEMENTS),
            'unlocked_count': len(self.data['achievements'])
        }


# Initialize session logger
session_logger = SessionLogger()

# Initialize gamification manager
gamification_manager = GamificationManager(session_logger=session_logger)


@app.route('/')
def index():
    """Serve the main Pomodoro timer page."""
    return render_template('index.html')


@app.route('/api/session', methods=['POST'])
def log_session():
    """
    API endpoint to log a completed Pomodoro session.
    
    Expected JSON payload:
    {
        "timestamp": "2024-01-01T12:00:00" (optional, defaults to current time),
        "duration": 1500 (optional, defaults to 25 minutes in seconds)
    }
    """
    try:
        data = request.get_json(silent=True)
        if not data:
            data = {}
        
        timestamp = data.get('timestamp')
        duration = data.get('duration', 1500)
        
        # Validate duration
        if not isinstance(duration, int) or duration < 30:
            return jsonify({'error': 'Duration must be at least 30 seconds'}), 400
        
        session_logger.log_session(timestamp, duration)
        
        # Update gamification data
        if timestamp:
            session_date = datetime.fromisoformat(timestamp).date()
        else:
            session_date = date.today()
        
        xp_result = gamification_manager.add_session_xp()
        gamification_manager.update_streak(session_date)
        new_achievements = gamification_manager.check_achievements()
        
        return jsonify({
            'success': True,
            'message': 'Session logged successfully',
            'gamification': {
                'xp_gained': xp_result['xp_gained'],
                'total_xp': xp_result['total_xp'],
                'level': xp_result['level'],
                'leveled_up': xp_result['leveled_up'],
                'new_achievements': new_achievements
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error logging session: {e}")
        return jsonify({'error': 'Failed to log session'}), 500


@app.route('/api/progress', methods=['GET'])
def get_progress():
    """
    API endpoint to get today's progress statistics.
    
    Returns:
    {
        "count": 3,        # Number of completed sessions today
        "minutes": 75      # Total focus minutes today
    }
    """
    try:
        progress = session_logger.get_today_progress()
        return jsonify(progress)
    except Exception as e:
        logger.error(f"Error getting progress: {e}")
        return jsonify({'error': 'Failed to get progress'}), 500


@app.route('/api/gamification', methods=['GET'])
def get_gamification():
    """
    API endpoint to get gamification data (XP, level, achievements, streak).
    
    Returns:
    {
        "xp": 250,
        "level": 3,
        "xp_progress": 50,
        "xp_needed": 200,
        "xp_percentage": 25,
        "current_streak": 5,
        "longest_streak": 7,
        "achievements": [...],
        "unlocked_achievements": [...]
    }
    """
    try:
        gamification_data = gamification_manager.get_gamification_data()
        return jsonify(gamification_data)
    except Exception as e:
        logger.error(f"Error getting gamification data: {e}")
        return jsonify({'error': 'Failed to get gamification data'}), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """
    API endpoint to get weekly/monthly statistics.
    
    Returns:
    {
        "weekly": {
            "data": {...},
            "total": 15,
            "average": 2.14,
            "completion_rate": 85.7
        },
        "monthly": {...}
    }
    """
    try:
        stats = gamification_manager.get_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': 'Failed to get stats'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)