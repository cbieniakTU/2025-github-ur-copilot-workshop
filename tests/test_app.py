"""
Tests for Pomodoro Timer Flask Application

Comprehensive test suite covering all functionality including:
- SessionLogger class methods
- Flask API endpoints
- Error handling
- Edge cases and validation
"""

import pytest
import json
import os
import tempfile
from datetime import datetime, date, timedelta
from unittest.mock import patch, mock_open
from app import app, SessionLogger


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def temp_log_file():
    """Create a temporary log file for testing."""
    fd, temp_file = tempfile.mkstemp()
    os.close(fd)
    yield temp_file
    # Cleanup
    if os.path.exists(temp_file):
        os.remove(temp_file)


class TestSessionLogger:
    """Test the SessionLogger class functionality."""
    
    def test_log_session_default_values(self, temp_log_file):
        """Test logging a session with default values."""
        logger = SessionLogger(temp_log_file)
        logger.log_session()
        
        # Check file exists and contains data
        assert os.path.exists(temp_log_file)
        
        with open(temp_log_file, 'r') as f:
            line = f.readline().strip()
            data = json.loads(line)
            assert data['duration'] == 1500  # Default 25 minutes
            assert 'timestamp' in data
            assert 'date' in data
    
    def test_log_session_custom_values(self, temp_log_file):
        """Test logging a session with custom values."""
        logger = SessionLogger(temp_log_file)
        custom_time = "2024-01-15T10:30:00"
        logger.log_session(timestamp=custom_time, duration=900)  # 15 minutes
        
        with open(temp_log_file, 'r') as f:
            line = f.readline().strip()
            data = json.loads(line)
            assert data['duration'] == 900
            assert data['timestamp'] == custom_time
            assert data['date'] == "2024-01-15"
    
    def test_log_session_multiple_entries(self, temp_log_file):
        """Test logging multiple sessions."""
        logger = SessionLogger(temp_log_file)
        logger.log_session(duration=1500)
        logger.log_session(duration=1800)
        
        with open(temp_log_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 2
            
        # Verify both entries
        data1 = json.loads(lines[0].strip())
        data2 = json.loads(lines[1].strip())
        assert data1['duration'] == 1500
        assert data2['duration'] == 1800
    
    def test_log_session_file_creation(self):
        """Test that log file is created if it doesn't exist."""
        non_existent_file = 'temp_test_file.log'
        logger = SessionLogger(non_existent_file)
        
        # Ensure file doesn't exist
        if os.path.exists(non_existent_file):
            os.remove(non_existent_file)
            
        logger.log_session()
        
        # File should now exist
        assert os.path.exists(non_existent_file)
        
        # Cleanup
        os.remove(non_existent_file)
    
    @patch('builtins.open', side_effect=IOError("Permission denied"))
    def test_log_session_file_error(self, mock_file):
        """Test error handling when file cannot be written."""
        logger = SessionLogger('test.log')
        
        with pytest.raises(IOError):
            logger.log_session()
    
    def test_get_today_progress_empty(self, temp_log_file):
        """Test getting progress when no sessions exist."""
        logger = SessionLogger(temp_log_file)
        progress = logger.get_today_progress()
        
        assert progress == {'count': 0, 'minutes': 0}
    
    def test_get_today_progress_with_sessions(self, temp_log_file):
        """Test getting progress with sessions logged today."""
        logger = SessionLogger(temp_log_file)
        
        # Log some sessions for today
        timestamp = datetime.now().isoformat()
        
        logger.log_session(timestamp=timestamp, duration=1500)  # 25 minutes
        logger.log_session(timestamp=timestamp, duration=1800)  # 30 minutes
        
        progress = logger.get_today_progress()
        assert progress['count'] == 2
        assert progress['minutes'] == 55  # 25 + 30 minutes
    
    def test_get_today_progress_mixed_dates(self, temp_log_file):
        """Test getting progress with sessions from different dates."""
        logger = SessionLogger(temp_log_file)
        
        # Log sessions for today and yesterday
        today_timestamp = datetime.now().isoformat()
        yesterday = datetime.now() - timedelta(days=1)
        yesterday_timestamp = yesterday.isoformat()
        
        logger.log_session(timestamp=today_timestamp, duration=1500)
        logger.log_session(timestamp=yesterday_timestamp, duration=1500)
        logger.log_session(timestamp=today_timestamp, duration=900)
        
        progress = logger.get_today_progress()
        assert progress['count'] == 2  # Only today's sessions
        assert progress['minutes'] == 40  # 25 + 15 minutes
    
    def test_get_today_progress_corrupted_file(self, temp_log_file):
        """Test progress reading with corrupted JSON data."""
        # Write invalid JSON to the file
        with open(temp_log_file, 'w') as f:
            f.write('invalid json line\n')
            f.write('{"valid": "json", "date": "' + date.today().isoformat() + '", "duration": 1500}\n')
        
        logger = SessionLogger(temp_log_file)
        progress = logger.get_today_progress()
        
        # Should return zeros due to JSON parsing error
        assert progress == {'count': 0, 'minutes': 0}
    
    def test_get_today_progress_nonexistent_file(self):
        """Test progress reading when log file doesn't exist."""
        logger = SessionLogger('nonexistent_file.log')
        progress = logger.get_today_progress()
        
        assert progress == {'count': 0, 'minutes': 0}
    
    @patch('builtins.open', side_effect=IOError("File read error"))
    def test_get_today_progress_file_read_error(self, mock_file, temp_log_file):
        """Test error handling when file cannot be read."""
        logger = SessionLogger(temp_log_file)
        progress = logger.get_today_progress()
        
        # Should return zeros on read error
        assert progress == {'count': 0, 'minutes': 0}


class TestFlaskApp:
    """Test Flask app routes and API endpoints."""
    
    def test_index_route(self, client):
        """Test the main index route."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'html' in response.data.lower()
    
    def test_index_route_methods(self, client):
        """Test that index route only accepts GET requests."""
        response = client.post('/')
        assert response.status_code == 405  # Method Not Allowed
        
        response = client.put('/')
        assert response.status_code == 405
        
        response = client.delete('/')
        assert response.status_code == 405
    
    def test_api_progress_empty(self, client):
        """Test progress API with no sessions."""
        response = client.get('/api/progress')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'count' in data
        assert 'minutes' in data
        assert isinstance(data['count'], int)
        assert isinstance(data['minutes'], int)
    
    def test_api_session_post_valid(self, client):
        """Test posting a valid session."""
        session_data = {
            'timestamp': datetime.now().isoformat(),
            'duration': 1500
        }
        
        response = client.post('/api/session',
                             data=json.dumps(session_data),
                             content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_api_session_post_invalid_duration(self, client):
        """Test posting session with invalid duration."""
        session_data = {
            'duration': 10  # Too short
        }
        
        response = client.post('/api/session',
                             data=json.dumps(session_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_api_session_post_empty_body(self, client):
        """Test posting session with empty body (should use defaults)."""
        response = client.post('/api/session',
                             data=json.dumps({}),
                             content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_api_session_post_no_json(self, client):
        """Test posting session without JSON content type."""
        response = client.post('/api/session')
        
        assert response.status_code == 201  # Should still work with empty data
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_api_session_post_invalid_json(self, client):
        """Test posting session with malformed JSON."""
        response = client.post('/api/session',
                             data='{"invalid": json}',
                             content_type='application/json')
        
        # Should still work as get_json(silent=True) handles errors
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_api_session_post_negative_duration(self, client):
        """Test posting session with negative duration."""
        session_data = {'duration': -100}
        
        response = client.post('/api/session',
                             data=json.dumps(session_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_api_session_post_string_duration(self, client):
        """Test posting session with string duration."""
        session_data = {'duration': 'not_a_number'}
        
        response = client.post('/api/session',
                             data=json.dumps(session_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_api_progress_methods(self, client):
        """Test that progress endpoint only accepts GET requests."""
        response = client.post('/api/progress')
        assert response.status_code == 405  # Method Not Allowed
        
        response = client.put('/api/progress')
        assert response.status_code == 405
        
        response = client.delete('/api/progress')
        assert response.status_code == 405
    
    @patch('app.session_logger.log_session', side_effect=Exception("Database error"))
    def test_api_session_post_logging_error(self, mock_log, client):
        """Test API response when logging fails."""
        session_data = {'duration': 1500}
        
        response = client.post('/api/session',
                             data=json.dumps(session_data),
                             content_type='application/json')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error'] == 'Failed to log session'
    
    @patch('app.session_logger.get_today_progress', side_effect=Exception("Read error"))
    def test_api_progress_error(self, mock_progress, client):
        """Test API response when progress retrieval fails."""
        response = client.get('/api/progress')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error'] == 'Failed to get progress'


class TestSessionLoggerEdgeCases:
    """Test edge cases and boundary conditions for SessionLogger."""
    
    def test_session_logger_initialization(self):
        """Test SessionLogger initialization with different parameters."""
        # Default initialization
        logger1 = SessionLogger()
        assert logger1.log_file == 'pomodoro.log'
        
        # Custom file initialization
        logger2 = SessionLogger('custom.log')
        assert logger2.log_file == 'custom.log'
    
    def test_log_session_boundary_durations(self, temp_log_file):
        """Test logging with boundary duration values."""
        logger = SessionLogger(temp_log_file)
        
        # Test minimum valid duration (30 seconds would be validated by API)
        logger.log_session(duration=30)
        
        # Test large duration
        logger.log_session(duration=86400)  # 24 hours
        
        with open(temp_log_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 2
            
            data1 = json.loads(lines[0].strip())
            data2 = json.loads(lines[1].strip())
            
            assert data1['duration'] == 30
            assert data2['duration'] == 86400
    
    def test_timestamp_parsing_edge_cases(self, temp_log_file):
        """Test various timestamp formats and edge cases."""
        logger = SessionLogger(temp_log_file)
        
        # Test different timestamp formats
        timestamps = [
            "2024-01-01T00:00:00",
            "2024-12-31T23:59:59",
            "2024-02-29T12:00:00",  # Leap year
        ]
        
        for timestamp in timestamps:
            logger.log_session(timestamp=timestamp, duration=1500)
        
        with open(temp_log_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) == len(timestamps)
            
            for i, line in enumerate(lines):
                data = json.loads(line.strip())
                assert data['timestamp'] == timestamps[i]


class TestAppConfiguration:
    """Test Flask app configuration and setup."""
    
    def test_app_config(self):
        """Test Flask app configuration."""
        assert app.config['DEBUG'] is True
        assert app.config['TESTING'] is True  # Set by pytest fixture
        assert app.config['JSON_SORT_KEYS'] is False
    
    def test_app_routes_exist(self):
        """Test that all expected routes are registered."""
        with app.test_client() as client:
            # Test route registration
            response = client.get('/')
            assert response.status_code == 200
            
            response = client.get('/api/progress')
            assert response.status_code == 200
            
            response = client.post('/api/session')
            assert response.status_code == 201
    
    def test_main_execution_guard_structure(self):
        """Test that the main execution guard is properly structured."""
        # Read the source code to verify the main guard structure
        with open('app.py', 'r') as f:
            source_lines = f.readlines()
        
        # Find the main guard
        main_guard_found = False
        app_run_found = False
        
        for i, line in enumerate(source_lines):
            if "if __name__ == '__main__':" in line.strip():
                main_guard_found = True
                # Check that the next line contains app.run
                if i + 1 < len(source_lines):
                    next_line = source_lines[i + 1].strip()
                    if 'app.run(' in next_line:
                        app_run_found = True
        
        assert main_guard_found, "Main execution guard not found"
        assert app_run_found, "app.run() not found after main guard"


if __name__ == '__main__':
    pytest.main([__file__])