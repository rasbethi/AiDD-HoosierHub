# Journey Maps — Hoosier Hub

These maps illustrate the real IU workflows we designed around. Each stage highlights touchpoints within Hoosier Hub plus supporting features (notifications, analytics, waitlist, etc.).

---

## 1. Maya (Student) — Publish & Book a Peer Coaching Session

| Stage | Touchpoints | Notes |
| --- | --- | --- |
| Discover | `Discover` nav → filters (category/capacity) | Browses published resources, sees recent reviews and “Book this for me” CTA on cards. |
| Decide | Resource detail → quick slot grid | Chooses date/time, purpose, recurrence. Slot picker shows limited/full badges that map to booking capacity logic. |
| Book | Booking form (server validation 1–10 hrs) | If public: instantly approved + confirmation flash. If restricted: status = pending with owner notification. |
| Confirm | `/bookings` dashboard + notification badge | Sees start/end times, cancel button, links to ICS export (top of dashboard). |
| Amplify | Review & Message panels on resource detail | Leaves review after booking, toggles favourite heart, sends message to owner if logistics change. |

**Support features**: desktop-responsive slot picker, favourites table, waitlist modal with pre-filled start/end, `/bookings/export` ICS link, review component tied to `Review` model.

---

## 2. Dr. Priyanka Iyer (Staff) — Approve & Manage a Restricted Lab

| Stage | Touchpoints | Notes |
| --- | --- | --- |
| Intake | Navbar badge → `Owner Inbox` (`/resources/owner/requests`) | Pending count pulled via context processor; accordion lists owner requests + direct messages. |
| Review | Request detail accordion | Shows requester info, slot, purpose, message history. Buttons for approve/reject feed `resource_bp.owner_approve_booking`/`owner_reject_booking`. |
| Decide | Approve/Reject actions | Approve auto-approves booking + notifies user. Reject triggers waitlist promotion helper if capacity frees up. |
| Monitor | `My Resources → Bookings` (`/resources/owner/bookings`) | Staff sees upcoming slots, can self-book using owner quick form; downtime blocks visible from admin schedule too. |
| Follow-up | Messaging thread + notifications | Owner sends clarifications via conversation thread; notifications update via navbar bell. |

**Support features**: owner_pending_count context, request accordion UI, waitlist_service promotion, owner self-book route, notification service hooks.

---

## 3. Marcus Holloway (Admin) — Triage “Book for Me” Requests & Update Site Pages

| Stage | Touchpoints | Notes |
| --- | --- | --- |
| Scan | `/admin/` dashboard | Sees total bookings/pending counts, SLA tiles, utilization list to decide what needs attention. |
| Act | Quick actions → `Admin Inbox` (`/admin/inbox`) or `Book for User` | Inbox has two tabs (allocator vs owner approvals). Book-for-User form mirrors resource detail slot picker and supports waitlist submit when full. |
| Resolve | Request detail view (`/admin/requests/<id>`) | Approve/deny/close with note logging; restricted bookings escalate owner approval flow via booking_service. |
| Communicate | Email log (`/admin/email-log`) + Site Pages (`/admin/pages`) | Verifies notifications were sent; edits About/Contact content using SitePage model. |
| Report | Dashboard analytics + upcoming features | Uses role/type charts to share insights; export endpoints feed stakeholders when needed. |

**Support features**: Admin Suite menu, admin_inbox filters, book_for_user slot builder, SitePage editor, notification log view.

---

These journey maps guide UX conversations: when someone proposes a change, map it to the relevant persona + stage to confirm we’re improving a real IU scenario.*** End Patch

