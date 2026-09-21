# 🏟️ SmartSports: Facility Management & Revenue Optimization Platform

SmartSports is an intelligent, full-stack sports facility booking and automated revenue management platform powered by **Agentic AI (Google Gemini)**, **FastAPI**, and **React 19 (Tailwind CSS)**.

---

## 🌟 Key Features

### 👤 1. Customer Portal
- **Court Discovery & Filters**: Real-time slot search with instant sport (`Football`, `Badminton`), calendar date picker, and time-of-day filters (`Morning`, `Afternoon`, `Evening`).
- **One-Click Court Booking**: Instant reservation flow with wallet balance simulation and availability locking.
- **AI Booking Assistant**: Natural-language conversational booking agent with function calling to query available courts and confirm reservations.
- **My Bookings Dashboard**: Clean reservation overview with booking details and one-click cancellation.

### 🛡️ 2. Admin Operations & Revenue Console
- **Pricing Strategy & Yield Engine**: Dynamic pricing recommendations based on real-time court demand, lead time, and historical fill rates.
- **Rate Approvals**: Human-in-the-loop review workflow for approving or customizing AI-suggested rates with override capabilities.
- **Facility Analytics**: Court utilization and gross revenue breakdown visualizations.
- **Customer Segmentation & Notification Audit**: Targeted promotional offer dispatching for off-peak and unfilled slots.

---

## 🏗️ Architecture

```
SmartSports/
├── agent/                  # AI agents & function calling tools (Gemini)
│   ├── booking_tools.py    # Search & booking tools for LLM
│   ├── customer_agent.py   # Conversational booking assistant
│   └── revenue_agent.py    # Revenue optimization decision engine
├── analytics/              # Demand, fill rate & profit calculation modules
├── backend/                # Production FastAPI REST API
│   └── main.py             # API endpoints & Swagger documentation
├── data/                   # Dataset generation scripts & CSV files
├── database/               # SQLite database & schema definitions
├── frontend/               # React 19 + Vite + Tailwind CSS web app
├── run_v2.bat              # One-click launcher script
└── requirements.txt        # Python backend dependencies
```

---

## 🚀 Quick Start Guide

### Prerequisites
- **Python 3.10+**
- **Node.js 18+** & `npm`
- **Google Gemini API Key** (from [Google AI Studio](https://aistudio.google.com/))

---

### Step 1: Clone the Repository
```bash
git clone https://github.com/<your-username>/<your-repo-name>.git
cd <your-repo-name>
```

### Step 2: Set Up Environment Variables
Create a `.env` file in the root directory:
```bash
cp .env.example .env
```
Add your Gemini API key inside `.env`:
```env
GEMINI_API_KEY=your_api_key_here
```

### Step 3: Install Backend Dependencies & Seed Database
```bash
pip install -r requirements.txt
python seed_data.py
```

### Step 4: Install Frontend Dependencies
```bash
cd frontend
npm install
cd ..
```

---

## 🏃 Running the Application

### Option A: One-Click Launch (Windows)
Double-click `run_v2.bat` in the project root.

### Option B: Manual Launch (Two Terminals)

**Terminal 1 — FastAPI Backend:**
```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

**Terminal 2 — React Frontend:**
```bash
cd frontend
npm run dev
```
- Web Application: [http://localhost:5173](http://localhost:5173)

---

## 📄 License
This project is licensed under the MIT License.
