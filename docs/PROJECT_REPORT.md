# Campus Compass — Project Report
*Full Stack Development PBL*

## 1. Abstract
Campus Compass is a unified digital ecosystem for college students. It replaces scattered WhatsApp groups, notice boards and word-of-mouth with one verified platform offering Lost & Found, a peer-to-peer marketplace, roommate matching, an interactive campus locator, senior mentorship, official announcements, notifications and private messaging, plus an administrative dashboard with analytics and reporting. It is built with Django 5, Bootstrap 5, vanilla JavaScript (Fetch API), Leaflet/OpenStreetMap and Chart.js, backed by SQLite in development and MySQL 8 in deployment.

## 2. Problem statement
Students regularly lose belongings, look for affordable second-hand items, search for compatible roommates, get lost finding classrooms or faculty cabins, and struggle to reach seniors for guidance. Information is fragmented, unverified and hard to search, and administrators have no visibility into these activities.

## 3. Objectives
1. Provide verified, role-based access for students, seniors and administrators.
2. Implement nine functional modules backed by a relational database.
3. Use asynchronous (AJAX) interactions for search, filters, saving, status changes, notifications and chat.
4. Add algorithmic assistance: lost-found matching and roommate compatibility.
5. Give administrators real-time analytics, moderation tools and CSV reports.
6. Follow web-security best practices (CSRF, hashing, validation, authorization).

## 4. Scope
In scope: everything listed in the README feature table. Out of scope: online payments, native mobile apps, WebSocket real-time push, scraping third-party sites.

## 5. Technology choices
| Need | Choice | Reason |
|---|---|---|
| Backend framework | Django 5 | batteries-included auth, ORM, forms, admin, security middleware |
| Database | SQLite → MySQL 8 | zero-setup development; production-grade relational DB |
| UI | Bootstrap 5 + custom CSS design system | responsive, accessible components; consistent navy/indigo theme |
| Async | Fetch API + `JsonResponse` | no extra framework, works with CSRF |
| Maps | Leaflet + OpenStreetMap | open-source, no API key |
| Charts | Chart.js | lightweight, responsive charts |
| Filtering | django-filter | declarative filters for mentorship and announcements |
| Images | Pillow | verifies uploaded images are real images |

## 6. System design
See `SYSTEM_ARCHITECTURE.md` (layers, request flows, security) and `ER_DIAGRAM.md` (21 entities across 10 apps).

### 6.1 Modules (Django apps)
`accounts`, `lostfound`, `marketplace`, `roommates`, `locator`, `mentorship`, `announcements`, `notifications`, `messaging`, `dashboard`, plus `core` for shared utilities.

### 6.2 Algorithms
**Lost & Found matching** (`lostfound/matching.py`)
```
score = 40·name_similarity + 25·same_category + 20·location_similarity + 15·date_proximity
name/location similarity = max(SequenceMatcher ratio, token Jaccard) with stop-words removed
date_proximity = 1 if ≤1 day apart, linearly decreasing to 0 at 15 days
threshold = 55% ; only open items of the opposite type and a different owner are compared
```
**Roommate compatibility** (`roommates/compatibility.py`)
```
score = 30·budget + 25·location + 15·food + 15·sleep + 15·cleanliness
budget: overlap of ranges relative to the narrower range (partial credit for near misses)
location: exact 1.0, "anywhere" 0.7 ; food: exact 1.0, "no preference" 0.8, veg/vegan 0.7 …
sleep: exact 1.0, "flexible" 0.6 ; cleanliness: same level 1.0, one level apart 0.5
"matching preferences" = factors scoring ≥ 0.7
```

### 6.3 Security measures
Password hashing (PBKDF2) and validators; hashed, expiring, attempt-limited OTP; CSRF on every POST/AJAX request; `require_POST` on mutations; ownership checks on all edit/delete/status operations; role decorators; participant-only conversations returning 404; Pillow image verification, size/extension limits, random upload names; domain-restricted LinkedIn/GitHub URLs and http(s)-only external links with `rel="noopener noreferrer"`; open-redirect protection; CSV formula-injection escaping; auto-escaped templates; secrets via environment variables; secure cookies/HSTS when not in debug.

## 7. Implementation highlights
- Custom `User` model (role, unique email, verification flag) + `Profile` created by a signal.
- `EmailVerificationMiddleware` gates the app until the OTP is verified.
- Reusable `CC` JavaScript helper: CSRF-aware `post()`, `getJSON()`, live-filter binding, delegated save/status buttons, notification polling.
- Server-rendered card partials are returned inside JSON (`html` key) so AJAX results look identical to the first page load and remain auto-escaped.
- Admin statistics are computed by ORM aggregation (`Count`, `TruncDate`) and shared by the dashboard page, chart API and CSV export.
- `seed_data` command builds a complete, fictional demo campus idempotently.

## 8. Testing
106 automated tests (see `TESTING_REPORT.md`), all passing, plus a page/API smoke test and headless-browser checks of the AJAX features.

## 9. Results
All nine required modules are functional and connected to the database; no static charts or placeholder buttons. The UI is responsive from mobile to desktop.

## 10. Limitations & future work
- Replace polling with Django Channels (WebSockets) for instant chat and notifications.
- Indoor floor plans for the locator; real campus coordinates entered by administrators.
- Image compression/thumbnails and object storage for media.
- Email digests, push notifications and a progressive web app.
- Recommendation engine for marketplace items.

## 11. Conclusion
Campus Compass demonstrates a complete full-stack workflow — data modelling, server-side validation, role-based security, asynchronous UX, mapping, analytics and automated testing — applied to real problems students face every day.
