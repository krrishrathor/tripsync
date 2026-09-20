# TripSync

AI-Powered Collaborative Travel Planner

## Overview
Groups of friends often struggle to decide where to travel because everyone has different budgets, interests, travel preferences, and constraints.
TripSync solves this by allowing a group to collaboratively create a trip, submit individual preferences, discover compatible destinations, vote on destinations, and then generate a complete AI-assisted itinerary using a LangGraph multi-agent workflow.

## Phase 1 Status
- Basic project structure initialized.
- Django backend configured with PostgreSQL, Redis, and Celery settings.
- Vue 3 frontend initialized with Vite, Pinia, and Tailwind CSS.
- Docker configuration (`docker-compose.yml` and `Dockerfiles`) created.

## How to run locally

### Using Docker
1. Copy `.env.example` to `.env`
2. Run `docker compose up --build`
3. Access the frontend at `http://localhost:5173`
4. Access the backend API at `http://localhost:8000`

### Local Development (Without Docker)
**Backend**:
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py runserver
```

**Frontend**:
```bash
cd frontend
npm install
npm run dev
```
