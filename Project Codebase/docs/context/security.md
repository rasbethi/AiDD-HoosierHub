```markdown
# Non-Functional Requirements & Security — Hoosier Hub

This document summarizes the security, reliability, and AI-governance requirements that already apply to the Hoosier Hub web application. Each item maps to concrete code paths or operational practices in the repo.

---

## 1. Server-Side Validation
- All booking forms funnel through `booking_rules.validate_time_block` and `ensure_capacity` (enforces 1–10 hour window, overlapping detection, owner/admin flows included).
- Resource creation/edit routes validate fields (category whitelist, access type, student category restrictions, description length, date parsing) before calling `db.session`.
- Waitlist entries, reviews, and messaging endpoints guard against empty content and enforce relationship ownership.

## 2. XSS & Injection Protections
- SQLAlchemy ORM with parameterized queries is used across controllers (no raw SQL outside controlled migrations).
- Jinja auto-escaping protects templates; the only `|safe` usage is `SitePage.body`, which is edited by authenticated admins.
- No arbitrary file uploads; stock images use remote URLs.

## 3. Password & Session Security
- `User` model stores bcrypt-hashed passwords; seed data uses `set_password`.
- Flask-Login handles session management; inactive/suspended users are blocked via `User.status`.

## 4. CSRF Protection
- Flask-WTF provides CSRF tokens for all forms; POST routes expect `_csrf_token`.
- API-style POSTs (e.g., messaging) still go through Flask form handling, so CSRF remains enforced.

## 5. File Uploads
- Current release does not accept user-uploaded files (resources use URLs). If uploads are added, we will restrict file types/sizes, sanitize filenames, and store outside `/static`.

## 6. Data Privacy & Minimal PII
- User profiles store only name, IU email, department, role, and optional avatar string.
- Admins can deactivate or delete users, fulfilling “right to removal” requests.
- Notifications and messages avoid exposing sensitive info beyond what is necessary for the workflow.

## 7. AI Testing & Verification
- AI concierge (`assistant_controller` + `concierge_service`) grounds responses in `docs/context/shared/concierge_guide.md` and live resource data; if Gemini SDK is unavailable, the fallback uses curated MENU shortcuts (no hallucinated info).
- `tests/ai_eval/README.md` outlines manual/automated scenarios to verify AI output authenticity and tone.
- Nova never fabricates resources: `search_resources` filters only `Resource.STATUS_PUBLISHED` entries.
- AI usage is logged via `.prompt/dev_notes.md`; prompts are curated in `.prompt/golden_prompts.md`.

## 8. Availability & Monitoring
- Booking conflict checks prevent database corruption.
- Waitlist promotion ensures freed capacity is reallocated automatically, reducing manual ops.
- Admin dashboard metrics (pending counts, utilization) help humans spot anomalies quickly.

## 9. Deployment & Tooling
- Linting/type-check: Pyright configuration plus lint pipeline keep the repo clean.
- `python3 -m pytest` executed after major changes; waitlist/booking logic covered by unit tests.

## 10. Testing & Validation Requirements
- Acceptance scenarios in `docs/context/APA/acceptance_tests.md` act as the manual regression suite (AT‑01 through AT‑06 map to all critical student/staff/admin flows).
- Automated unit tests (current focus: booking rules) live under `tests/`; goal is to add more coverage for services (waitlist, messaging, Site Pages).
- AI features follow the plan in `tests/ai_eval/README.md`; concierge responses must be verified against `/docs/context` materials and actual resource data.

These controls are live in the current codebase; refer back here when preparing the final security/NFR section or QA plan.

These controls are live in the current codebase; refer back here when preparing the final security/NFR section of the portfolio or presentation.
```

