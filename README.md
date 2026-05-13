# Autonomous Customer Support Copilot

An AI-powered customer support web application built using Flask, Groq LLM, SQLAlchemy, and Plotly. The system helps automate customer support queries, detect user intent, escalate critical issues, and visualize support analytics through a dashboard.

---

# Live Demo

[Autonomous Customer Support Copilot](https://autonomous-customer-support-copilot.onrender.com)

---

# Features

- User Authentication (Signup/Login/Logout)
- Multi-Chat Support
- AI-Powered Customer Support Assistant
- Intent Detection System
- Automatic Escalation Handling
- Customer Support Analytics Dashboard
- SQLite Database Integration
- Responsive UI
- Cloud Deployment on Render

---

# Tech Stack

## Backend
- Python
- Flask
- Flask-Login
- Flask-SQLAlchemy

## AI / NLP
- Groq API
- Llama 3 Model

## Frontend
- HTML
- CSS
- JavaScript
- Bootstrap

## Database
- SQLite

## Data Visualization
- Plotly
- Pandas

## Deployment
- Render

---

# Project Structure

```bash
autonomous-customer-support-copilot/
│
├── app.py
├── requirements.txt
├── Procfile
├── .gitignore
├── README.md
│
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── signup.html
│   ├── dashboard.html
│   └── settings.html
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
├── instance/
│   └── copilot.db
│
└── company_docs/
    └── support_data.txt
```

---

# Installation

## Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/autonomous-customer-support-copilot.git
```

## Navigate to Project

```bash
cd autonomous-customer-support-copilot
```

---

# Create Virtual Environment

## Windows

```bash
python -m venv venv
venv\Scripts\activate
```

## Mac/Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

---

# Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Create .env File

Create a `.env` file in the root directory.

```env
SECRET_KEY=your_secret_key
GROQ_API_KEY=your_groq_api_key
```

---

# Run Application

```bash
python app.py
```

---

# Open in Browser

```text
http://127.0.0.1:5000
```

---

# Dashboard Features

- Customer Intent Distribution
- Escalation Analytics
- Support Query Statistics
- Intent-Based Visualization

---

# Supported Intents

- Refund
- Technical Issue
- Password Reset
- Complaint
- General Query

---

# Escalation System

The system automatically escalates high-risk customer queries such as:

- Fraud
- Scam
- Lawsuit
- Account Cancellation
- Severe Complaints

---

# Future Improvements

- Voice-Based Support Agent
- Real-Time Ticketing System
- PostgreSQL Integration
- Email Notifications
- RAG-Based Knowledge Retrieval
- Admin Panel
- Docker Deployment

---

# Deployment

This project is deployed using Render.

---

# Author

Yogita Dokh

---

# License

This project is developed for educational and academic purposes.
