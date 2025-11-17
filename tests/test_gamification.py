"""
Tests for Gamification Features

Test suite covering:
- GamificationManager class methods
- XP and level progression
- Achievement unlocking
- Streak tracking
- Statistics calculations
- API endpoints for gamification
"""

import pytest
import json
import os
import tempfile
from datetime import datetime, date, timedelta
from unittest.mock import patch, MagicMock
from app import app, SessionLogger, GamificationManager


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def temp_gamification_file():
    """Create a temporary gamification data file for testing."""
    fd, temp_file = tempfile.mkstemp(suffix='.json')
    os.close(fd)
    yield temp_file
    # Cleanup
    if os.path.exists(temp_file):
        os.remove(temp_file)


@pytest.fixture
def temp_log_file():
    """Create a temporary log file for testing."""
    fd, temp_file = tempfile.mkstemp()
    os.close(fd)
    yield temp_file
    # Cleanup
    if os.path.exists(temp_file):
        os.remove(temp_file)


@pytest.fixture
def gamification_manager_with_logger(temp_gamification_file, temp_log_file):
    """Create a GamificationManager with a SessionLogger for testing."""
    session_logger = SessionLogger(temp_log_file)
    manager = GamificationManager(temp_gamification_file, session_logger)
    return manager, session_logger


class TestGamificationManager:
    """Test the GamificationManager class functionality."""
    
    def test_initialization_new_file(self, temp_gamification_file):
        """Test initialization with a new file."""
        manager = GamificationManager(temp_gamification_file)
        
        assert manager.data['xp'] == 0
        assert manager.data['level'] == 1
        assert manager.data['achievements'] == []
        assert manager.data['current_streak'] == 0
        assert manager.data['longest_streak'] == 0
    
    def test_initialization_existing_file(self, temp_gamification_file):
        """Test initialization with existing data."""
        existing_data = {
            'xp': 500,
            'level': 5,
            'achievements': ['first_session', 'streak_3'],
            'current_streak': 3,
            'longest_streak': 5,
            'last_session_date': '2024-01-15'
        }
        
        with open(temp_gamification_file, 'w') as f:
            json.dump(existing_data, f)
        
        manager = GamificationManager(temp_gamification_file)
        
        assert manager.data['xp'] == 500
        assert manager.data['level'] == 5
        assert len(manager.data['achievements']) == 2
    
    def test_add_session_xp(self, temp_gamification_file):
        """Test adding XP for a session."""
        manager = GamificationManager(temp_gamification_file)
        
        result = manager.add_session_xp()
        
        assert result['xp_gained'] == 25
        assert result['total_xp'] == 25
        assert result['level'] == 1
        assert result['leveled_up'] is False
    
    def test_level_up(self, temp_gamification_file):
        """Test leveling up when XP threshold is reached."""
        manager = GamificationManager(temp_gamification_file)
        manager.data['xp'] = 95  # Just below level 2 (100 XP)
        manager._save_data()
        
        result = manager.add_session_xp()
        
        assert result['total_xp'] == 120
        assert result['level'] == 2
        assert result['leveled_up'] is True
    
    def test_get_level_from_xp(self, temp_gamification_file):
        """Test calculating level from XP."""
        manager = GamificationManager(temp_gamification_file)
        
        assert manager.get_level_from_xp(0) == 1
        assert manager.get_level_from_xp(50) == 1
        assert manager.get_level_from_xp(100) == 2
        assert manager.get_level_from_xp(250) == 3
        assert manager.get_level_from_xp(450) == 4
        assert manager.get_level_from_xp(1000) == 6
    
    def test_streak_first_session(self, temp_gamification_file):
        """Test streak counter on first session."""
        manager = GamificationManager(temp_gamification_file)
        today = date.today()
        
        manager.update_streak(today)
        
        assert manager.data['current_streak'] == 1
        assert manager.data['longest_streak'] == 1
        assert manager.data['last_session_date'] == today.isoformat()
    
    def test_streak_consecutive_days(self, temp_gamification_file):
        """Test streak increases on consecutive days."""
        manager = GamificationManager(temp_gamification_file)
        today = date.today()
        
        manager.update_streak(today - timedelta(days=2))
        assert manager.data['current_streak'] == 1
        
        manager.update_streak(today - timedelta(days=1))
        assert manager.data['current_streak'] == 2
        
        manager.update_streak(today)
        assert manager.data['current_streak'] == 3
        assert manager.data['longest_streak'] == 3
    
    def test_streak_same_day(self, temp_gamification_file):
        """Test streak doesn't change on same day."""
        manager = GamificationManager(temp_gamification_file)
        today = date.today()
        
        manager.update_streak(today)
        assert manager.data['current_streak'] == 1
        
        manager.update_streak(today)
        assert manager.data['current_streak'] == 1
    
    def test_streak_broken(self, temp_gamification_file):
        """Test streak resets when broken."""
        manager = GamificationManager(temp_gamification_file)
        today = date.today()
        
        manager.update_streak(today - timedelta(days=5))
        manager.update_streak(today - timedelta(days=4))
        assert manager.data['current_streak'] == 2
        
        # Skip a day - breaks streak
        manager.update_streak(today)
        assert manager.data['current_streak'] == 1
        assert manager.data['longest_streak'] == 2
    
    def test_longest_streak_tracking(self, temp_gamification_file):
        """Test that longest streak is properly tracked."""
        manager = GamificationManager(temp_gamification_file)
        today = date.today()
        
        # Create a streak of 5
        for i in range(5, 0, -1):
            manager.update_streak(today - timedelta(days=i))
        assert manager.data['current_streak'] == 5
        assert manager.data['longest_streak'] == 5
        
        # Break streak by skipping 2 days
        manager.update_streak(today + timedelta(days=2))
        assert manager.data['current_streak'] == 1
        assert manager.data['longest_streak'] == 5  # Should remain 5


class TestAchievements:
    """Test achievement unlocking functionality."""
    
    def test_first_session_achievement(self, gamification_manager_with_logger):
        """Test 'First Steps' achievement unlocks on first session."""
        manager, logger = gamification_manager_with_logger
        
        logger.log_session()
        achievements = manager.check_achievements()
        
        assert len(achievements) == 1
        assert achievements[0]['id'] == 'first_session'
        assert achievements[0]['name'] == 'First Steps'
        assert 'first_session' in manager.data['achievements']
    
    def test_streak_3_achievement(self, gamification_manager_with_logger):
        """Test '3-Day Warrior' achievement."""
        manager, logger = gamification_manager_with_logger
        today = date.today()
        
        # Create 3-day streak
        for i in range(2, -1, -1):
            session_date = today - timedelta(days=i)
            logger.log_session(timestamp=session_date.isoformat() + 'T10:00:00')
            manager.update_streak(session_date)
        
        achievements = manager.check_achievements()
        achievement_ids = [a['id'] for a in achievements]
        
        assert 'streak_3' in achievement_ids
        assert 'streak_3' in manager.data['achievements']
    
    def test_streak_7_achievement(self, gamification_manager_with_logger):
        """Test 'Week Champion' achievement."""
        manager, logger = gamification_manager_with_logger
        today = date.today()
        
        # Create 7-day streak
        for i in range(6, -1, -1):
            session_date = today - timedelta(days=i)
            logger.log_session(timestamp=session_date.isoformat() + 'T10:00:00')
            manager.update_streak(session_date)
        
        achievements = manager.check_achievements()
        achievement_ids = [a['id'] for a in achievements]
        
        assert 'streak_7' in achievement_ids
    
    def test_week_10_achievement(self, gamification_manager_with_logger):
        """Test 'Weekly Master' achievement (10 sessions in a week)."""
        manager, logger = gamification_manager_with_logger
        today = date.today()
        
        # Get the start of current week (Monday)
        week_start = today - timedelta(days=today.weekday())
        
        # Log 10 sessions this week, spread across different days
        for i in range(10):
            # Spread across current week (max 7 days)
            days_offset = i % 7
            session_date = week_start + timedelta(days=days_offset)
            logger.log_session(timestamp=session_date.isoformat() + f'T{10+i}:00:00')
        
        achievements = manager.check_achievements()
        achievement_ids = [a['id'] for a in achievements]
        
        assert 'week_10' in achievement_ids
    
    def test_total_50_achievement(self, gamification_manager_with_logger):
        """Test 'Half Century' achievement (50 total sessions)."""
        manager, logger = gamification_manager_with_logger
        
        # Log 50 sessions
        for i in range(50):
            logger.log_session()
        
        achievements = manager.check_achievements()
        achievement_ids = [a['id'] for a in achievements]
        
        assert 'total_50' in achievement_ids
    
    def test_achievements_not_duplicated(self, gamification_manager_with_logger):
        """Test achievements are only unlocked once."""
        manager, logger = gamification_manager_with_logger
        
        logger.log_session()
        achievements1 = manager.check_achievements()
        achievements2 = manager.check_achievements()
        
        assert len(achievements1) == 1
        assert len(achievements2) == 0  # Already unlocked


class TestStatistics:
    """Test statistics calculation functionality."""
    
    def test_stats_empty(self, gamification_manager_with_logger):
        """Test statistics with no sessions."""
        manager, logger = gamification_manager_with_logger
        
        stats = manager.get_stats()
        
        assert stats['weekly']['total'] == 0
        assert stats['weekly']['average'] == 0
        assert stats['monthly']['total'] == 0
    
    def test_stats_weekly(self, gamification_manager_with_logger):
        """Test weekly statistics calculation."""
        manager, logger = gamification_manager_with_logger
        today = date.today()
        
        # Log sessions for the past 7 days
        for i in range(7):
            session_date = today - timedelta(days=i)
            logger.log_session(timestamp=session_date.isoformat() + 'T10:00:00')
        
        stats = manager.get_stats()
        
        assert stats['weekly']['total'] == 7
        assert stats['weekly']['average'] == 1.0
        assert stats['weekly']['completion_rate'] == 100.0
    
    def test_stats_monthly(self, gamification_manager_with_logger):
        """Test monthly statistics calculation."""
        manager, logger = gamification_manager_with_logger
        today = date.today()
        
        # Log 15 sessions spread across the month
        for i in range(15):
            session_date = today - timedelta(days=i * 2)
            logger.log_session(timestamp=session_date.isoformat() + 'T10:00:00')
        
        stats = manager.get_stats()
        
        assert stats['monthly']['total'] == 15
        assert stats['monthly']['average'] == 0.5  # 15 sessions / 30 days
        assert stats['monthly']['completion_rate'] == 50.0  # 15 days with sessions / 30 days


class TestGamificationAPI:
    """Test gamification API endpoints."""
    
    def test_api_gamification_endpoint(self, client):
        """Test GET /api/gamification endpoint."""
        response = client.get('/api/gamification')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'xp' in data
        assert 'level' in data
        assert 'current_streak' in data
        assert 'achievements' in data
    
    def test_api_stats_endpoint(self, client):
        """Test GET /api/stats endpoint."""
        response = client.get('/api/stats')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'weekly' in data
        assert 'monthly' in data
        assert 'total' in data['weekly']
        assert 'average' in data['weekly']
    
    def test_api_session_returns_gamification(self, client):
        """Test that POST /api/session returns gamification data."""
        response = client.post('/api/session', 
                              json={'duration': 1500},
                              content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        
        assert 'gamification' in data
        assert 'xp_gained' in data['gamification']
        assert 'level' in data['gamification']
        assert 'leveled_up' in data['gamification']
        assert 'new_achievements' in data['gamification']
    
    def test_gamification_data_structure(self, client):
        """Test the structure of gamification data returned."""
        response = client.get('/api/gamification')
        data = json.loads(response.data)
        
        # Check all required fields
        required_fields = [
            'xp', 'level', 'xp_progress', 'xp_needed', 'xp_percentage',
            'current_streak', 'longest_streak', 'achievements',
            'unlocked_achievements', 'total_achievements', 'unlocked_count'
        ]
        
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        # Check achievements structure
        if len(data['achievements']) > 0:
            achievement = data['achievements'][0]
            assert 'id' in achievement
            assert 'name' in achievement
            assert 'description' in achievement
            assert 'icon' in achievement
            assert 'unlocked' in achievement


class TestGamificationIntegration:
    """Integration tests for gamification system."""
    
    def test_complete_gamification_workflow(self, client):
        """Test a complete workflow with sessions, XP, and achievements."""
        # Start with clean state - get initial data
        initial_response = client.get('/api/gamification')
        initial_data = json.loads(initial_response.data)
        initial_xp = initial_data['xp']
        
        # Log a session
        session_response = client.post('/api/session',
                                      json={'duration': 1500},
                                      content_type='application/json')
        assert session_response.status_code == 201
        
        session_data = json.loads(session_response.data)
        assert session_data['gamification']['xp_gained'] == 25
        
        # Get updated gamification data
        updated_response = client.get('/api/gamification')
        updated_data = json.loads(updated_response.data)
        
        # XP should have increased
        assert updated_data['xp'] == initial_xp + 25
        
        # First session achievement should be unlocked
        unlocked_ids = [a['id'] for a in updated_data['unlocked_achievements']]
        assert 'first_session' in unlocked_ids
    
    def test_level_progression(self, client):
        """Test that level increases as XP accumulates."""
        # Log enough sessions to level up (100 XP = level 2, 25 XP per session)
        for _ in range(5):
            client.post('/api/session',
                       json={'duration': 1500},
                       content_type='application/json')
        
        response = client.get('/api/gamification')
        data = json.loads(response.data)
        
        # Should have at least 125 XP and be level 2
        assert data['xp'] >= 125
        assert data['level'] >= 2
