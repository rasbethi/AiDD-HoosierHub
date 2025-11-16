# Agility, Processes & Automation (APA) — Hoosier Hub

This folder records the “definition of done” for the workflows we actually shipped in Hoosier Hub. Instead of generic BPMN diagrams, we maintain executable acceptance tests that match our code paths (slot picker booking, owner approvals, waitlist promotion, admin book-for-user, Site Pages editor).

## Contents
- **acceptance_tests.md** — Acceptance criteria for the live flows (students, owners, admins). Each scenario references real seed users/resources so QA or instructors can replay them.

## How We Use It
- During sprint reviews we walk through these tests to prove features work end to end (no guess work).
- When filing regressions we reference the scenario ID in the bug report.
- Future automation (pytest/Playwright) will mirror these steps exactly, so this file is the canonical source for workflow expectations.

If a feature changes (e.g., new approval rule, extra notification), update the matching scenario here immediately so the APA folder always reflects the current web app.
