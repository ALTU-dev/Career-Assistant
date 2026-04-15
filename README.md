# 🎓 Career Development Assistant (ALT University)

An intelligent Telegram bot designed to help students build careers, generate resumes, find jobs, and prepare for interviews using AI.

Built with **Google Gemini AI + HH.kz API + Telegram Bot API**

---

## 🚀 Features

### 👤 Profile Builder
- Collects student information step-by-step
- Stores data persistently (`users_data.json`)
- Validates inputs (email, phone, etc.)

### 📊 Career Planning (AI-powered)
- Personalized career roadmap
- Skill gap analysis
- Internship recommendations
- 6-month learning plan

### 📄 Resume Generator
- Automatically generates:
  - Resume (CV)
  - Cover letter
- Tailored to Kazakhstan job market

### 💼 Smart Job Search
- Integrates with **HH.kz API**
- AI filters best vacancies
- Supports:
  - No experience (internships)
  - Junior positions
- Provides:
  - Salary info
  - Company details
  - Application links

### 🎤 Interview Training
- Generates realistic HR questions
- Evaluates user answers
- Provides structured feedback

### 🔥 Top Careers
- Shows high-demand professions in Kazakhstan (2025–2026)
- Includes salary insights and required skills

### 📤 HH.kz Auto Publishing
- Automatically creates & publishes resume on HH.kz
- Updates existing resumes
- Generates public resume link

---

## 🧠 AI Integration

Powered by **Google Gemini 2.5 Flash**:
- Context-aware responses
- Career recommendations
- Resume generation
- Vacancy filtering
- Interview analysis

---

## 🛠 Tech Stack

- Python
- pyTelegramBotAPI (telebot)
- Google Generative AI (Gemini)
- HH.kz API
- Requests
- JSON (local storage)

---

## ⚙️ Installation

### 1. Clone repository
```bash
git clone https://github.com/ALTU-dev/career-assistant-bot.git
cd career-assistant-bot
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set API Keys

Open `main.py` and replace:
```bash
TELEGRAM_TOKEN = "your_telegram_token"
GEMINI_API_KEY = "your_gemini_key"
HH_TOKEN = "your_hh_token"
```

### ▶️ Run the bot
```bash
python main.py
```

### 🌍 Localization

- Languages supported:
  - 🇰🇿 Kazakh
  - 🇷🇺 Russian
- Designed for Kazakhstan job market

### 🤝 Contributing

Pull requests are welcome!

### 📄 License

MIT License
