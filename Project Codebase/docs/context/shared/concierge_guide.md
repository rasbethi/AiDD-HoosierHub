### Cancel a booking (students/staff)
1. Open **My Bookings** (`/bookings/`).  
2. Click **Cancel Booking** on the card or open the detail page and use the **Cancel Booking** panel.  
3. The slot reopens immediately (or the next waitlisted user is promoted).  

### Cancel a booking (admins)
1. Go to **Admin Suite › Bookings** (`/admin/bookings`).  
2. Use **Edit / Cancel** to open the booking detail screen.  
3. Click **Cancel Booking & Notify User**; the user and waitlist are updated automatically.  

### Publish / edit a resource
- **Students:** use **Add Resource** (`/resources/create`). Only the approved student categories (Study Group, Peer Tutoring Circle, Club Resource, Case Prep Room) are available and all listings must be public.  
- **Staff:** use the same form; staff can pick any category, add new categories, and mark resources as restricted.  
- **Admins:** open **Admin › Resources** (`/admin/resources`) then **Add Resource** to publish on behalf of any owner (select the owner from the dropdown, set status draft/published, etc.).  

### Owner inbox & direct messages
- The Owner Inbox lives at `/resources/owner/requests`. It shows booking approvals *and* all direct message threads.  
- You can also reach it from the profile dropdown (**Messages**) or from **My Spaces › Owner Inbox**.  
- Each conversation keeps a threaded history; replies go back to the user’s Messages panel on the resource page.  

### Admin inbox & requests
- Admin-only “book for me” and escalation threads live under `/admin/inbox` (unified inbox).  
- Detailed request filtering is available at `/admin/requests` (status + resource filters).  
- Admins can allocate resources directly from a request via the **Book Resource** shortcut.  

### Message a resource owner
1. Open the resource detail page (`/resources/<id>`).  
2. Scroll below the reviews to **Message the Owner**.  
3. Review the thread (if any) and send a new message; replies arrive in the owner’s inbox.  

### Booking & waitlists
1. Use the **Book this Resource** panel on the detail page.  
2. Pick a quick slot or enter custom times, choose recurrence if needed, and submit.  
3. If the slot is full, the page prompts you to **Join the Waitlist** with the selected time prefilled.  
4. Waitlist entries appear under **My Bookings › Waitlisted Requests** and in the owner/admin schedule views.  

### Request admin booking / book on behalf
- Students/staff: click **Request Admin Booking** on a resource detail page; admins receive it in `/admin/requests`.  
- Admins: use `/admin/book-for-user` (or the **Book this Resource for a User** button on the detail page) to schedule directly for someone else.  

### Helpful routes the concierge can cite
- `/resources/` — browse/filter the catalog.  
- `/bookings/` — review or cancel your reservations, download iCal.  
- `/resources/owner/requests` — booking approvals + messages for owners.  
- `/admin/bookings` — admins manage any booking.  
- `/admin/resources` — manage/publish listings as an admin.  
- `/admin/inbox` and `/admin/requests` — handle escalated requests.  
- `/admin/book-for-user` — admin allocation form.

### Context Grounding Requirement
- When Nova references personas, use `docs/context/DT/personas.md` and `journey_maps.md` (e.g., Maya uses slot picker, Dr. Iyer checks Owner Inbox, Marcus edits Site Pages).
- When explaining booking/waitlist behavior, cite acceptance criteria from `docs/context/APA/acceptance_tests.md` (AT-01 through AT-06).
- For security/NFR answers, rely on `docs/context/security.md` (CSRF, validation, AI fallback).
- If Nova cannot ground a response in these docs or live resource data, it should return the MENU shortcut or say it lacks reliable information—never invent new facts.

