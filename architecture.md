# Pomodoro Timer Web App Architecture

This document summarizes the proposed architecture for the Pomodoro timer web app based on the project goals and the provided UI mockup.

---

## 1. Frontend (HTML/CSS/JavaScript)

### Responsibilities:
- Display the Pomodoro timer UI, including circular progress, session timer, and stats (“Today's Progress”).
- Implement countdown timer and progress animation fully in JavaScript on the client.
- Handle user interactions: Start and Reset buttons.
- Fetch and display progress data (sessions completed, focus time) from the backend via AJAX.

### Technologies:
- **HTML/CSS:** UI structure and styling (including circular progress using SVG or Canvas).
- **Vanilla JavaScript:** Timer logic, UI interactivity, and API communication.

### UI Elements:
- Circular timer progress bar and countdown display.
- Start/Reset buttons.
- Area showing today’s completed count and focus minutes.

---

## 2. Backend (Flask, Python)

### Responsibilities:
- Serve the main HTML page and static assets (CSS, JS).
- Provide REST API endpoints for:
    - Logging a completed Pomodoro session.
    - Reporting progress for “Today's Progress”.
- Store session logs (timestamped) in a simple file format (e.g., JSON or CSV).

### Technologies:
- **Flask:** Lightweight Python web framework.

### API Endpoints:

| Endpoint         | Method | Purpose                                                     | Input/Output                 |
|------------------|--------|-------------------------------------------------------------|------------------------------|
| `/`              | GET    | Serve main page (index.html)                                | HTML                         |
| `/static/*`      | GET    | Serve CSS, JS, image assets                                 | File                         |
| `/api/session`   | POST   | Log a session completion. Called by JS when timer hits zero | `{timestamp, ...}` (JSON)    |
| `/api/progress`  | GET    | Return today’s stats for progress section                   | `{count, minutes}` (JSON)    |

#### File Storage:
A line-by-line log in a text, JSON, or CSV file, storing session completions per date/time.

---

## 3. Project Structure Proposal

```
pomodoro-app/
├── app.py            # Flask backend
├── static/
│   ├── style.css     # CSS styles
│   └── timer.js      # JS logic
├── templates/
│   └── index.html    # Main HTML (Jinja template)
├── pomodoro.log      # Session history (text, JSON, or CSV)
└── README.md
```

---

## 4. Frontend-Backend Integration

- On page load, JS fetches `/api/progress` to update progress.
- When the user starts the timer, countdown and display logic run on the client.
- When the timer completes, JS sends a POST to `/api/session` to record the session.
- After logging, JS may re-fetch `/api/progress` to update stats.

---

## 5. Typical Sequence for One Session

1. User loads page `/` — Flask serves index.html and static assets.
2. JS fetches session progress from `/api/progress`.
3. User clicks “Start” — timer animation/countdown starts in browser.
4. Upon completion, JS POSTs to `/api/session` with timestamp.
5. JS updates progress display by calling `/api/progress` again.

---

## 6. Rationale

- **Simplicity**: No authentication/database needed, making the architecture easy to build and understand.
- **Learning Focus**: Clean separation of frontend and backend, showing REST, file I/O, and dynamic frontend updates.
- **Extensible**: Easy to add features (long break tracking, session types, persistent storage) later.
- **UI/UX**: Matches the reference design:

![image1](image1)

---

This architecture ensures a clear division of responsibility, leverages Flask + modern JS, and is ideal for hands-on learning with the Pomodoro technique.