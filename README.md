# 📚 StudyTrack — Full Stack Study Tracker

A modern, feature-rich study tracking web application built with Flask + SQLite.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the App
```bash
python app.py
```

### 3. Open in Browser
Visit: http://localhost:5000

---

## 🌟 Features

| Feature | Description |
|---------|-------------|
| 🔐 Auth | Register, Login, Logout with password hashing |
| 📊 Dashboard | Daily tasks, streak, reminders, Pomodoro timer |
| ✅ Checklist | Add/edit/delete/complete tasks with priority |
| 📅 Timetable | Weekly schedule view + list view |
| 📈 Analytics | Charts for tasks, subjects, hours |
| 💪 Motivation | Daily quotes, challenges, mood tracker |
| 🎓 Study Tips | 9 proven techniques with step-by-step guides |
| 🤖 Chatbot | Rule-based AI assistant for study advice |
| 👥 Collaboration | Create/join study groups + group chat |
| 👤 Profile | Edit profile, theme customization |
| 🎨 Themes | Dark/Light mode + 6 color accents |
| ⏰ Reminders | Set alarms with browser notifications |
| 🔥 Streaks | Daily streak tracking with achievement badges |

## 📁 Project Structure

```
study-tracker/
├── app.py              # Flask backend (all API routes)
├── database.db         # SQLite database (auto-created)
├── requirements.txt    # Python dependencies
├── templates/
│   ├── base.html       # Base HTML template
│   ├── layout.html     # App shell with sidebar
│   ├── login.html      # Login page
│   ├── register.html   # Registration page
│   ├── dashboard.html  # Main dashboard
│   ├── checklist.html  # Task management
│   ├── timetable.html  # Weekly timetable
│   ├── analytics.html  # Charts & stats
│   ├── motivation.html # Quotes & challenges
│   ├── tips.html       # Study techniques
│   ├── chatbot.html    # AI assistant
│   ├── collaboration.html # Study groups
│   └── profile.html    # User profile & themes
└── static/
    ├── css/style.css   # Complete design system
    └── js/main.js      # Shared utilities
```

## 🛠 Tech Stack
- **Backend**: Python 3.x + Flask
- **Database**: SQLite (via sqlite3)
- **Frontend**: HTML5 + CSS3 + Vanilla JavaScript
- **Charts**: Chart.js
- **Fonts**: Syne + DM Sans (Google Fonts)
