# Hoosier Hub Glossary

Quick definitions for terms used across the Hoosier Hub web app, docs, and AI prompts. Each entry references the actual route/model so copilots and reviewers know where it lives.

## Core Concepts
- **Resource** – Any listing in Hoosier Hub (study group, lab, equipment) stored in the `resources` table and rendered at `/resources/<id>`.
- **Owner Inbox** – `/resources/owner/requests`; queue where staff owners approve bookings and respond to direct messages.
- **Waitlist** – Entries in the `waitlist` table when a slot is full; users see them on `/bookings/`, owners/admins see them on schedule views.
- **Waitlist Promotion** – Logic in `src/services/waitlist_service.py` that converts the next waitlist entry into a booking after a cancellation/rejection.
- **Book-for-User** – Admin-only workflow at `/admin/book-for-user` (or “Book this Resource for a User” button) that sets `booked_by_admin=True`.
- **Site Pages** – CMS entries (“About”, “Contact”) stored in `SitePage` model, edited via `/admin/pages` and rendered at `/about` / `/contact`.

## Roles
- **Student** – Can search, book, cancel, leave reviews, and create public resources in the approved student category list.
- **Staff** – Everything students can do plus ownership of restricted resources, self-booking, and access to My Resources dashboards.
- **Admin** – Full control: manage users/resources/bookings, respond to “book for me” requests, edit Site Pages, access analytics, run Book-for-User.

## Booking Lifecycle
- **Pending** – Awaiting owner approval (restricted) or admin action (allocator requests).
- **Approved** – Confirmed booking; slot blocked on calendars.
- **Rejected** – Denied by owner/admin; triggers waitlist promotion when applicable.
- **Cancelled** – User or admin cancelled before start time; slot freed for waitlist or new booking.
- **Completed** – Time window passed; booking eligible for reviews/export.

## Resource Lifecycle
- **Draft** – Saved but hidden (admins/staff preparing listings).
- **Published** – Visible in Discover and detail routes.
- **Archived** – Hidden from search but kept for audit/analytics.

## Feature-Specific Terms
- **Quick Slot Picker** – Three-day slot grid on resource detail + Book-for-User pages showing limited/full states.
- **Request Admin Booking** – Student/staff action on resource detail that creates a `BookingRequest` (`kind="allocator"`) for admins.
- **Direct Message Thread** – Conversation stored in `ResourceConversation` tables; surfaced on resource detail (users) and Owner Inbox (owners).
- **Notification Bell** – Admin navbar dropdown pulling from `Notification` table (`/admin/notifications/<id>/read` marks entries as read).
- **Downtime Block** – Maintenance slot created via `/admin/resource_schedule/<resource_id>` to mark resources unavailable.
- **Nova** – AI concierge served by `assistant_controller`, grounded in `/docs/context`.

_Last updated: November 15, 2025_

