"""
Integration tests for Pomodoro Timer Application

These tests verify the complete workflow and integration between components.
"""

import pytest
import json
import os
import tempfile
from datetime import datetime
from app import app, SessionLogger


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def clean_log_file():
    """Provide a clean temporary log file for integration tests."""
    fd, temp_file = tempfile.mkstemp(suffix='.log')
    os.close(fd)
    
    # Import the session_logger from app module
    from app import session_logger
    
    # Replace the global session logger's file
    original_file = session_logger.log_file
    session_logger.log_file = temp_file
    
    yield temp_file
    
    # Restore original file and cleanup
    session_logger.log_file = original_file
    if os.path.exists(temp_file):
        os.remove(temp_file)


class TestPomodoroWorkflow:
    """Test complete Pomodoro timer workflow scenarios."""
    
    @pytest.mark.integration
    def test_complete_pomodoro_session_workflow(self, client, clean_log_file):
        """Test a complete Pomodoro session from start to finish."""
        # Step 1: Check initial progress (should be empty)
        response = client.get('/api/progress')
        assert response.status_code == 200
        progress = json.loads(response.data)
        assert progress['count'] == 0
        assert progress['minutes'] == 0
        
        # Step 2: Complete a Pomodoro session
        session_data = {
            'timestamp': datetime.now().isoformat(),
            'duration': 1500  # 25 minutes
        }
        
        response = client.post('/api/session',
                             data=json.dumps(session_data),
                             content_type='application/json')
        assert response.status_code == 201
        result = json.loads(response.data)
        assert result['success'] is True
        
        # Step 3: Check updated progress
        response = client.get('/api/progress')
        assert response.status_code == 200
        progress = json.loads(response.data)
        assert progress['count'] == 1
        assert progress['minutes'] == 25
        
        # Step 4: Complete another session
        session_data['duration'] = 900  # 15 minute break
        response = client.post('/api/session',
                             data=json.dumps(session_data),
                             content_type='application/json')
        assert response.status_code == 201
        
        # Step 5: Verify final progress
        response = client.get('/api/progress')
        assert response.status_code == 200
        progress = json.loads(response.data)
        assert progress['count'] == 2
        assert progress['minutes'] == 40  # 25 + 15
    
    @pytest.mark.integration
    def test_multiple_days_workflow(self, client, clean_log_file):
        """Test workflow spanning multiple days."""
        # Log sessions for different days
        today = datetime.now()
        yesterday = today.replace(day=today.day-1) if today.day > 1 else today.replace(month=today.month-1, day=28)
        
        # Yesterday's sessions
        yesterday_session = {
            'timestamp': yesterday.isoformat(),
            'duration': 1500
        }
        response = client.post('/api/session',
                             data=json.dumps(yesterday_session),
                             content_type='application/json')
        assert response.status_code == 201
        
        # Today's sessions
        today_session = {
            'timestamp': today.isoformat(),
            'duration': 1800
        }
        response = client.post('/api/session',
                             data=json.dumps(today_session),
                             content_type='application/json')
        assert response.status_code == 201
        
        # Progress should only show today's sessions
        response = client.get('/api/progress')
        assert response.status_code == 200
        progress = json.loads(response.data)
        assert progress['count'] == 1
        assert progress['minutes'] == 30  # Only today's 30-minute session
    
    @pytest.mark.integration
    def test_error_recovery_workflow(self, client, clean_log_file):
        """Test system behavior during error conditions."""
        # Test invalid session data
        invalid_session = {'duration': 'invalid'}
        response = client.post('/api/session',
                             data=json.dumps(invalid_session),
                             content_type='application/json')
        assert response.status_code == 400
        
        # Progress should still work after error
        response = client.get('/api/progress')
        assert response.status_code == 200
        progress = json.loads(response.data)
        assert progress['count'] == 0  # No sessions logged due to error
        
        # Valid session should work after error
        valid_session = {'duration': 1500}
        response = client.post('/api/session',
                             data=json.dumps(valid_session),
                             content_type='application/json')
        assert response.status_code == 201
        
        # Progress should reflect the valid session
        response = client.get('/api/progress')
        assert response.status_code == 200
        progress = json.loads(response.data)
        assert progress['count'] == 1


class TestDataPersistence:
    """Test data persistence and file handling."""
    
    @pytest.mark.integration
    def test_log_file_persistence(self, clean_log_file):
        """Test that session data persists in the log file."""
        logger = SessionLogger(clean_log_file)
        
        # Log multiple sessions
        sessions = [
            {'duration': 1500, 'timestamp': '2024-01-01T10:00:00'},
            {'duration': 900, 'timestamp': '2024-01-01T10:30:00'},
            {'duration': 1800, 'timestamp': '2024-01-01T11:00:00'},
        ]
        
        for session in sessions:
            logger.log_session(
                timestamp=session['timestamp'],
                duration=session['duration']
            )
        
        # Verify file contents
        assert os.path.exists(clean_log_file)
        with open(clean_log_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) == len(sessions)
            
            for i, line in enumerate(lines):
                data = json.loads(line.strip())
                assert data['duration'] == sessions[i]['duration']
                assert data['timestamp'] == sessions[i]['timestamp']
    
    @pytest.mark.integration
    def test_concurrent_access_simulation(self, clean_log_file):
        """Test behavior with multiple loggers accessing the same file."""
        logger1 = SessionLogger(clean_log_file)
        logger2 = SessionLogger(clean_log_file)
        
        # Simulate concurrent writes
        logger1.log_session(duration=1500)
        logger2.log_session(duration=900)
        logger1.log_session(duration=1200)
        
        # Both loggers should read the same data
        progress1 = logger1.get_today_progress()
        progress2 = logger2.get_today_progress()
        
        assert progress1 == progress2
        assert progress1['count'] == 3
        # Total minutes: 25 + 15 + 20 = 60
        assert progress1['minutes'] == 60


class TestWebInterface:
    """Test web interface components."""
    
    @pytest.mark.integration
    def test_index_page_content(self, client):
        """Test that the index page serves correctly."""
        response = client.get('/')
        assert response.status_code == 200
        
        # Check for HTML content
        content = response.data.decode('utf-8')
        assert 'html' in content.lower()
        
        # The page should be serve-able without errors
        assert response.headers.get('Content-Type', '').startswith('text/html')
    
    @pytest.mark.integration  
    def test_api_json_responses(self, client):
        """Test that API endpoints return proper JSON responses."""
        # Test progress endpoint
        response = client.get('/api/progress')
        assert response.status_code == 200
        assert response.headers.get('Content-Type', '').startswith('application/json')
        
        data = json.loads(response.data)
        assert isinstance(data, dict)
        assert 'count' in data
        assert 'minutes' in data
        
        # Test session endpoint
        response = client.post('/api/session',
                             data=json.dumps({'duration': 1500}),
                             content_type='application/json')
        assert response.status_code == 201
        assert response.headers.get('Content-Type', '').startswith('application/json')
        
        data = json.loads(response.data)
        assert isinstance(data, dict)
        assert 'success' in data or 'error' in data


if __name__ == '__main__':
    pytest.main([__file__, '-v'])