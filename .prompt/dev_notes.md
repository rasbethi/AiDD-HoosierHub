# Dev Notes - AI Usage Log
## Tools I Used

- **Cursor AI (Auto)**: Main coding assistant for pretty much everything - implementation, debugging, refactoring
- **Context Files**: The docs/context/ folder that helps ground AI responses in our actual project
- **Google Gemini API**: For Nova concierge natural language stuff (optional, has fallback)

---

## What I Did With AI Help

### Project Setup & Structure
- **Prompt:** Fix imports in `app.py` and create the missing `src/controllers` structure; reorganize if needed.\n- **What Cursor gave back:** Blueprint-based layout, generated controllers (`main_controller.py`, `auth_controller.py`, etc.), and corrected import paths.\n- **What I changed:** Kept Blueprints, renamed a few files to match our style, and reorganized folders for clarity.

### Database Stuff
- **Prompt:** Fix `flask_sqlalchemy` errors and set up correct relationships.\n- **What Cursor gave back:** Added `Flask-SQLAlchemy==3.1.1`, implemented relationships with cascades, removed manual FK cleanup, fixed circular imports.\n- **What I changed:** Softened some cascades to avoid over-deletes; overall model layer is cleaner.

### Booking System Logic
- **Prompt:** Add time-aware capacity checks (no overlaps, honor limits) across direct, restricted, and admin booking flows.\n- **What Cursor gave back:** Created `booking_rules.py` with `validate_time_block()` and `ensure_capacity()`; centralized validation.\n- **What I changed:** Stress-tested overlapping cases and fixed one time-comparison bug. Centralization removed lots of edge-case bugs.

### Waitlist Auto-Promotion
- **Prompt:** Automatically promote waitlist entries when a slot opens because of cancel/reject.\n- **What Cursor gave back:** `promote_waitlist_entry()` wired into cancellation and rejection, with transactions to avoid races.\n- **What I changed:** Added guards to prevent duplicate promotions during bursts of cancellations; verified end-to-end.

### Nova AI Concierge
- **Prompt:** Make the chatbot fully functional with menus/shortcuts, Gemini intent detection, and deep links.\n- **What Cursor gave back:** Hybrid model (rule shortcuts + Gemini), `MENU_SHORTCUTS`, deep-links, slot-picker integration.\n- **What I changed:** Reordered keywords so “cancel booking” doesn’t match “book”; kept hybrid for speed and reliability.

### Admin Dashboard Reorganization
- **Prompt:** Clean up admin UX and navigation.\n- **What Cursor gave back:** Persistent sidebar/top nav, resource tabs, search/filter chips, consolidated “Scheduling”.\n- **What I changed:** Trimmed a few UI bits; removed the redundant Quick Actions card; navigation is much clearer.

### Owner Inbox & Messaging
- **Prompt:** Build a “Book for me” workflow with threaded messages between owners and admins.\n- **What Cursor gave back:** `BookingRequest(kind=...)`, threaded messaging models, approval and close-request flows.\n- **What I changed:** Expanded message handling to enable future attachments/rich formatting; validated full lifecycle.

### Visual Slot Picker
- **Prompt:** Show available/limited/full slots visually and prefill the form on click.\n- **What Cursor gave back:** Color-coded pills (green/yellow/red) and `build_slot_days()` for a 3‑day view.\n- **What I changed:** Tweaked colors for Hoosier Hub branding; UX kept as provided.

### Data Access Layer Refactoring
- **Prompt:** Move controllers to a DAL and remove deprecated SQLAlchemy usage.\n- **What Cursor gave back:** `resources_dal.py`, `bookings_dal.py`, `waitlist_dal.py`; `db.session.get()`; `db_helpers.get_or_404()`.\n- **What I changed:** Added a few helper methods and standardized file structure; warnings gone; tests pass.

### Python Upgrade & Deprecation Warnings
- **Prompt:** Eliminate `LegacyAPIWarning` and replace `datetime.utcnow()`.\n- **What Cursor gave back:** Replaced with `datetime.now(timezone.utc)` and modern SQLAlchemy APIs; updated requirements for 3.10+.\n- **What I changed:** Manually reviewed all touch points; coverage looked complete.

### Context Files
- **Prompt:** Align context docs with the real app and remove generic/fabricated bits.\n- **What Cursor gave back:** Rewrote concierge guide, updated personas, added Hoosier Hub glossary, removed “mobile app” mentions.\n- **What I changed:** Adjusted persona stories and journey flows based on user testing; ensured docs ground the concierge correctly.

---

## Key Decisions AI Helped With

### 1. Centralized Validation Services

Created booking_rules.py, slot_service.py, waitlist_service.py as separate service modules. AI suggested this to avoid code duplication and ensure consistent business logic. This reduced bugs from inconsistent validation.

### 2. Hybrid AI Concierge

Rule-based shortcuts + Gemini API. AI recommended this to balance reliability (rule-based) with flexibility (LLM). Fast responses for common queries, graceful degradation when API keys are missing.

### 3. Data Access Layer

Introduced DAL modules to encapsulate database operations. AI identified deprecated SQLAlchemy patterns and suggested modern alternatives. Fixed deprecation warnings and improved testability.

### 4. Context-First Documentation

Structured docs/context/ folders to ground AI responses. AI tools perform way better with structured context. This led to more accurate suggestions and fewer hallucinations.

---

## Reflection Questions

### 1. How did AI tools shape your design or coding decisions?

AI influenced a lot of architectural decisions:

- **Service Layer Pattern**: AI suggested extracting booking validation, slot building, and waitlist promotion into separate service modules. Made code organization way better and testing easier.

- **Hybrid AI Approach**: For Nova concierge, AI recommended combining rule-based shortcuts with LLM-based intent detection. Balanced performance with user experience.

- **Modern SQLAlchemy Patterns**: AI found deprecated patterns (Query.get(), datetime.utcnow()) and suggested modern alternatives. Prevented future compatibility issues.

- **Context Grounding**: AI helped structure docs/context/ folders with project-specific knowledge. Improved quality of AI suggestions.

- **UX Improvements**: AI suggested visual slot pickers, color-coded status indicators, and consolidated admin navigation based on workflow analysis.

### 2. What did you learn about verifying and improving AI-generated outputs?

**Always test AI code, especially business logic:**
- Manual testing caught edge cases AI missed. For example, initial waitlist promotion didn't handle concurrent cancellations correctly.
- Code review is essential - AI code can have subtle bugs. Reviewing logic flow and SQL transactions caught issues.
- Incremental integration works better than accepting large refactors wholesale. Test after each step.

**How to improve AI outputs:**
- **Context refinement**: When AI produced generic code, I updated context files to be more specific. This improved subsequent suggestions.
- **Prompt iteration**: "implement booking system" was too vague. "implement time-aware capacity checks with validation functions" got better results.
- **Pattern recognition**: Learned to spot when AI was generating boilerplate vs project-specific logic. Always verified project-specific code against actual requirements.

### 3. What ethical or managerial considerations emerged?

**Ethical stuff:**
- **Academic integrity**: Documented all AI usage here to be transparent.
- **Bias & hallucinations**: AI sometimes generated code that didn't match requirements (like generic "mobile app" references). Had to verify everything against project specs.
- **Dependency risk**: Heavy AI use could reduce my understanding of the codebase. Balanced AI help with manual review and testing.

**Managerial considerations:**
- **Time vs quality**: AI sped things up but required significant verification time. Net benefit was positive, but need to budget for review cycles.
- **Knowledge transfer**: AI-assisted code might be harder for future developers to understand. Kept clear comments and documentation.
- **API key management**: Gemini integration needed secure key management. Implemented graceful fallbacks so app works without API keys - reduces vendor lock-in.
- **Version control**: AI-generated code changes fast during iteration. Used Git branches and PRs to review changes before merging.

**Best practices I established:**
- Always verify AI-generated business logic with manual tests
- Document AI usage and decisions
- Use context files to ground AI responses
- Implement graceful degradation for AI features

### 4. How might these tools change the role of a business technologist or product manager in the next five years?

**For business technologists:**
- **Shift from coding to orchestration**: Less time writing boilerplate, more time designing architectures, defining requirements, verifying AI outputs.
- **Context engineering**: New skill - structuring documentation and prompts to guide AI tools. Quality of context files directly impacts AI output quality.
- **Quality assurance focus**: With AI generating code faster, focus more on testing, security audits, edge case analysis.
- **Domain expertise premium**: AI excels at generic patterns but struggles with domain-specific logic. Deep domain knowledge becomes more valuable for verifying/refining AI outputs.

**For product managers:**
- **Rapid prototyping**: AI enables faster MVP development, test hypotheses and gather feedback quickly.
- **Requirement precision**: Vague requirements lead to poor AI outputs. Need more precise, testable specifications.
- **UX design focus**: AI can generate functional code, but UX design still needs human judgment. PMs focus more on user research and experience design.
- **Technical debt management**: AI generates code quickly but may introduce technical debt if not reviewed. Need to balance speed with maintainability.

**Organizational changes:**
- **AI-first workflows**: Teams structure repositories (like our .prompt/ and docs/context/ folders) to maximize AI effectiveness.
- **Hybrid human-AI collaboration**: Best teams combine AI speed with human judgment - AI for implementation, humans for design/verification/domain expertise.
- **Continuous learning**: AI tools evolve rapidly. Need to continuously learn new capabilities and best practices.

**Risks & mitigations:**
- **Over-reliance on AI**: Teams may lose deep technical understanding. Mitigation: Maintain code review processes, encourage manual testing.
- **Bias in AI outputs**: AI may perpetuate biases from training data. Mitigation: Diverse review teams, explicit bias checks.
- **Vendor lock-in**: Heavy dependence on specific AI tools creates risk. Mitigation: Implement graceful fallbacks, abstraction layers.

---

## Context Files & Impact

| File | Purpose | How AI Uses It |
|------|---------|----------------|
| docs/context/shared/concierge_guide.md | Role-specific instructions for Nova | Grounds AI responses in actual app functionality |
| docs/context/DT/personas.md | User personas | Ensures AI suggestions match user needs |
| docs/context/shared/glossary.md | Hoosier Hub terminology | Prevents AI from using generic/incorrect terms |
| .prompt/golden_prompts.md | Reusable prompt templates | Standardizes AI interactions |

---

## Lessons Learned

1. **Context is critical**: AI tools perform way better with structured, project-specific context. Generic prompts = generic code.

2. **Verify everything**: AI-generated code, especially business logic, must be manually tested. Edge cases are often missed.

3. **Incremental integration**: Large AI-generated refactors should be integrated incrementally with testing at each step.

4. **Documentation matters**: Well-documented code and context files improve AI output quality in subsequent iterations.

5. **Hybrid approaches work best**: Combining AI speed with human judgment (design, verification, domain expertise) produces the best results.

---

## Future AI Enhancements

- Automated test generation for new features
- Code review automation with AI-powered static analysis
- User feedback analysis to suggest UX improvements
- Predictive analytics for resource demand and scheduling optimization
