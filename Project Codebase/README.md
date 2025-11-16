# Hoosier Hub (CampusResourceHub)

Hoosier Hub is a role-aware campus resource platform built for Indiana University. Students and staff can publish spaces, enforce access rules, manage waitlists, and converse with admins, while administrators gain analytics, AI assistance, and booking controls.

---

## Table of Contents

1. [Overview](#overview)
2. [Feature Highlights](#feature-highlights)
3. [Architecture & Tech Stack](#architecture--tech-stack)
4. [Prerequisites](#prerequisites)
5. [Setup & Quick Start](#setup--quick-start)
6. [Configuration](#configuration)
7. [Running & Developer Workflow](#running--developer-workflow)
8. [Database & Lightweight Migrations](#database--lightweight-migrations)
9. [Demo Accounts](#demo-accounts)
10. [Project Layout](#project-layout)
11. [Troubleshooting & FAQ](#troubleshooting--faq)

---

## Overview

Hoosier Hub centralizes academic resources such as study rooms, labs, equipment, and tutoring circles. Core personas:

- **Students** publish public resources, submit booking or “book-for-me” requests, manage waitlists, and message owners.
- **Staff** own public or restricted resources, auto-approve self-bookings, and respond to restricted access requests.
- **Admins** operate dashboards, approve or forward requests, view analytics, schedule downtime, and manage an AI concierge.

---

## Feature Highlights

- Resource lifecycle (draft → published → archived) with stock image gallery and category rules by role.
- Booking engine with whole-hour validation, recurrence, time-aware capacity, waitlist promotion, and “book this for myself” shortcuts.
- Separate owner and admin inboxes, each with threaded messaging, request histories, and close/deny flows.
- Nova AI assistant backed by Gemini intent detection (optional), knowledge retrieval, and menu shortcuts that deep-link into the UI.
- Admin suite includes usage analytics (by role/category/department), status toggles, downtime blocks, email log, and notification center.
- Reviews, favorites, Google Custom Search boost (optional), messaging owners, and visual slot picker for self-service bookings.

---

## Architecture & Tech Stack

| Layer | Technologies |
| --- | --- |
| Backend | Flask, Flask-SQLAlchemy, Flask-Login, Flask-Limiter, Flask-Talisman |
| Database | SQLite (`instance/app.db`, auto-generated) |
| Frontend | Jinja2 templates, Bootstrap 5, custom CSS/JS under `src/static` |
| Services | Booking rules, slot builder, waitlist promotion, concierge retrieval, Gemini assistant integration, notification logging |

Blueprints live under `src/controllers`, templates under `src/views`, and support services under `src/services`.

---

## AI Integration

Hoosier Hub integrates AI assistance at multiple levels: development workflow, user-facing features, and context grounding.

### AI-Enhanced Features

#### Nova AI Concierge
The Nova assistant (`/assistant/ask`) provides natural language guidance to users:

- **Retrieval-Based Responses**: Grounds answers in project documentation (`docs/context/shared/concierge_guide.md`) and database content
- **Intent Detection**: Uses Google Gemini API (optional) for natural language understanding, with graceful fallback to rule-based shortcuts
- **Deep-Link Navigation**: Menu shortcuts provide direct links to relevant pages (e.g., "how to cancel booking" → `/bookings/`)
- **Role-Aware Suggestions**: Responses adapt based on user role (student, staff, admin)

**Technical Implementation:**
- `src/services/concierge_service.py`: Document retrieval and response formatting
- `src/services/chatbot_service.py`: Gemini API integration (optional)
- `src/static/js/main.js`: Frontend widget for Nova interface

**Graceful Degradation:** If `GEMINI_API_KEY` is not set, Nova uses rule-based keyword matching from `MENU_SHORTCUTS` instead of LLM-based intent detection.

### AI-Assisted Development

The project uses an **AI-first repository structure** to maximize AI tool effectiveness:

- **Context Files** (`docs/context/`): Structured documentation that grounds AI responses in project-specific knowledge
  - `shared/concierge_guide.md`: Role-specific instructions for Nova
  - `DT/personas.md`: User personas for design decisions
  - `shared/glossary.md`: Hoosier Hub-specific terminology
- **Development Log** (`.prompt/dev_notes.md`): Tracks AI usage, prompts, and decisions for academic integrity
- **Golden Prompts** (`.prompt/golden_prompts.md`): Reusable prompt templates for consistent AI interactions

**AI Tools Used:**
- **Cursor AI (Auto)**: Primary coding assistant for implementation, debugging, and refactoring
- **Context Grounding**: Structured documentation ensures AI suggestions match actual application behavior

### Ethical Considerations

- **Transparency**: All AI usage is documented in `.prompt/dev_notes.md`
- **Verification**: AI-generated code is manually tested, especially business logic (booking validation, waitlist promotion)
- **Bias Mitigation**: Context files are reviewed to prevent AI from generating generic or incorrect content
- **Graceful Degradation**: AI features (Gemini API) are optional; the app works without them

### Technical Overview

**AI Service Architecture:**
```
User Query → assistant_controller.py
    ↓
concierge_service.py (retrieval + formatting)
    ↓
chatbot_service.py (Gemini API, optional)
    ↓
Response (menu shortcuts + deep links)
```

**Context Grounding Flow:**
1. User query received via `/assistant/ask`
2. `concierge_response()` checks `MENU_SHORTCUTS` for keyword matches
3. If no match, searches `docs/context/` files for relevant information
4. Formats response with actionable steps and navigation links
5. Falls back to Gemini API for natural language understanding (if API key available)

**Key Files:**
- `src/services/concierge_service.py`: Core concierge logic
- `src/services/chatbot_service.py`: Gemini API wrapper
- `src/controllers/assistant_controller.py`: HTTP endpoint for Nova
- `docs/context/shared/concierge_guide.md`: Knowledge base for Nova responses

### Future AI Enhancements

- **Automated Test Generation**: AI-powered unit test creation for new features
- **Predictive Analytics**: ML models to predict resource demand and optimize scheduling
- **User Feedback Analysis**: AI analysis of reviews to suggest UX improvements
- **Code Review Automation**: AI-powered static analysis for bug detection

For detailed AI usage documentation, see `.prompt/dev_notes.md`.

---

## AI-First Repository Structure

| Path | Purpose |
| --- | --- |
| `.prompt/dev_notes.md` | Running log of AI-assisted work sessions and outcomes. |
| `.prompt/golden_prompts.md` | Curated prompts that consistently yield high-quality results. |
| `docs/context/shared/` | Context pack for copilots (personas, concierge guide, glossary). |
| `src/data_access/` | Dedicated data-access layer so controllers avoid direct ORM calls. |
| `tests/ai_eval/` | Placeholder for scripted evaluations of AI features (Nova concierge). |

This structure keeps Copilot/Cursor grounded in shared context while enforcing a clear MVC + DAL separation.

---

## Prerequisites

- Python 3.10 or newer (upgrade recommended from current 3.9.6 dev box)
- pip
- (Optional) virtualenv for isolation
- SQLite (bundled with Python installations)

Install dependencies with `pip install -r requirements.txt`.

---

## Setup & Quick Start

```bash
# 1. Navigate to the project directory
cd /Users/rasbethi/Downloads/CampusResourceHub

# 2. (Recommended) create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Start the application (default port 5001)
python3 app.py
```

On first launch the application will:
1. Ensure `instance/app.db` exists (created automatically if missing).
2. Run lightweight schema migrations (see below).
3. Seed demo data (users, resources, bookings, reviews) and print login credentials.

Open `http://127.0.0.1:5001/` in a browser. If the port is busy, stop the conflicting process or adjust the port in `app.py`.

---

## Configuration

Both `.env` and `.flaskenv` are loaded automatically. Add whichever keys you need:

| Key | Description |
| --- | --- |
| `SECRET_KEY` | Flask session secret. Defaults to `supersecretkey` if omitted. |
| `GOOGLE_SEARCH_API_KEY`, `GOOGLE_SEARCH_ENGINE_ID` | Powers the “Boost with Google Search” related-term chips on the resource listing. |
| `GEMINI_API_KEY` | Enables Gemini intent detection for Nova. Without it, Nova uses rule-based responses. |

These values are optional; the platform degrades gracefully when they are absent.

---

## Running & Developer Workflow

```bash
cd /Users/rasbethi/Downloads/CampusResourceHub
source .venv/bin/activate      # if using virtualenv
python3 app.py
```

- Blueprints auto-register the main, auth, resource, booking, assistant, and admin routes.
- Templates reside in `src/views`; static assets load from `src/static`.
- During startup the console prints “Booking statuses already up-to-date.” when initialization finishes.

**Common commands**

| Task | Command |
| --- | --- |
| Activate virtualenv | `source .venv/bin/activate` |
| Install dependencies | `pip install -r requirements.txt` |
| Start dev server | `python3 app.py` |
| Run unit tests | `pytest` |
| Open Flask shell | `flask --app app.py shell` |
| Drop local database | `rm instance/app.db` |
| Rerun seeding | See [Reseeding](#re-running-seeds) |
| View simulated emails | Visit `/admin/email-log` |
| Kill stuck port 5001 | `lsof -ti :5001 | xargs kill -9` (macOS/Linux) |

---

## Database & Lightweight Migrations

- SQLite database lives at `instance/app.db`.
- `create_app()` always invokes `db.create_all()` and applies targeted `ALTER TABLE` statements for new columns:
  - `users.status`
  - `messages.request_id`
  - `bookings.decision_at`, `bookings.booked_by_admin`
  - `booking_requests.kind`
  - `waitlist.start_time`, `waitlist.end_time`, `waitlist.purpose`, `waitlist.status`
  - Lifecycle normalization for `resources.status`
- No external migration tool (Alembic) is required for the current scope.

### Re-running Seeds

Seeding runs automatically only when `instance/app.db` does not exist. To force a reseed:

```bash
rm -f instance/app.db
python3 app.py
```

or run the seeder manually:

```bash
python3 - <<'PY'
from app import create_app
from src.data.seed_data import seed_database
app = create_app()
with app.app_context():
    seed_database()
PY
```

---

## Demo Accounts

| Role | Email | Password |
| --- | --- | --- |
| Admin | `admin@campushub.edu` | `admin123` |
| Staff | `sjohnson@faculty.iu.edu` | `staff123` |
| Student | `athompson@iu.edu` | `student123` |

These accounts showcase the admin dashboard, owner inbox, student bookings, and Nova concierge flows.

---

## Project Layout

```
CampusResourceHub/
├── .prompt/                # AI workflow notes (dev_notes, golden prompts)
├── app.py                  # Flask application factory, config, lightweight migrations
├── requirements.txt        # Python dependencies (includes pytest)
├── README.md               # Documentation (this file)
├── docs/context/           # Design thinking, APA, PM, security, concierge context
├── docs/schema_erd.md      # Canonical ER diagram & table definitions
├── instance/app.db         # SQLite database (generated)
├── src/
│   ├── controllers/        # Blueprints (auth, admin, booking, resource, assistant, etc.)
│   ├── data/               # Seed script
│   ├── data_access/        # Encapsulated CRUD helpers (Resources, Bookings, Waitlist)
│   ├── models/             # SQLAlchemy models
│   ├── services/           # Booking rules, concierge, waitlist, notifications, etc.
│   ├── static/             # CSS / JS assets
│   └── views/              # Jinja2 templates (admin, resources, bookings, auth, assistant)
└── tests/
    ├── conftest.py         # Adds src/ to PYTHONPATH for pytest
    ├── test_booking_rules.py
    └── ai_eval/            # Placeholder for AI regression/eval scripts
```

---

## Contribution Workflow

- Use GitHub branches for every feature or fix; open PRs for peer/AI review before merging.
- Capture significant AI-assisted steps inside `.prompt/dev_notes.md` so future collaborators can replay decisions.
- Keep documentation (README + context pack) in sync with structural changes to preserve AI reasoning quality.

---

## Troubleshooting & FAQ

| Issue | Resolution |
| --- | --- |
| Port 5001 already in use | `lsof -ti :5001 | xargs kill -9` to terminate the stuck process, then restart. |
| `ModuleNotFoundError` | Ensure the virtualenv is active and rerun `pip install -r requirements.txt`. |
| Schema mismatch errors | Delete `instance/app.db` and rerun `python3 app.py` to recreate tables via lightweight migrations. |
| Gemini or Google integrations inactive | Confirm the relevant API keys exist in `.env`. The features fall back to rule-based logic if omitted. |
| Need to inspect live data | Run `flask --app app.py shell`, then interact with models (`from src.models.models import User, Resource, Booking, Waitlist`). |
| Notifications not clearing | Use the “Mark as read” option in the admin bell dropdown (routes through `/admin/notifications/<id>/read`). |

For additional support, review the controller/service source files or contact the project maintainer with reproduction steps, expected behavior, and current output.

