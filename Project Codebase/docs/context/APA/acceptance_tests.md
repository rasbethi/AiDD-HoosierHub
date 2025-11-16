# Acceptance Test Scenarios — Hoosier Hub (Web App)

All scenarios use seed data from `src/data/seed_data.py`. Follow them exactly (no guess work) when validating features.

---

### AT-01 (End-to-End UI) — Student books a public resource
**Given**: Alex Thompson (`athompson@iu.edu`, student) is logged in  
**When**:
1. Visits `/resources/` → filters category = “Study Group”
2. Opens “Python Study Group” detail page
3. Uses slot picker to select tomorrow 14:00–16:00
4. Enters purpose “Peer review session” and clicks **Book Resource**

**Then**:
- Booking record created with status `approved` (public resource)
- Success flash shown and entry appears on `/bookings/`
- Slot pill flips to “Booked” state when page reloads
- ICS export includes the new event

**Pass criteria**: Booking row exists with correct start/end, `booked_by_admin=False`, no overlapping bookings allowed. _(This scenario doubles as the required end-to-end UI validation.)_

---

### AT-02 Staff owner approves a restricted booking
**Given**: Staff owner Sarah Johnson (`sjohnson@faculty.iu.edu`) has a pending request on “AI Research Lab - GPU Cluster”  
**When**:
1. Logs in → navbar badge shows pending count
2. Opens `Owner Inbox` (`/resources/owner/requests`)
3. Expands the first pending request and clicks **Approve**

**Then**:
- Booking status transitions `pending → approved`
- Request card moves to “Recently resolved”
- Student requester receives notification (check bell icon)
- Lab capacity reflects the booking on resource schedule

**Pass criteria**: Booking `approved_by` populated with owner_id, notification row exists for requester.

---

### AT-03 Waitlist auto-promotes after admin rejection
**Given**: A restricted booking for “AI Research Lab - GPU Cluster” has a waitlist (`/bookings/waitlist`) entry waiting  
**When**:
1. Admin rejects the active booking via `/admin/bookings` → **Reject & Notify**
2. Reject reason = “Owner requested reschedule”

**Then**:
- Original booking marked `rejected`, waitlist_service creates a new booking for the first waitlist user
- Waitlist entry status flips to `converted`
- Converted booking inherits slot times and status `pending` (since resource is restricted)
- Flash message confirms next person was auto-booked

**Pass criteria**: New booking exists referencing same resource/time, waitlist row `converted`, notification sent to promoted user.

---

### AT-04 Admin books a resource for someone else (Book-for-User)
**Given**: Admin user (`admin@campushub.edu`) wants to book “Collaborative Study Space” for Maya Rivers (`mgarcia@iu.edu`)  
**When**:
1. Opens `/admin/book-for-user`
2. Selects Maya from user dropdown, chooses the resource, uses slot picker to pick next Monday 10:00–12:00
3. Enters purpose “Case competition prep” and submits

**Then**:
- Booking created with `booked_by_admin=True`, status `approved` (resource is public)
- Success alert references Maya by name
- Booking appears on Maya’s `/bookings/` dashboard but not on admin’s personal list

**Pass criteria**: Booking row has `user_id` = Maya, `booked_by_admin=True`, and confirmation flash displayed.

---

### AT-05 Admin updates Site Pages (About/Contact)
**Given**: Admin is logged in  
**When**:
1. Opens `Admin Suite → Site Pages` (`/admin/pages`)
2. Edits Contact page copy to include “Hours: 9AM–5PM ET” and clicks **Save Changes**
3. Visits `/contact` to verify content

**Then**:
- `site_pages` row for slug `contact` updated with new HTML
- Page shows updated copy immediately (no redeploy needed)
- Change attributed to current admin (`updated_by`)

**Pass criteria**: Database row updated, `/contact` renders new content, audit column reflects admin user.

---

### AT-06 Student leaves a review after completed booking
**Given**: Booking seeded for student `athompson@iu.edu` has `status=completed`  
**When**:
1. User visits resource detail page after the booking end time
2. Scrolls to Reviews → submits 5-star rating + comment “Great lighting”

**Then**:
- Review saved (check `reviews` table)
- Aggregate rating badge updates instantly
- User cannot submit another review for the same booking (button disabled)

**Pass criteria**: Single review per user/resource enforced, average rating recalculated server-side.

---

**Execution**: Manual run before each demo + automated regression (pytest) where applicable  
**Coverage goal**: 100% of critical flows (student booking, owner approvals, waitlist, admin tooling, reviews, CMS)  
**Last updated**: November 15, 2025
