# 🤖 AI Chatbot using Gemini API

This project is a feature-rich AI-powered chatbot web app built with Flask and Google Gemini API. It supports voice input, multi-file upload & analysis, dark/light mode, file conversion, and personalized user profiles.

## 🌟 Features

- 🧠 Chat with Gemini Pro model (Creative/Technical modes)
- 📂 Multi-file upload (PDF, DOCX, TXT, CSV, JSON, XLSX, etc.)
- 📝 Document summarization & Q&A
- 🎤 Voice input using microphone
- 🔁 File type conversion (.txt/.pdf/.docx)
- 🌗 Persistent dark/light mode toggle
- 💾 Export chatbot response (.txt/.pdf/.docx)
- 🔍 Chat history with search and threading
- 📈 Admin usage analytics (peak usage, most common queries)
- 👤 User profiles with password change & session timeout
- 👍 Feedback system for AI response rating

## 💻 Technologies Used

- Python (Flask)
- HTML, CSS, JavaScript
- Google Generative AI (Gemini Pro)
- SQLite (with schema for users, history, feedback)
- PDF/DOCX/CSV processors: `PyPDF2`, `python-docx`, `pandas`, `fpdf`

## 🚀 Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/AI_chatbot.git
cd AI_chatbot
