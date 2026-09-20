# TripSync Interview Notes

This document is a living guide for preparing for software engineering interviews based on the architecture, decisions, and implementation details of the TripSync project.

## Phase 1: Project Setup & Architecture

### 1. What is the Tech Stack?
- **Backend:** Django (Python), Django REST Framework, Celery.
- **Frontend:** Vue 3 (Composition API), Vite, Pinia, Vue Router, Tailwind CSS.
- **Database:** PostgreSQL.
- **In-Memory Store / Broker:** Redis.
- **Infrastructure:** Docker & Docker Compose.
- **AI Orchestration:** LangGraph (planned for later phases).

### 2. Why did we choose this stack?
- **Django/Python:** Excellent ecosystem for both robust web development (DRF) and AI/ML data processing. Python is the dominant language for LLM tools (LangChain/LangGraph).
- **Vue 3:** A progressive, lightweight framework that scales well. The Composition API provides excellent logic reuse (similar to React Hooks but often considered cleaner).
- **PostgreSQL:** Reliable, supports complex relational queries (essential for the group preference aggregation), and offers JSONB fields for unstructured preference data if needed.
- **Redis:** Serves a dual purpose: caching layer for performance and message broker for Celery and Django Channels (WebSockets).
- **Docker:** Ensures consistency across development, staging, and production environments.

### 3. How does it fit into TripSync?
We need a robust, deterministic backend to handle user management, complex state (trips, budgets, votes), and real-time collaboration. The AI layer is kept isolated and strictly acts as an orchestration engine (LangGraph) that interacts with the deterministic Django core.

### 4. What alternatives were considered?
- *Node.js (Express/NestJS):* Good for real-time, but Python is significantly better suited for LangGraph and AI SDKs.
- *React:* A valid alternative to Vue, but Vue 3 provides a very streamlined development experience for this project scope.
- *MongoDB (NoSQL):* Rejected because TripSync's core domain (Trips, Members, Votes, Itinerary Items, Budgets) is highly relational. A NoSQL approach would make complex preference aggregation and budget settlement algorithms much harder.

### 5. What problems does this setup solve?
- It prevents "AI drift" by strictly separating deterministic business logic (Postgres/Django) from stochastic AI generation.
- It prepares the application for real-time collaboration (Redis/WebSockets) from day one.

### 6. What tradeoffs exist?
- **Complexity:** Running Django, Postgres, Redis, Celery, and Vue locally requires Docker to avoid "it works on my machine" issues.
- **Resource Usage:** Python and Django consume more memory than a lightweight Go or Node backend.

### 7. How would we scale it?
- The frontend can be statically hosted (e.g., S3/CloudFront or Vercel).
- The Django backend can scale horizontally behind a load balancer.
- PostgreSQL can be scaled vertically, and read replicas can be added for heavy query loads (like browsing destinations).
- Celery workers can be scaled horizontally to handle high volumes of AI itinerary generation tasks independently of the web server.

### 8. What questions might an interviewer ask?
- *Q: Why use Celery for AI generation instead of synchronous API calls?*
  - A: AI generation (especially multi-agent LangGraph workflows) can take 30-90 seconds. Synchronous HTTP requests would time out. Celery allows us to offload the work and notify the user via WebSockets when done.
- *Q: Why PostgreSQL over MongoDB for a flexible app like this?*
  - A: Travel planning is highly relational (User -> Trip -> Itinerary -> Expenses). Calculating budgets and settling expenses requires ACID compliance. For flexible data like specific user dietary requirements, Postgres' `JSONB` gives us NoSQL flexibility within a relational model.
