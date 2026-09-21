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

## Phase 2: Authentication

### 1. What is it?
We implemented user registration and login using a Custom User Model in Django and JWT (JSON Web Tokens) via `djangorestframework-simplejwt`. The frontend uses a Pinia store and an Axios interceptor to manage tokens and auto-refresh them.

### 2. Why did we use it?
- **Custom User Model:** In Django, it is highly recommended to start with a custom user model (inheriting from `AbstractUser`) even if you don't need extra fields immediately. It saves massive migration headaches later. We set `USERNAME_FIELD = 'email'` because modern apps prefer email login over arbitrary usernames.
- **JWT (JSON Web Tokens):** Since Vue and Django are decoupled (running on different ports/containers), session-based authentication (cookies) requires complex CORS and CSRF configuration. JWTs are stateless; the backend doesn't need to query the database to verify the token signature, which improves scalability.

### 3. How does it work?
- The user logs in via the Vue frontend.
- Django verifies credentials and returns an `access_token` (short-lived, e.g., 5-15 mins) and a `refresh_token` (long-lived, e.g., 1-7 days).
- Vue stores these in `localStorage`.
- Every subsequent Axios request includes the `access_token` in the `Authorization: Bearer <token>` header.
- If the access token expires (401 response), the Axios interceptor catches the error, uses the `refresh_token` to request a new access token, and retries the original request transparently.

### 4. How does it fit into TripSync?
Authentication is the foundation. A user must be authenticated to create a trip, invite members, or cast votes. The custom user model allows us to easily add fields like `profile_image` or global user preferences later.

### 5. What alternatives exist?
- *Session Auth (Cookies):* More secure against XSS, but harder to configure across different domains/ports and less suited for mobile apps.
- *Token Auth (DRF built-in):* Uses long-lived, non-expiring tokens stored in the database. Less secure because if a token is compromised, it never expires until manually revoked.

### 6. What problems did it solve?
It solved the problem of secure, stateless communication between a decoupled SPA (Vue) and an API (Django).

### 7. What tradeoffs exist?
- **Security:** `localStorage` is vulnerable to XSS (Cross-Site Scripting). If an attacker injects malicious JS, they can steal the token. (The more secure, but more complex, alternative is `HttpOnly` cookies for JWTs).
- **Revocation:** JWTs cannot be easily revoked before they expire because they are stateless. If a user changes their password, the old token remains valid until expiration unless a token blocklist (database lookup) is implemented, which defeats the stateless benefit.

### 8. What could go wrong?
- Token interceptors creating an infinite loop if the refresh token itself is expired or invalid. (We prevent this by checking `!originalRequest._retry`).

### 9. What questions might an interviewer ask?
- *Q: Why store tokens in localStorage instead of HttpOnly cookies?*
  - A: LocalStorage is simpler for SPA architectures and mobile app consumption. However, I am aware of the XSS risk. In a strict enterprise scenario, HttpOnly cookies are better, but for this portfolio piece, LocalStorage with a short-lived access token is standard.
- *Q: How do you handle token expiration gracefully?*
  - A: By using an Axios response interceptor that detects a 401 Unauthorized error, pauses the request queue, hits the `/token/refresh/` endpoint, and then replays the failed request.

## Phase 3: Trip Creation & Members

### 1. What is it?
We built the core domain logic for `Trip` and `TripMember` models. The API allows creating a trip, fetching a list of trips the user is part of, retrieving trip details (with member info), generating an invite code, and joining a trip via that code.

### 2. Why did we use it?
Everything in TripSync is scoped to a "Trip". A many-to-many relationship via a "through" table (`TripMember`) is used to attach users to a trip. The through table allows us to store extra data, specifically the `role` (OWNER vs MEMBER) and `joined_at` timestamp.

### 3. How does it work?
- When a user creates a trip, they are automatically added to `TripMember` with the role `OWNER`.
- The `Trip` model overrides `save()` to auto-generate an 8-character url-safe `invite_code` using Python's `secrets` module if one doesn't exist.
- A custom permission `IsTripMemberOrOwner` ensures users can only access trips they have joined, preventing IDOR (Insecure Direct Object Reference) vulnerabilities.
- To join a trip, a user POSTs to `/join/<invite_code>/`. The view checks if the trip exists and if the user is already a member before adding them.

### 4. How does it fit into TripSync?
This is the collaborative container. The `Trip` UUID will be used later as the primary filter for Preferences, Votes, Budget, and LangGraph state.

### 5. What alternatives exist?
- *UUID invite links:* We used a short 8-char `secrets.token_urlsafe` for invite codes instead of the full Trip UUID because short codes are easier to share via WhatsApp/SMS. 

### 6. What problems did it solve?
- Ensures strict data isolation between different groups of users.
- Prevents duplicate memberships using Django's `unique_together` meta class.

### 7. What tradeoffs exist?
- Since anyone with the link can join (if they have an account), it might be less secure than explicit email invites. However, for a consumer travel app, friction-less short-link invites usually provide a better UX. We can regenerate the invite code if a link is leaked.
