# Golden Prompts

Use these templates when working with AI copilots to keep responses focused and context-aware.

## Admin Workflow Triage
```
You are Nova, the Hoosier Hub assistant. Review the current admin dashboard metrics (bookings, waitlist, notifications) and suggest the next best action. Reference docs/context/shared/concierge_guide.md.
```

## Booking Logic Review
```
Given booking_rules.validate_time_block and waitlist_service.promote_waitlist_entry, explain how the system enforces 1-10 hour limits and capacity-aware waitlists. Cite relevant files.
```

## Concierge Context Injection
```
You are Nova. A user asked: "{{user_query}}". Reference docs/context/shared/concierge_guide.md and summarize 2-3 actionable steps plus one direct navigation link. Respond with friendly bullet points.
```

## AI Waitlist Regression
```
Run through the waitlist promotion flow using waitlist_service.promote_waitlist_entry and admin_controller.reject_booking. List the SQL tables touched, expected status transitions, and any notifications sent.
```

## Admin Dashboard Insight Pulse
```
Using src/controllers/admin_controller.py and src/views/admin/dashboard.html, summarize the KPIs shown (bookings totals, SLA, utilization). Recommend one follow-up action for each metric that looks risky.
```

## Owner Inbox Troubleshooting
```
Analyze src/controllers/resource_controller.py (owner_requests, owner_approve_booking, owner_reject_booking). Explain how pending requests move between inbox tabs, which notifications fire, and how waitlist promotion is triggered. Output a checklist owners can follow when buttons "do nothing."
```

## Slot Picker Consistency Audit
```
Inspect slot_service.build_slot_days and templates resources/detail.html + admin/book_for_user.html. Verify that booked/limited/full states render consistently and identify any mismatched CSS classes. Suggest fixes if a state is missing.
```

## Notification Routing Review
```
Trace send_notification usage in resource_controller, admin_controller, and waitlist_service. Produce a table of (event -> recipients -> message key) so we can confirm every workflow pings the correct user.
```

## Data Access Layer Health Check
```
Look at src/data_access/*.py and note which controllers call each helper. Identify gaps where controllers still hit models directly and propose DAL stubs we should add.
```

## Gemini/Concierge Failover Prompt
```
If google-generativeai is disabled, describe how concierge_service.concierge_response falls back to MENU_SHORTCUTS/search_context_docs. Provide a ready-to-send explanation to an instructor proving we handle missing API keys gracefully.
```

## Advanced Search Smoke Test
```
Simulate a request to resource list with `boost_search=true`. Detail the call sequence: controller -> external_search.fetch_related_terms -> template chips. List common failure points (missing env vars, API quota) and mitigation steps.
```

## Booking Request Lifecycle
```
Using models (BookingRequest), booking_service.create_owner_booking_request, admin_controller.list_requests/view_request, narrate the full lifecycle from student "book for me" submission through admin allocation and owner approval. Highlight status transitions and fields updated.
```

## Python Upgrade Checklist
```
Summarize how to move the project to a new Python version: install via Homebrew, adjust ~/.zshrc, recreate .venv, reinstall requirements, run pytest. Base your answer on .prompt/dev_notes.md entries.
```

## Persona-Guided Walkthrough
```
From docs/context/shared/concierge_guide.md, pick a persona and generate a "day in the life" using actual routes (e.g., /resources/create, /resources/owner/requests). Include nav hints for that persona.
```

## AI Eval Scenario Generator
```
Draft a test plan for tests/ai_eval/README.md covering 3 scenarios: concierge answering booking question, Nova suggesting owner actions, and waitlist auto-promotion. For each, list prompt, expected actions, and metrics to capture.
```
