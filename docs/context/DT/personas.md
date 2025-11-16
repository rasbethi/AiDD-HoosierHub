# User Personas — Hoosier Hub

These personas are derived from interviews with students, staff owners, and campus administrators at Indiana University. Each persona maps directly to flows implemented in Hoosier Hub (slot picker, owner inbox, admin analytics).

---

## Persona 1 – **Maya Rivers, Kelley Student Entrepreneur**
- **Role**: Junior, Kelley School of Business (runs a peer coaching circle)
- **Tech confidence**: Power user of IU web tools (Canvas, Zoom, Google Workspace)
- **Behaviors**:
  - Books shared spaces 2–3 times per week at odd hours (evenings/weekends)
  - Logs into Hoosier Hub from her laptop between classes or late evenings
  - Saves favourite rooms to reuse the same setup
- **Goals**:
  - Publish her tutoring circle so freshmen can RSVP
  - Self-book owned resources instantly without approvals
  - Track reviews to prove credibility when recruiting new members
- **Pain points before Hoosier Hub**:
  - Had to email building managers for every session
  - Couldn’t see how many people were already on the waitlist
  - Lost sign‑ups because confirmations got buried in email threads
- **Key quotes**: “If I can’t confirm a space in a minute, my attendees assume it’s not happening.”
- **Design implications**:
  - Prominent “My Resources → Bookings” dashboard
  - Visual slot picker that hides past times and shows capacity by color (desktop-first but responsive)
  - Owner self-book flow that bypasses approval and auto-notifies the group

---

## Persona 2 – **Dr. Priyanka Iyer, Eskenazi Lab Steward**
- **Role**: Staff research coordinator managing a restricted bio-lab
- **Tech confidence**: Comfortable with desktop dashboards, cautious about mobile
- **Behaviors**:
  - Reviews owner inbox each morning and after lunch
  - Annotates booking requests with context (purpose, safety training status)
  - Exports waitlist data weekly for compliance audits
- **Goals**:
  - Enforce access rules (restricted vs public) without juggling spreadsheets
  - Approve or reject bookings with a single click and auto-notify requesters
  - See downtime blocks alongside bookings to plan maintenance
- **Pain points before Hoosier Hub**:
  - Students would overbook GPUs, leading to conflict
  - No timeline view showing downtime vs. active slots
  - Tracking who had keycard access required separate systems
- **Key quotes**: “I just want a queue that shows who’s next and whether they’re even allowed in the lab.”
- **Design implications**:
  - Owner inbox badge with pending counts in the navbar
  - Booking detail view that surfaces approval history and purpose
  - Waitlist promotion automation that re-checks capacity and logs the actor

---

## Persona 3 – **Marcus Holloway, Campus Operations Analyst**
- **Role**: Central admin within University Facilities & Scheduling
- **Tech confidence**: Expert; builds dashboards in PowerBI/Tableau
- **Behaviors**:
  - Lives in the admin dashboard each morning to scan KPIs
  - Uses the “Book for User” form to help departments with VIP visits
  - Reviews email logs to ensure notification delivery
- **Goals**:
  - Remove bottlenecks by reallocating requests to the right owners
  - Maintain Hoosier Hub content (About/Contact) and broadcast updates
  - Pull department-level utilization reports for leadership
- **Pain points before Hoosier Hub**:
  - Couldn’t see cross-department usage from one place
  - Manual email follow-ups whenever a booking was cancelled
  - CMS tasks (updating contact info) required someone from Web Services
- **Key quotes**: “If I see a spike in waitlists for study rooms, I need evidence to lobby for more space.”
- **Design implications**:
  - Admin analytics cards grouped by role/resource type
  - Editable Site Pages (About/Contact) inside Admin Suite
  - Quick action bar linking to Requests, Bookings, Resources, and Site Pages

---

## Persona Snapshots → Feature Mapping
| Persona | Primary Journeys | Critical Features |
| --- | --- | --- |
| Maya (student entrepreneur) | Discover → Book → Review | Desktop-friendly slot picker, favourites, My Resources dashboard |
| Dr. Iyer (staff steward) | Owner Inbox → Approve/Reject → Waitlist | Pending badge, detailed booking cards, auto-promotion |
| Marcus (admin analyst) | Admin dashboard → Requests → Pages | Analytics KPIs, Book-for-User, Site Pages editor |

Each sprint review verifies changes against these personas to keep Hoosier Hub grounded in IU-specific needs.
