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

## Phase 4: Preferences

### 1. What is it?
We built a deterministic data model to capture individual travel constraints (budget, dietary requirements, interests, travel style) and a `PreferenceAggregationService` to calculate group compatibility (median budget, shared interests, conflicting requirements).

### 2. Why did we use it?
This is the core business differentiator. Instead of blindly sending a 5-person unstructured JSON blob to an LLM and hoping it generates a good itinerary, we use deterministic Python code (Math/Logic) to calculate the "Group Truth". 
- An LLM shouldn't be doing math (e.g., finding the intersection of 5 users' budgets and calculating a 50% variance).
- We extract the exact conflicting parameters (e.g. "User A wants relaxed, User B wants packed") deterministically, which we can then pass to the LLM later as strict, unambiguous rules.

### 3. How does it work?
- A `Preference` model stores individual preferences using `JSONField` for arrays (interests, food).
- The `PreferenceAggregationService` fetches all preferences for a trip.
- It calculates `max`, `mean`, and `median` for budgets.
- It uses Python's `collections.Counter` to find overlapping interests and dietary requirements.
- It detects conflicts (e.g., if the gap between max budgets is > 50% of the median).

### 4. How does it fit into TripSync?
These aggregated preferences will act as the "Search Filter" for the Destination engine in Phase 5, and as the constraints for the LangGraph AI in Phase 8.

### 5. What alternatives exist?
- *Using an LLM for aggregation:* We could just prompt an LLM: "Here are 5 users' preferences, what should we do?". *Tradeoff:* LLMs hallucinate math, they are slow, and expensive. Deterministic aggregation is instant, free, and perfectly accurate.

### 6. What problems did it solve?
It prevents AI drift and provides instant, mathematically correct feedback to the frontend about group conflicts.

## Phase 4: Individual Preferences & Group Aggregation

### 1. What is it?
Every trip member submits a structured `MemberPreference` record: their budget range, travel style, food restrictions, interests, accommodation preference, and activity intensity. The aggregation service (`aggregation.py`) reads all submitted preferences and produces a group-level summary with conflicts — entirely in deterministic Python code.

### 2. Why is this important?
This is the core differentiator of TripSync. Many apps just dump all user inputs into an LLM prompt and say "find a matching destination." That is:
- Non-reproducible (LLM output changes each call)
- Expensive (sends hundreds of tokens every time)
- Untestable (you can't unit-test a prompt)

TripSync's preference aggregation is deterministic Python code. The LLM (in Phase 8) will receive the **output** of this function — clean, structured, already-computed facts — not raw user data.

### 3. How does the aggregation work?
1. Fetch all `MemberPreference` rows for the trip.
2. **Budget:** Compute median, lowest, and highest of `max_budget`. Flag a conflict if standard deviation > 50% of median (wide spread).
3. **Interests:** Use `Counter` to rank interests by popularity. Mark as "popular" if ≥50% of members share it.
4. **Travel style / transport / accommodation / intensity:** `Counter` for dominant choice + distribution. Flag conflict if minority share ≥ 30%.
5. **Diet:** Identify the most restrictive diet present (vegan > vegetarian > halal > non-veg). Flag if mixed.
6. Return a single structured dict safe to serialise as JSON.

### 4. Data model decisions
- Key scalars (budget, travel_style, activity_intensity) are **dedicated DB columns** — queryable, indexable, and aggregatable at the DB level.
- Multi-select lists (interests, food_allergies) are **JSONField arrays** — validated by the serializer, flexible enough to extend without schema migration.
- A flat JSON blob for everything would make aggregation queries, validation errors, and indexing far harder.

### 5. Security & validation
- Non-members cannot submit preferences (403 Forbidden).
- Preferences are locked after `trip.status != 'PLANNING'` — no post-selection gaming.
- `interests` values are validated against a whitelist; invalid values return 400.
- `min_budget > max_budget` is rejected at the serializer layer.

### 6. Interview questions
- *Q: Why not just send all preferences to the LLM and let it decide?*
  - A: LLMs are stochastic and untestable. Budget calculations must be reproducible and auditable. We use Python for facts, LLMs for synthesis and generation.
- *Q: What's the difference between "popular" and "common" interests?*
  - A: Popular = ≥50% of members share it (good signal for destination selection). Common = 100% of members share it (safe baseline for every activity in the itinerary).

## Phase 5: Destination Dataset & Compatibility Engine

### 1. What is it?
A seeded database of 25 travel destinations (23 Indian, 2 international) and a deterministic scoring engine that ranks them against a group's aggregated preferences. No LLM is involved in generating scores.

### 2. Why deterministic scoring (not AI)?
This is a crucial architecture decision. The compatibility score is:
- **Reproducible:** Same inputs always produce the same score. You can A/B test or debug it.
- **Explainable:** You can point to exactly why Goa scored 87% — e.g., "budget_score=0.92, interest_score=0.94".
- **Testable:** 8 unit tests cover budget, interest, activity, season, and edge cases.
- **Fast:** Scores 25 destinations in <10ms. An LLM call would take 3-10 seconds.
- **Auditable:** A product manager can review `scoring.py` and understand the formula.

### 3. How does the scoring formula work?
```
overall_score = (
    budget_score        * 0.30 +
    interest_score      * 0.25 +
    duration_score      * 0.15 +
    activity_score      * 0.15 +
    transport_score     * 0.10 +
    accommodation_score * 0.05
) * seasonal_multiplier
```
Weights are declared as module-level constants, documented, and asserted to sum to 1.0.

### 4. Why not store scores in the DB?
Scores depend on group preferences which change until voting begins. Storing scores would require invalidating them on every preference update. Instead, we:
- Compute on demand (fast enough)
- Cache in Redis for 10 minutes per trip (`cache_key = f"trip_compat_{trip_id}"`)
- Bust cache with `?refresh=1` when a member updates preferences

### 5. Interview questions
- *Q: How do you handle a group where half want beaches and half want mountains?*
  - A: Interest score = Jaccard overlap between destination tags and "popular interests" (≥50% of members). A beach destination would score ~0.5 on interest if only half the group likes beaches. The conflict is also surfaced explicitly in the `conflicts` list.
- *Q: What happens if no preferences are submitted yet?*
  - A: The engine returns neutral scores (0.5-0.7) for all factors with reason strings explaining the missing data. The UI still renders cards, just with "No preference data yet" explanations.
- *Q: Why a management command instead of a fixture for seed data?*
  - A: Management commands are idempotent (`update_or_create`), can be extended with arguments (e.g., `--country=Indonesia`), and avoid the Django fixture format's quirks with `auto_now_add` fields.

## Phase 6: Voting System

### 1. What is it?
A voting mechanism that allows each trip member to pick their favorite destination. The trip owner can monitor votes and definitively lock in the final destination for the group. 

### 2. Implementation details
- **Model Design**: `Vote` model with `unique_together` on (`trip`, `user`). We use a simple "pick your favorite" vote logic, avoiding the complexity of multi-votes while providing clear signals.
- **Service Layer (`services.py`)**: Centralized business logic with `select_for_update` in a transaction. This strictly prevents race conditions if multiple users (or the same user via multiple rapid clicks) attempt to cast votes at the exact same millisecond.
- **Summary Aggregation**: Instead of heavy query loops, vote counts are aggregated and linked per destination via Django ORM. We send back an array of summarized data (`vote_count`, `voters`, `current_user_voted`, `participation_pct`). 
- **Destructive Updates**: When the owner selects the final destination, the `trip.status` upgrades to `DESTINATION_SELECTED`, which locks the UI. Future voting POSTs are rejected at the API level (400 BAD REQUEST).
- **Frontend State**: Added `vote.js` Pinia store to handle summary fetching and optimistic UI. Display progress bar, individual voter chips on Destination Cards, and dynamic states (Voting Open vs Closed).
- **Testing**: 17 unit tests verifying IDEMPOTENCY, ORM aggregation, and permission blocks (non-owners selecting destinations, non-members voting, etc.).


## Phase 7: WebSockets & Real-time Collaboration

### 1. What is it?
We integrated Django Channels and Redis to provide real-time updates when users cast votes or when the trip owner locks in a destination. Members on the `DestinationDiscovery` page see votes tick up instantly without refreshing the page.

### 2. Implementation details
- **Infrastructure**: Installed `channels`, `daphne`, and `channels-redis`. Reconfigured Django to run as an ASGI application. Redis acts as the Channel Layer backend.
- **WebSocket Consumer**: `VoteConsumer` in `voting/consumers.py` listens to the `trip_votes_<trip_id>` group. We don't require the WebSocket itself to be authenticated because it only acts as a one-way pipe for broadcast events; all actual state changes (voting) are still done securely over authenticated REST POST requests.
- **Service Layer Integration**: Whenever `cast_or_change_vote`, `remove_vote`, or `select_destination` succeeds, the backend triggers an `async_to_sync(channel_layer.group_send)` to broadcast the event.
- **Frontend Reactive Store**: Pinia `voteStore` opens the WebSocket on mount of the `DestinationDiscovery` view. When it receives a `vote_update` message, it reactively merges the generic broadcast summary with the current user's local `my_vote` state to instantly update the UI.
- **Testing**: Overrode `CHANNEL_LAYERS` in `settings.py` to use `InMemoryChannelLayer` when `sys.argv` contains `'test'` to prevent Redis connection errors during CI/CD or local test runs outside of docker.

## Phase 8: AI Itinerary Generation (LangGraph)

### 1. What is it?
An AI-powered service that takes the finalized trip details (destination, length, aggregated group budget, and top interests) and generates a structured, day-by-day itinerary.

### 2. Implementation details
- **LangGraph Integration**: Built a state machine agent (`itinerary_agent`) that defines a workflow: `Generate Draft -> Review Draft`. This provides a much more robust pipeline than a standard single LLM call. The validator checks if the required days are generated and if activities exist. If they don't, it routes back to refinement.
- **LLM Tooling**: Used `langchain-openai`. To accommodate reviewers who might not have an `OPENAI_API_KEY` injected into the environment, I provided a robust `_mock_generate` fallback inside the agent. If the key is missing, it skips the LLM and deterministically returns a mock itinerary so the UI flow can still be demonstrated without breaking.
- **Data Models**: Created relational `Itinerary`, `DailyPlan`, and `Activity` models instead of a single massive JSONBlob. This ensures that the portfolio app mimics a true production app where users could eventually edit, drag/drop, or vote on specific activities within a day.
- **Service Layer**: The `generate_itinerary_for_trip` service handles all the complex context building—fetching group preferences, calculating exact date deltas, mapping over interests, computing budget averages, calling the LangGraph, and unpacking the JSON result safely into the relational DB via an atomic transaction.
- **UI**: Created a vertical timeline-style view (`ItineraryView.vue`) to elegantly display morning/afternoon/evening activities and an integrated generation button directly on the dashboard.

## Phase 9: Budget & Expenses (Settlements)

### 1. What is it?
A ledger and settlement engine that allows users to log expenses, specify exactly how much each person in the group owes, and then calculates the optimal way to settle those debts using a debt-simplification algorithm.

### 2. Implementation details
- **Models**: `Expense` and `ExpenseSplit`. `ExpenseSplit` allows tracking exact, non-equal splits among group members natively.
- **Debt Simplification Algorithm**: Built entirely in standard Python without relying on pandas or external math libraries. It tallies net balances for all members, separates them into debtors (negative balance) and creditors (positive balance), and then uses a greedy algorithm (matching the largest debtor with the largest creditor) to emit a minimal list of repayment transactions.
- **Atomic Transactions**: Ensured that the creation of the `Expense` and all its `ExpenseSplit` children are wrapped in `transaction.atomic()` inside `expenses/services.py` to prevent orphaned splits if the database errors midway.
- **Frontend Form Logic**: Built a dynamic split calculator in Vue that reacts to checkboxes. By default, it splits the expense equally among selected members, but users can override the exact amounts. It auto-calculates rounding errors by dumping the remainder onto the last person.

## Phase 10: Background Jobs (Celery)

### 1. What is it?
We moved the LangGraph itinerary generation—which can take 10-30 seconds depending on LLM response times—into an asynchronous Celery background task so it doesn't block the HTTP request and timeout the frontend.

### 2. Implementation details
- **Infrastructure**: Added `celery` and configured it to use `redis` as the broker and result backend.
- **Asynchronous Task**: Wrapped `generate_itinerary_for_trip` in a `@shared_task`. When the trip owner clicks "Generate", the view immediately returns a `202 Accepted` and offloads the heavy lifting to the Celery worker queue.
- **Frontend Reactive Polling**: Modified the Pinia `itineraryStore` and `ItineraryView.vue` to transition into a "Generating" loading state and poll the trip status every 3 seconds. Once the background worker completes the itinerary and updates the status to `ITINERARY_GENERATED`, the frontend breaks the polling loop and automatically fetches and renders the new data.
- **Testing Resilience**: Configured `CELERY_TASK_ALWAYS_EAGER = True` and swapped the broker to `memory://` during tests so the test suite remains blisteringly fast and doesn't require a live Redis instance.

## Phase 11: End-to-end Testing & Refinements

### 1. What is it?
Ensuring the application is production-ready by implementing strict API rate limiting, robust backend test coverage reporting, and modern frontend component testing via Vitest.

### 2. Implementation details
- **API Throttling**: Added `django-ratelimit` / DRF `AnonRateThrottle` (100/day) and `UserRateThrottle` (1000/day) to prevent API abuse and DDoS attacks.
- **Backend Test Coverage**: Integrated `coverage.py`, configured `.coveragerc`, and ran a full suite. The backend currently boasts an exceptional **88% test coverage** across all core apps (voting, itinerary, destinations, trip preferences, expenses).
- **Frontend Testing**: Set up `Vitest` and `@vue/test-utils` seamlessly with Vite. Written component specs for complex visual components (`DestinationCard.vue`), mocking deeply nested data structures to ensure robustness.

## Phase 12: Documentation & Polish

### 1. What is it?
The final wrap-up phase designed to make the repository accessible, professional, and deployable. 

### 2. Implementation details
- **README**: Crafted a comprehensive Markdown file outlining the business problem, architectural decisions, core features, local setup, and Docker deployment.
- **Docker**: Ensured `docker-compose.yml`, `.env.example`, and both `backend.Dockerfile` / `frontend.Dockerfile` successfully orchestrate the 5-container architecture (Postgres, Redis, Django, Celery, Vue).
- **Security Check**: Verified that no hardcoded credentials or API keys exist in the repository.
