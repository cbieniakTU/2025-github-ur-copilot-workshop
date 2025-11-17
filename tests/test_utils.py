"""
Test utilities and helper functions for Pomodoro Timer tests.

This module provides common fixtures, mock objects, and utility functions
that are shared across multiple test files.
"""

import json
import os
import tempfile
from datetime import datetime, date, timedelta
from contextlib import contextmanager
from typing import List, Dict, Any

import pytest
from app import SessionLogger


class TestDataGenerator:
    """Generate test data for various scenarios."""
    
    @staticmethod
    def create_session_data(
        timestamp: str = None,
        duration: int = 1500,
        date_str: str = None
    ) -> Dict[str, Any]:
        """Create a session data dictionary."""
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        if date_str is None:
            date_str = datetime.fromisoformat(timestamp).date().isoformat()
        
        return {
            'timestamp': timestamp,
            'duration': duration,
            'date': date_str
        }
    
    @staticmethod
    def create_multiple_sessions(
        count: int,
        base_date: date = None,
        duration_range: tuple = (900, 1800)
    ) -> List[Dict[str, Any]]:
        """Create multiple session data entries."""
        if base_date is None:
            base_date = date.today()
        
        sessions = []
        for i in range(count):
            timestamp = datetime.combine(
                base_date,
                datetime.min.time().replace(hour=9, minute=i * 30)
            ).isoformat()
            
            duration = duration_range[0] + (i * 300) % (duration_range[1] - duration_range[0])
            
            sessions.append(TestDataGenerator.create_session_data(
                timestamp=timestamp,
                duration=duration
            ))
        
        return sessions
    
    @staticmethod
    def create_historical_sessions(days_back: int = 7) -> List[Dict[str, Any]]:
        """Create session data for multiple historical days."""
        sessions = []
        base_date = date.today()
        
        for days_ago in range(days_back):
            session_date = base_date - timedelta(days=days_ago)
            day_sessions = TestDataGenerator.create_multiple_sessions(
                count=2 + (days_ago % 3),  # Vary sessions per day
                base_date=session_date
            )
            sessions.extend(day_sessions)
        
        return sessions


class MockSessionLogger:
    """Mock SessionLogger for testing without file I/O."""
    
    def __init__(self):
        self.sessions = []
        self.should_raise_error = False
        self.error_message = "Mock error"
    
    def log_session(self, timestamp=None, duration=1500):
        """Mock log_session method."""
        if self.should_raise_error:
            raise Exception(self.error_message)
        
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        session_data = TestDataGenerator.create_session_data(
            timestamp=timestamp,
            duration=duration
        )
        self.sessions.append(session_data)
    
    def get_today_progress(self):
        """Mock get_today_progress method."""
        if self.should_raise_error:
            raise Exception(self.error_message)
        
        today = date.today().isoformat()
        count = 0
        total_minutes = 0
        
        for session in self.sessions:
            if session.get('date') == today:
                count += 1
                total_minutes += session.get('duration', 1500) // 60
        
        return {'count': count, 'minutes': total_minutes}
    
    def set_error_mode(self, should_error: bool, message: str = "Mock error"):
        """Configure the mock to raise errors."""
        self.should_raise_error = should_error
        self.error_message = message
    
    def add_sessions(self, sessions: List[Dict[str, Any]]):
        """Add multiple sessions to the mock."""
        self.sessions.extend(sessions)


@contextmanager
def temporary_log_file(initial_data: List[Dict[str, Any]] = None):
    """Context manager for temporary log files with optional initial data."""
    fd, temp_file = tempfile.mkstemp(suffix='.log')
    os.close(fd)
    
    try:
        # Write initial data if provided
        if initial_data:
            with open(temp_file, 'w') as f:
                for session in initial_data:
                    f.write(json.dumps(session) + '\n')
        
        yield temp_file
        
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)


def assert_session_data_equal(actual: Dict[str, Any], expected: Dict[str, Any]):
    """Assert that two session data dictionaries are equal."""
    assert actual['duration'] == expected['duration']
    assert actual['date'] == expected['date']
    
    # For timestamp, we might have slight differences due to test timing
    if 'timestamp' in expected:
        assert actual['timestamp'] == expected['timestamp']


def assert_progress_equal(actual: Dict[str, Any], expected: Dict[str, Any]):
    """Assert that two progress dictionaries are equal."""
    assert actual['count'] == expected['count']
    assert actual['minutes'] == expected['minutes']


class TestScenarios:
    """Common test scenarios that can be reused."""
    
    @staticmethod
    def basic_session_workflow(client) -> Dict[str, Any]:
        """Execute a basic session workflow and return results."""
        # Get initial progress
        initial_response = client.get('/api/progress')
        initial_progress = json.loads(initial_response.data)
        
        # Log a session
        session_data = {'duration': 1500}
        session_response = client.post('/api/session',
                                     data=json.dumps(session_data),
                                     content_type='application/json')
        
        # Get final progress
        final_response = client.get('/api/progress')
        final_progress = json.loads(final_response.data)
        
        return {
            'initial_progress': initial_progress,
            'session_response': session_response,
            'final_progress': final_progress
        }
    
    @staticmethod
    def error_handling_workflow(client) -> Dict[str, Any]:
        """Execute error handling workflow and return results."""
        # Test invalid duration
        invalid_data = {'duration': 10}
        error_response = client.post('/api/session',
                                   data=json.dumps(invalid_data),
                                   content_type='application/json')
        
        # Test progress after error
        progress_response = client.get('/api/progress')
        
        return {
            'error_response': error_response,
            'progress_response': progress_response
        }


# Pytest fixtures that can be imported by test files

@pytest.fixture
def mock_session_logger():
    """Provide a MockSessionLogger instance."""
    return MockSessionLogger()


@pytest.fixture
def test_data_generator():
    """Provide a TestDataGenerator instance."""
    return TestDataGenerator()


@pytest.fixture
def sample_sessions():
    """Provide sample session data for testing."""
    return TestDataGenerator.create_multiple_sessions(count=5)


@pytest.fixture
def historical_sessions():
    """Provide historical session data for testing."""
    return TestDataGenerator.create_historical_sessions(days_back=7)