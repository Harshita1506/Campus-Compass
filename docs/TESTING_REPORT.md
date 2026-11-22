# Testing Report

**Command:** `python manage.py test`
**Result (at packaging time):** `Ran 106 tests … OK` — 0 failures, 0 errors (Python 3.13, Django 5.1, SQLite test database).

In addition to the automated suite, every page and JSON endpoint was smoke-tested with the seeded demo data as an anonymous user, a student, a senior and an admin, and the key AJAX flows (live search, save toggle, roommate filters, locator search & map focus, chat send/poll, notifications dropdown, admin charts) were exercised in headless Chrome with no JavaScript errors.

## Coverage by area
| Area | Test file | What is verified |
|---|---|---|
| Registration | `accounts/tests.py` | account + profile created, password stored hashed, OTP email sent, weak password rejected, duplicate email rejected, cannot self-register as admin |
| OTP verification | `accounts/tests.py` | unverified users redirected, correct code verifies, lock after 5 wrong attempts, OTP stored hashed |
| Login / logout | `accounts/tests.py` | login by username and by email, wrong password, POST logout |
| Profile | `accounts/tests.py` | edit profile, LinkedIn URL domain validation |
| Validators / landing | `core/tests.py` | LinkedIn/GitHub/safe-URL validators, image extension check, landing page |
| Lost & Found CRUD | `lostfound/tests.py` | create, future-date rejection, owner-only edit/delete, AJAX mark recovered (403 for others), search API |
| Matching algorithm | `lostfound/tests.py` | similar items ≥ 70%, unrelated < 40%, matches stored once, both owners notified, own items never matched |
| Marketplace CRUD | `marketplace/tests.py` | create with real image (random filename), fake image rejected, negative price rejected, owner edit, non-owner blocked (403), mark sold |
| Marketplace search | `marketplace/tests.py` | text search, category filter, price range + sort, sold excluded by default, hidden excluded |
| Marketplace interactions | `marketplace/tests.py` | save/unsave toggle, POST-only, enquiry → notification + conversation, one report per user, hidden listing 403, seller page |
| Roommate algorithm | `roommates/tests.py` | weights 30/25/15/15/15, identical = 100, opposite < 15, single-factor miss = 85, symmetry |
| Roommate flow | `roommates/tests.py` | budget validation, filter API with compatibility, request → no duplicates → receiver-only accept → notifications, AJAX reject, save toggle |
| Campus locator API | `locator/tests.py` | login required, buildings JSON, search by room number / faculty / department, type filter, unique room per building, floor labels |
| Mentorship | `mentorship/tests.py` | filters (skill/domain/batch), request → accept with note → notifications, reject, no duplicate pending, unavailable seniors, senior-only pages, skills M2M save, unsafe LinkedIn rejected |
| Announcements | `announcements/tests.py` | admin create/edit/pin/delete + broadcast notifications, students blocked from management, unsafe registration link rejected, category/upcoming filters, drafts hidden |
| Notifications | `notifications/tests.py` | no self-notifications, unread count API, mark read / all read, cannot touch others' notifications, safe redirect on open |
| Messaging | `messaging/tests.py` | one conversation per pair, start view, read receipts, AJAX send + poll, empty rejected, notification de-duplication, CSRF enforced |
| Messaging privacy | `messaging/tests.py` | non-participant cannot view, poll, send, or see in inbox (404) |
| Admin dashboard | `dashboard/tests.py` | admin-only (403 for students), stats equal real DB counts, date range filter, page renders, moderation hide, student management, building management |
| CSV reporting | `dashboard/tests.py` | all 7 reports download as CSV, contents, formula-injection neutralised, unknown report 404 |
| Cross-cutting security | `tests/test_security.py` | login required on all modules, CSRF on AJAX, users cannot modify others' listings, GET blocked on mutations, XSS escaped |

## Manual test checklist (for viva / demo)
1. Register a new account → read OTP in terminal → verify.
2. Report a lost item similar to an existing found item → see the match + notification.
3. Marketplace: type in search, change price range, sort; save an item; send enquiry → chat opens.
4. Roommates: create profile → see compatibility rings → send request; log in as receiver → accept.
5. Locator: search "A310", "AI", "Kavita"; click a result → map flies to marker.
6. Seniors: filter by skill "Python" → send request → log in as `neha.senior` → accept.
7. Open chat in two browsers (normal + incognito) → messages appear within 3 seconds.
8. Admin: apply date range, export CSV, hide a reported listing, suspend a user, edit a building.

## Known limitations found during testing
- Real-time features use polling, so there is a delay of up to 3 s (chat) / 20 s (notification badge).
- Map tiles require internet access; offline, the markers and search still work on a blank background.
