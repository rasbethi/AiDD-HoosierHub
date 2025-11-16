# OKRs — Hoosier Hub (18-Day Timeline)

These objectives map directly to the features and workflows already live in the Hoosier Hub web app. Each key result is tied to a measurable milestone we track inside GitHub issues and daily standups.

---

## O1. Unified Booking Experience for Students & Staff
**Objective**: Deliver the end-to-end booking flow (discover → slot picker → booking detail → review/waitlist) by Day 10.

- **KR1.1**: Discover page with search, filters, and “Show All” button deployed (list view + real reviews surfaced).
- **KR1.2**: Resource detail page shows slot picker, request admin booking modal, waitlist, messaging, and reviews (shipping now).
- **KR1.3**: `/bookings/` dashboard lists personal bookings + waitlist entries with cancel action and ICS export.
- **KR1.4**: Student review flow works only after completed bookings; aggregate rating updates in real time.
- **KR1.5**: Visual states (available/limited/full) mirror capacity logic; slot picker hides past times.

**Status**: ✅ Live in production branch (validated via AT‑01 + AT‑06).

---

## O2. Owner & Admin Control Center
**Objective**: Equip staff owners and admins with approval, messaging, and CMS tools by Day 13.

- **KR2.1**: Owner Inbox with pending badge + accordion detail shipped (`/resources/owner/requests`).
- **KR2.2**: Owner self-booking + My Resources → Bookings pages (auto-approve for owned slots).
- **KR2.3**: Admin dashboard includes analytics (role usage, resource types, departmental usage).
- **KR2.4**: Admin Inbox + Book-for-User workflow operational with waitlist fallback.
- **KR2.5**: Site Pages editor (`/admin/pages`) lets admins update About/Contact copy; pages render at `/about` and `/contact`.

**Status**: ✅ Live; verified with AT‑02, AT‑03, AT‑04, AT‑05.

---

## O3. AI Concierge & Context Pack
**Objective**: Make Nova (AI concierge) helpful and safe with grounded context by Day 15.

- **KR3.1**: `docs/context/shared/concierge_guide.md` curated; concierge_service reads real snippets + MENU shortcuts.
- **KR3.2**: Gemini integration toggled via env vars with graceful fallback when the SDK isn’t available (Python 3.14 fix).
- **KR3.3**: `.prompt/dev_notes.md` and `.prompt/golden_prompts.md` populated (20+ logged AI interactions, 10+ prompts).
- **KR3.4**: AI Eval plan seeded in `tests/ai_eval/README.md` (scenarios focus on concierge/waitlist/admin flows).

**Status**: ✅ Concierge returning real answers; fallback works without Gemini.

---

## O4. Quality Gates & Tooling
**Objective**: Keep the repo deploy-ready throughout the sprint.

- **KR4.1**: pytest suite green (`python3 -m pytest` run after each major change).
- **KR4.2**: Pyright warnings suppressed only for intentional areas; MVC + DAL enforced.
- **KR4.3**: README, DT/APA/PM docs updated whenever flows change (no stale references to mobile-only features).
- **KR4.4**: New acceptance scenarios committed immediately after features ship (see APA folder).

**Status**: ✅ All gates passing as of November 15, 2025.

---

## O5. Demo-Ready Narrative
**Objective**: Show the complete IU story (student, staff, admin) in the final presentation.

- **KR5.1**: Personas + journey maps (docs/context/DT) rewritten to match our actual web app.
- **KR5.2**: Admin/Owner/Student flows captured in APA acceptance tests for live demo reference.
- **KR5.3**: README includes architecture, setup (Python 3.14), AI-first structure, and troubleshooting steps.
- **KR5.4**: Timeline slide (18 days) mirrors these OKRs for the capstone panel.

**Status**: ✅ Content reviewed with the team; ready for slide deck integration.

---

**Measurement cadence**: Checked in standup + daily GitHub issue updates  
**Success threshold**: All KRs above marked ✅ before final presentation  
**Last updated**: November 15, 2025
