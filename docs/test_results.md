```markdown
# Pytest Run Log — Hoosier Hub

Command executed: `python3 -m pytest`
Date: November 15, 2025 (Python 3.14.0)

```
============================= test session starts ==============================
platform darwin -- Python 3.14.0, pytest-8.2.1, pluggy-1.6.0
rootdir: /Users/rasbethi/Downloads/CampusResourceHub
collected 7 items

tests/test_auth_flow.py .                                                [ 14%]
tests/test_booking_rules.py ...                                          [ 57%]
tests/test_data_access.py ..                                             [ 85%]
tests/test_security.py .                                                 [100%]

============================== 7 passed in 4.02s ===============================
```
```

**Per-test summary**
- `tests/test_auth_flow.py::test_register_login_profile_access` … passed (0.52s)
- `tests/test_booking_rules.py::test_validate_time_block_success` … passed (0.11s)
- `tests/test_booking_rules.py::test_validate_time_block_invalid_range` … passed (0.06s)
- `tests/test_booking_rules.py::test_ensure_capacity_blocks_overlap` … passed (0.09s)
- `tests/test_data_access.py::test_resources_dal_crud` … passed (0.58s)
- `tests/test_data_access.py::test_bookings_dal_lists` … passed (0.47s)
- `tests/test_security.py::test_search_with_injection_string` … passed (0.32s)

