"""
Pomodoro Timer Flask Application

A simple web application for managing Pomodoro timer sessions.
Provides a web interface and REST API for session tracking.
"""

from flask import Flask, render_template, request, jsonify
import os
import json
from datetime import datetime, date
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


# Initialize session logger
session_logger = SessionLogger()


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
        
        return jsonify({
            'success': True,
            'message': 'Session logged successfully'
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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)