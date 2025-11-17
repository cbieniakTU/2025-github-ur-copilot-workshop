# Pomodoro Timer Web App

A beautiful, modern web-based Pomodoro timer built with Flask backend and vanilla JavaScript frontend. This application helps you manage your time using the Pomodoro Technique with session tracking and daily progress monitoring.

![Pomodoro Timer](pomodoro.png)

## ✨ Features

- **25-minute Pomodoro Timer**: Classic 25-minute focus sessions
- **Visual Progress**: Elegant circular progress bar with smooth animations
- **Enhanced Visual Feedback**: Floating particles and ripple effects during active sessions
- **Dynamic Color Changes**: Progress ring changes color based on timer state (idle/running/completed)
- **Session Tracking**: Automatic logging of completed sessions
- **Daily Statistics**: View your daily progress (sessions completed and focus time)
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Clean UI**: Modern, distraction-free interface with contextual animations
- **RESTful API**: Backend API for session management

## 🚀 Getting Started

### Prerequisites

- Python 3.8+ 
- `uv` package manager (recommended)

### Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd 2025-github-ur-copilot-workshop
```

2. **Install `uv` package manager**:
If you don't have `uv` installed, follow the installation guide at: https://docs.astral.sh/uv/getting-started/installation/

3. **Create virtual environment**:
```bash
uv venv
```

4. **Activate virtual environment**:
```bash
source .venv/bin/activate
```

5. **Install dependencies**:
```bash
uv pip install -r requirements.txt
```

### Running the Application

1. **Start the Flask development server**:
```bash
python app.py
```

2. **Open your browser** and navigate to:
```
http://127.0.0.1:5000
```

That's it! Your Pomodoro timer is now running.

## 🎯 How to Use

1. **Start a Session**: Click the "Start" button to begin a 25-minute Pomodoro session
2. **Monitor Progress**: Watch the circular progress bar fill as time counts down
3. **Pause/Resume**: Click "Pause" during a session to pause, then "Resume" to continue
4. **Reset Timer**: Click "Reset" to return to 25:00
5. **Automatic Completion**: When a session completes, it's automatically logged and your daily progress updates
6. **View Progress**: Check your "Today's Progress" section to see completed sessions and focus time

## 🏗️ Project Structure

```
pomodoro-app/
├── app.py                 # Flask backend with API endpoints
├── requirements.txt       # Python dependencies
├── static/
│   ├── style.css         # UI styles with particle/ripple animations
│   └── timer.js          # Timer logic with visual effects system
├── templates/
│   └── index.html        # Main HTML template with visual effects containers
├── tests/
│   └── test_app.py       # Backend API tests
├── pomodoro.log          # Session history (auto-generated)
├── README.md             # This file
├── architecture.md       # Technical architecture documentation
└── plan.md              # Development plan and roadmap
```

## 🔧 API Endpoints

The application provides a RESTful API for session management:

### `GET /api/progress`
Returns today's progress statistics.
```json
{
  "count": 3,
  "minutes": 75
}
```

### `POST /api/session`
Logs a completed Pomodoro session.
```json
{
  "timestamp": "2024-01-01T12:00:00",
  "duration": 1500
}
```

## 🧪 Testing

This project includes comprehensive unit tests to ensure reliability and maintainability. The test suite covers all critical functionality with high code coverage.

### Prerequisites

Testing dependencies are included in `requirements.txt`. Make sure you have activated the virtual environment:

```bash
source .venv/bin/activate
```

### Running Tests

#### Basic Test Execution

Run all tests with verbose output:
```bash
python -m pytest tests/ -v
```

#### Run Specific Test Files

Run only unit tests:
```bash
python -m pytest tests/test_app.py -v
```

Run only integration tests:
```bash
python -m pytest tests/test_integration.py -v
```

#### Code Coverage Analysis

Generate a detailed coverage report:
```bash
python -m pytest tests/ --cov=app --cov-report=term-missing
```

Generate HTML coverage report:
```bash
python -m pytest tests/ --cov=app --cov-report=html
```

The HTML report will be available in `htmlcov/index.html` - open it in your browser to see detailed line-by-line coverage.

#### Test Markers

Run tests by category using pytest markers:
```bash
# Run only unit tests (fast)
python -m pytest tests/ -m "not integration" -v

# Run only integration tests
python -m pytest tests/ -m integration -v

# Run tests excluding slow tests
python -m pytest tests/ -m "not slow" -v
```

### Test Suite Overview

The test suite is organized into several files:

#### `tests/test_app.py`
**Unit Tests** - Core functionality testing:
- `TestSessionLogger`: File-based session logging operations
- `TestFlaskApp`: API endpoints and HTTP request handling
- `TestSessionLoggerEdgeCases`: Boundary conditions and edge cases
- `TestAppConfiguration`: Flask application setup and configuration

#### `tests/test_integration.py`
**Integration Tests** - End-to-end workflow testing:
- `TestPomodoroWorkflow`: Complete user session workflows
- `TestDataPersistence`: File handling and data persistence
- `TestWebInterface`: Frontend-backend integration

#### `tests/test_utils.py`
**Test Utilities** - Shared fixtures and helper functions:
- Mock objects for testing without file I/O
- Test data generators for various scenarios
- Common assertion helpers

### Coverage Target

The project maintains **99% code coverage** with comprehensive tests covering:

- ✅ **SessionLogger Class**: All methods including error handling
- ✅ **Flask API Endpoints**: All routes with valid/invalid inputs
- ✅ **Data Validation**: Input validation and sanitization
- ✅ **Error Handling**: Exception scenarios and recovery
- ✅ **File Operations**: Session logging and progress reading
- ✅ **Edge Cases**: Boundary conditions and unusual inputs
- ✅ **Integration Workflows**: Complete user journeys

### Test Configuration

The project uses `pytest.ini` for test configuration:
- Automatic test discovery in `tests/` directory
- Coverage reporting with HTML output
- Strict marker enforcement
- Custom test markers for organization

### Continuous Testing

For development, you can run tests automatically on file changes using pytest-watch:

```bash
# Install pytest-watch (optional)
uv pip install pytest-watch

# Run tests automatically on changes
ptw tests/ app.py
```

### Test Data

Tests use temporary files and isolated test environments to ensure:
- No interference between test runs
- Clean state for each test
- No pollution of development data
- Reliable and repeatable results

### Test Runner Script

For convenience, use the provided test runner script:

```bash
# Run all tests (default)
./run_tests.sh

# Run only unit tests
./run_tests.sh unit

# Run only integration tests  
./run_tests.sh integration

# Run tests with HTML coverage report
./run_tests.sh coverage

# Run tests quickly without coverage
./run_tests.sh quick

# Show help
./run_tests.sh help
```

The script automatically activates the virtual environment and provides colored output for better readability.

### Debugging Tests

Run tests with debugging information:
```bash
# Show local variables on test failures
python -m pytest tests/ -v --tb=long

# Run specific test with debugging
python -m pytest tests/test_app.py::TestSessionLogger::test_log_session_default_values -v -s

# Use pdb debugger on failures
python -m pytest tests/ --pdb
```

## 💻 Development

This project was built with modern web development practices:

- **Backend**: Flask (Python) - Lightweight and efficient
- **Frontend**: Vanilla JavaScript - No framework dependencies, includes visual effects system
- **Styling**: CSS3 with particle animations, ripple effects, and responsive design
- **Visual Effects**: Performance-optimized particle system and dynamic color transitions
- **Storage**: File-based logging (JSON format)
- **Testing**: pytest with comprehensive test coverage

### Key Components

1. **SessionLogger Class**: Handles file-based session persistence
2. **PomodoroTimer Class**: JavaScript timer logic with state management and visual effects
3. **Circular Progress**: SVG-based progress visualization with dynamic color changes
4. **Visual Effects System**: Particle generation and ripple animations
5. **Responsive Design**: Mobile-first CSS approach with performance-optimized animations

## 📱 Browser Support

- ✅ Chrome/Chromium 70+ (Full visual effects support)
- ✅ Firefox 65+ (Full visual effects support)
- ✅ Safari 12+ (Full visual effects support)
- ✅ Edge 79+ (Full visual effects support)

**Note**: Visual effects (particles and ripples) use modern CSS animations and transforms. Older browsers will gracefully degrade to basic functionality.

## 📄 License

This project is part of the GitHub Copilot Workshop for GitHub Universe Recap 2025, Jakarta, Indonesia.

## 🤝 Contributing

This is a workshop project, but feel free to:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 🎓 Workshop Information

**Event**: GitHub Copilot Workshop - GitHub Universe Recap 2025  
**Location**: Jakarta, Indonesia  
**Technologies**: Python, JavaScript, HTML, CSS, Flask

---

Made with ❤️ using GitHub Copilot
