# JSON API Documentation

All endpoints are internal Django views returning `JsonResponse`. They require an authenticated, email-verified session (unauthenticated requests are redirected to `/accounts/login/`). State-changing endpoints are **POST-only** (`405` otherwise) and require the CSRF token in the `X-CSRFToken` header (or `csrfmiddlewaretoken` form field). The front-end helper `CC.post()` in `static/js/main.js` adds it automatically.

Common error codes: `400` invalid input · `403` not the owner / missing role / CSRF failure · `404` not found or not a participant · `405` wrong method.

---

## Lost & Found
### `GET /lost-found/api/search/`
Query: `q`, `item_type` (`lost|found`), `category`, `status` (`open|recovered`).
```json
{"count": 1, "results": [{"id": 3, "title": "Black wallet", "type": "found", "category": "Bags & Wallets",
  "location": "Central Library", "date": "2026-11-20", "status": "open"}], "html": "<div class=…>"}
```
### `POST /lost-found/api/<id>/status/` *(owner or admin)*
Body: `status=recovered|open` → `{"ok": true, "status": "recovered", "label": "Recovered"}`

## Marketplace
### `GET /marketplace/api/search/`
Query: `q`, `category`, `condition`, `min_price`, `max_price`, `sort` (`newest|oldest|price_asc|price_desc`), `include_sold` (`on`). Hidden (moderated) listings are never returned.
```json
{"count": 2, "results": [{"id": 2, "title": "Casio fx-991ES", "price": "700.00", "category": "Electronics",
  "condition": "Like new", "status": "available", "saved": false, "url": "/marketplace/2/"}], "html": "…"}
```
### `POST /marketplace/api/<id>/save/` → `{"ok": true, "saved": true, "count": 3}` (toggle)
### `POST /marketplace/api/<id>/status/` *(seller or admin)*
Body: `status=available|reserved|sold` → `{"ok": true, "status": "sold", "label": "Sold"}`

## Roommates
### `GET /roommates/api/filter/`
Query: `q`, `location`, `accommodation`, `food`, `sleep`, `max_budget`, `sort` (`match|newest|budget`). The viewer's own profile is excluded.
```json
{"count": 6, "results": [{"id": 16, "name": "Diya Kapoor", "headline": "…", "compatibility": 96,
  "matching": ["Budget", "Location", "Food", "Sleep schedule", "Cleanliness"]}], "html": "…"}
```
`compatibility` is `null` when the viewer has no roommate profile.
### `POST /roommates/api/<id>/save/` → `{"ok": true, "saved": true}`
### `POST /roommates/requests/<id>/<accept|reject>/` *(receiver only; send `X-Requested-With: XMLHttpRequest` for JSON)*
→ `{"ok": true, "status": "accepted", "label": "Accepted"}`

## Campus Locator
### `GET /locator/api/buildings/`
```json
{"buildings": [{"id": 1, "name": "Aryabhata Academic Block (Demo)", "code": "A-BLK", "type": "academic",
  "type_label": "Academic block", "lat": 20.5945, "lng": 78.9617, "floors": 5, "description": "…",
  "hours": "8:00 AM – 6:00 PM", "is_demo": true, "departments": ["Computer Science & Engineering (Demo)"]}]}
```
### `GET /locator/api/search/?q=<text>&type=<room or building type>`
Searches room number, room name, faculty name, department, building name/code. Room types: `classroom, lab, cabin, office, seminar, library, cafeteria, other`; building types: `academic, lab, library, cafeteria, admin, hostel, sports, auditorium, other`.
```json
{"query": "kavita", "buildings": [], "rooms": [{"id": 5, "room_number": "A310", "name": "Faculty Cabin",
  "type": "cabin", "type_label": "Faculty cabin", "floor": 3, "floor_label": "3rd floor",
  "department": "Computer Science & Engineering (Demo)", "faculty": "Dr. Kavita Rao (fictional)", "capacity": null,
  "description": "", "building": {"id": 1, "name": "…", "code": "A-BLK", "lat": 20.5945, "lng": 78.9617}}]}
```

## Notifications
| Method & path | Response |
|---|---|
| `GET /notifications/api/unread/` | `{"unread": 2, "latest": [{"id", "title", "message", "icon", "is_read", "time", "url"}]}` |
| `POST /notifications/api/<id>/read/` | `{"ok": true, "unread": 1}` (404 if not the recipient) |
| `POST /notifications/api/read-all/` | `{"ok": true, "unread": 0}` |

## Messaging
| Method & path | Notes |
|---|---|
| `GET /messages/api/<conversation_id>/messages/?after=<message_id>` | New messages after an id; marks received ones read. `{"messages": [{"id", "body", "sender", "mine", "time"}]}` |
| `POST /messages/api/<conversation_id>/send/` | JSON body `{"body": "Hello"}` (max 2000 chars). `{"ok": true, "message": {…}}`; `400` if empty |
| `GET /messages/api/unread/` | `{"unread": 3}` |

Non-participants always receive **404** (existence is not revealed).

## Admin (staff / admin role only)
| Method & path | Notes |
|---|---|
| `GET /dashboard/admin/api/stats/?start=YYYY-MM-DD&end=YYYY-MM-DD` | `{"summary": {12 KPIs}, "charts": {"lostfound", "products_by_category", "available_vs_sold", "registrations", "mentorship_status", "accommodation"}}` — each chart is `{"labels": [...], "data": [...]}` |
| `GET /dashboard/admin/export/<report>/?start=&end=` | CSV download. `report` ∈ `summary, students, products, lostfound, roommates, mentorship, reports` |

## Example (JavaScript)
```js
const data = await CC.getJSON('/marketplace/api/search/?q=book&sort=price_asc');
await CC.post('/marketplace/api/12/save/');                 // form-encoded + CSRF header
await CC.post('/messages/api/4/send/', {body: 'Hi!'}, true); // JSON + CSRF header
```
