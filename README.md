# TripSync 🌎✈️

<p align="center">
  <em>An AI-powered, real-time collaborative travel planner for groups of friends.</em>
</p>

![TripSync Overview](https://via.placeholder.com/1200x600.png?text=TripSync+Dashboard)

## Why TripSync?

Planning group trips is notoriously painful. Everyone has different budgets, different food preferences, conflicting schedules, and wildly varying ideas of a "good vacation" (e.g., relaxing on a beach vs. waking up at 5 AM to hike a mountain). 

**TripSync** solves this by:
1. **Aggregating Preferences**: Each member submits their individual budgets, dietary restrictions, and travel styles.
2. **AI-Powered Discovery**: An intelligent algorithm finds and scores destinations that best match the entire group's constraints.
3. **Real-time Voting**: Users vote on destinations collaboratively via WebSocket-powered real-time updates.
4. **Autonomous AI Itinerary Generation**: Once the group locks in a destination, LangGraph AI dynamically generates a fully fleshed-out daily itinerary.
5. **Debt Simplification**: An integrated expense tracker simplifies shared group debts, calculating exactly who owes whom using a minimal-transaction greedy algorithm.

---

## Architecture & Tech Stack

This is a production-style, monolithic full-stack application demonstrating modern system design.

### Backend
- **Framework**: Django & Django REST Framework (DRF)
- **Database**: PostgreSQL (relational models for Users, Trips, Destinations, Ledgers)
- **Real-Time Engine**: Django Channels & Daphne (ASGI)
- **Background Jobs**: Celery & Redis (for asynchronous AI generation tasks)
- **AI Integration**: LangGraph & LangChain (OpenAI)
- **Security**: JWT Authentication, Role-based API permissions, Throttling/Rate-limiting (1000/day).
- **Testing**: 88% overall backend test coverage via `pytest` and `coverage.py`.

### Frontend
- **Framework**: Vue.js 3 (Composition API) & Vite
- **State Management**: Pinia
- **Styling**: Tailwind CSS (v4)
- **Routing**: Vue Router
- **Component Testing**: Vitest & Vue Test Utils

---

## Core Features

- **Authentication**: Secure JWT-based login and registration.
- **Trip Dashboards**: Centralized hub displaying live group status, invite links, and active phases.
- **Preference Matrix**: Individual preference inputs mapped to a collective compatibility report.
- **Algorithmic Scoring**: Backend dynamically scores destinations from 0-100% based on overlapping group criteria and active conflicts.
- **Real-Time Collaboration**: Django Channels broadcast WebSocket events instantly when votes are cast or retracted.
- **LangGraph Itinerary Agent**: A sophisticated multi-node state machine that drafts, validates, and refines a daily schedule based on the group's exact constraints.
- **Smart Debt Ledger**: Allows unequal splitting (e.g., "Alice pays 100, Bob pays 200"). Automatically reduces a web of debts into minimal peer-to-peer transactions.

---

## Local Setup & Development

### 1. Requirements
- Python 3.12+
- Node.js 20+
- Redis (Running locally on port `6379`)
- PostgreSQL (or rely on default SQLite for immediate prototyping)

### 2. Backend Setup
```bash
# Navigate to backend
cd backend

# Create virtual environment and install dependencies
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create .env and add your OpenAI Key (optional)
echo "OPENAI_API_KEY=your_key_here" > .env

# Run migrations
python manage.py migrate

# Load initial destination data (Optional but recommended)
python manage.py load_destinations

# Start the Daphne ASGI server (needed for WebSockets)
daphne -p 8000 config.asgi:application
```

### 3. Celery Worker (New Terminal)
```bash
cd backend
source venv/bin/activate
celery -A config worker -l info
```

### 4. Frontend Setup (New Terminal)
```bash
cd frontend
npm install
npm run dev
```
Navigate to `http://localhost:5173`.

---

## Docker Deployment (Production-Ready)

TripSync includes a fully containerized architecture mapping Postgres, Redis, Django, Daphne, Celery, and Vue.

```bash
# 1. Rename the example environment file
cp .env.example .env

# 2. Add your OpenAI API key to .env

# 3. Spin up the cluster
docker-compose up --build
```
*Note: The frontend builds via Vite and proxies `/api` calls directly to the Django container.*

---

## Testing

**Backend (Coverage)**
```bash
cd backend
coverage run manage.py test
coverage report -m
```

**Frontend (Vitest)**
```bash
cd frontend
npm run test
```

---

## System Design Highlights

- **Thick Backend / Thin Frontend**: Complex scoring, aggregation, and AI orchestration happens securely on the backend. The frontend remains a lightweight, reactive view layer.
- **State Machine AI**: The LangGraph agent employs a `Generate Draft` -> `Validate` loop to ensure itineraries do not exceed the group's stated budget before returning data.
- **Graceful Fallbacks**: If no `OPENAI_API_KEY` is provided, the backend seamlessly falls back to a deterministic, locally mocked JSON itinerary generator so reviewers/developers can still test the flow.
- **Atomic Ledgers**: The `add_expense` service is wrapped in `transaction.atomic()` to guarantee that parent expenses and their child splits are never orphaned.

---
*Built with ❤️ for collaborative travel.*
