# Campus Compass 🧭
**Your College. Your Community. Your Guide.**

Campus Compass is a full-stack Django web application that brings everyday student services into one verified community platform: Lost & Found, a Buy & Sell marketplace, roommate matching, an interactive campus locator, senior mentorship, announcements, notifications, private messaging and an admin reporting dashboard.

> Full Stack Development PBL project. **All people, companies, buildings, rooms and coordinates in the demo data are fictional.**

---

## ✨ Features

| Module | Highlights |
|---|---|
| **Authentication & profiles** | Registration, login with username *or* email, logout (POST), hashed passwords + Django password validators, 6-digit email OTP verification (hashed, 10-min expiry, 5-attempt lock), profile pictures, branch & year, LinkedIn URL, roles: Student / Senior / Admin |
| **Lost & Found** | Report lost/found items with image, category, location and date; live AJAX search & filters; contact owner via chat; mark recovered (AJAX); edit/delete own listings; **matching algorithm** (name 40%, category 25%, location 20%, date 15%) with automatic notifications |
| **Marketplace** | Listings with up to 3 photos, price, category, condition; live search, category / condition / price range filters, sorting; save/unsave (AJAX); enquiries (auto-opens chat + notifies seller); status updates available/reserved/sold (AJAX); report suspicious listings; seller profiles. No online payments. |
| **Find a Roommate** | Profiles with budget range, location, accommodation, food, sleep, cleanliness; live AJAX filters; **compatibility algorithm** (budget 30%, location 25%, food 15%, sleep 15%, cleanliness 15%) with per-factor breakdown; send / accept / reject requests; save profiles |
| **Campus Locator** | Leaflet.js + OpenStreetMap map; buildings, departments and rooms stored in the DB; AJAX search by room number, lab, faculty name, department, library, cafeteria; marker popups with floor, department & faculty. Demo data clearly labelled and editable |
| **Senior networking** | Senior profiles (company, designation, skills [M2M], domain, achievements, LinkedIn, GitHub, mentorship interests); search by skill, filter by domain & batch (django-filter); mentorship requests that seniors accept/reject. No LinkedIn scraping |
| **Announcements & events** | Admin CRUD, categories, event dates, venues, safe registration links, pinning, optional broadcast notification; student filtering (category, search, upcoming) |
| **Notifications** | Enquiries, roommate & mentorship requests, accept/reject, messages, lost-found matches, announcements, moderation; unread badge polled via AJAX; mark read / mark all read |
| **Messaging** | One-to-one conversations, AJAX send + 3-second polling, read receipts; only participants can access (404 otherwise) |
| **Admin dashboard** | 12 live KPIs, 6 Chart.js charts from real DB values, date-range filter, 7 CSV reports (with formula-injection protection), listing moderation, student management, building/room/department management, announcement management |

---

## 🧱 Technology stack
- **Backend:** Python 3.12, Django 5.1, Django ORM, Auth, Forms/ModelForms, JsonResponse APIs, django-filter
- **Frontend:** HTML5, CSS3, JavaScript (Fetch API), Bootstrap 5.3, Bootstrap Icons, Leaflet.js 1.9, Chart.js 4
- **Database:** SQLite (default, zero setup) or **MySQL 8** (recommended for deployment)
- **Other:** Pillow (image validation), python-dotenv, PyMySQL

Bootstrap, Bootstrap Icons, Leaflet and Chart.js are bundled in `static/vendor/`, so the UI works offline. Map **tiles** (OpenStreetMap) and the Google font need internet.

---

## 📋 Requirements
- Python **3.10 – 3.13** (3.12 recommended) — <https://www.python.org/downloads/> (tick *"Add python.exe to PATH"* on Windows)
- pip (bundled with Python)
- *(Optional)* MySQL Server 8.x

---

## 🚀 Quick start — Windows (VS Code terminal, PowerShell)

```powershell
# 1. Extract the ZIP and open the folder
Expand-Archive -Path "$HOME\Downloads\Campus_Compass.zip" -DestinationPath "$HOME\Projects" -Force
cd "$HOME\Projects\campus_compass"
code .            # optional: opens the folder in VS Code

# 2. Create and activate a virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1
#   If you get "running scripts is disabled", run once:
#   Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

# 3. Install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# 4. Environment file
copy .env.example .env

# 5. Database + demo data
python manage.py migrate
python manage.py seed_data

# 6. Run
python manage.py runserver
```
Open <http://127.0.0.1:8000/>.

### macOS / Linux
```bash
cd campus_compass
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

---

## 🔑 Demo credentials (fictional — for local testing only)

| Role | Username | Password |
|---|---|---|
| Admin (superuser) | `admin` | `Admin@12345` |
| Student | `aarav.demo` | `Demo@12345` |
| Student | `diya.demo`, `kabir.demo`, `isha.demo`, `rohan.demo`, `meera.demo`, `vivaan.demo`, `ananya.demo` | `Demo@12345` |
| Senior / mentor | `neha.senior`, `arjun.senior`, `priya.senior`, `sid.senior`, `tanvi.senior` | `Demo@12345` |
| Unverified student (to try OTP) | `newbie.demo` | `Demo@12345` |

You can log in with the username or the email (`<username>@campuscompass.demo`).
**Change or remove these accounts before any public deployment** (`python manage.py seed_data --clear`).

Good demo flows:
- Log in as `aarav.demo` → Dashboard shows a lost-wallet match, a chat with Diya, saved products.
- Log in as `diya.demo` → Roommates → 96% match with Aarav.
- Log in as `neha.senior` → Mentee requests → accept/reject.
- Log in as `admin` → avatar menu → *Admin dashboard* (charts, CSV, moderation).
- Log in as `newbie.demo` → you'll be asked for an OTP. Click **Resend code** and read the code in the `runserver` terminal.

---

## 🗄️ Database configuration

### SQLite (default)
Nothing to do — `DB_ENGINE=sqlite` creates `db.sqlite3` in the project folder.

### MySQL 8
```sql
CREATE DATABASE campus_compass CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'campus_user'@'localhost' IDENTIFIED BY 'your-strong-password';
GRANT ALL PRIVILEGES ON campus_compass.* TO 'campus_user'@'localhost';
FLUSH PRIVILEGES;
```
Then edit `.env`:
```
DB_ENGINE=mysql
DB_NAME=campus_compass
DB_USER=campus_user
DB_PASSWORD=your-strong-password
DB_HOST=127.0.0.1
DB_PORT=3306
```
and run `python manage.py migrate` and `python manage.py seed_data` again. The pure-Python **PyMySQL** driver is used (installed via requirements), so no C compiler is needed on Windows. If you prefer `mysqlclient`, `pip install mysqlclient` — it is picked up automatically.

---

## 🛠️ Common commands
| Task | Command |
|---|---|
| Apply migrations | `python manage.py migrate` |
| Create migrations after model changes | `python manage.py makemigrations` |
| Seed / reset demo data | `python manage.py seed_data` |
| Remove demo data | `python manage.py seed_data --clear` |
| Create your own superuser | `python manage.py createsuperuser` |
| Run dev server | `python manage.py runserver` |
| Run all tests | `python manage.py test` |
| Run one app's tests | `python manage.py test marketplace` |
| Django admin | <http://127.0.0.1:8000/django-admin/> |
| Custom admin dashboard | <http://127.0.0.1:8000/dashboard/admin/> |

A superuser created with `createsuperuser` can log in immediately (superusers skip OTP). To make them appear as an *Admin* role, set the role in Django admin or Admin dashboard → Students.

---

## ✉️ Email / OTP
- Development: `EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend` prints emails (and OTP codes) in the terminal running `runserver`.
- Real email (e.g. Gmail with an App Password):
```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=you@gmail.com
EMAIL_HOST_PASSWORD=your-16-char-app-password
```
- Restrict sign-ups to your college domain with `ALLOWED_EMAIL_DOMAIN=yourcollege.edu`.

## 🗺️ Campus map
Demo buildings are placed around `CAMPUS_CENTER_LAT/LNG` (default: a neutral reference point, **not** a real college). To use your campus: set your campus centre in `.env`, then edit building coordinates in *Admin dashboard → Buildings & rooms* or Django admin, and untick **Is demo**.

---

## 🧪 Tests
```powershell
python manage.py test
```
106 automated tests cover registration, OTP, login, CRUD, permissions & ownership, CSRF, XSS escaping, marketplace search/filters, lost & found matching, roommate compatibility, locator API, mentorship, notifications, messaging privacy, admin dashboard stats and CSV export. See `docs/TESTING_REPORT.md`.

---

## 📁 Project structure
```
campus_compass/
├── config/            settings, urls, wsgi/asgi
├── core/              shared validators, upload naming, landing page, seed_data command
├── accounts/          custom User, Profile, EmailOTP, auth views, decorators, middleware
├── lostfound/         Item, ItemMatch, matching.py
├── marketplace/       Product, SavedProduct, Enquiry, ProductReport
├── roommates/         RoommateProfile, RoommateRequest, compatibility.py
├── locator/           Building, Department, Room, JSON search API
├── mentorship/        Skill, SeniorProfile, MentorshipRequest, filters
├── announcements/     Announcement, filters
├── notifications/     Notification, notify() helper, JSON API
├── messaging/         Conversation, Message, polling API
├── dashboard/         student home, admin dashboard, stats, CSV reports
├── templates/         base + per-module templates
├── static/            css, js, images, vendor libraries
├── docs/              report, ER diagram, architecture, API, testing, user guide
└── tests/             shared helpers and cross-cutting security tests
```

---

## 🧯 Troubleshooting
| Problem | Fix |
|---|---|
| `python` not recognised | Reinstall Python with "Add to PATH", or use `py` instead of `python`. |
| `Activate.ps1 cannot be loaded` | `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` then retry. Or use Command Prompt: `venv\Scripts\activate.bat`. |
| `No module named django` | The venv is not active — run `.\venv\Scripts\Activate.ps1` (you should see `(venv)`). |
| `no such table` | Run `python manage.py migrate`. |
| Can't log in with demo accounts | Run `python manage.py seed_data`. |
| Stuck on "Verify your email" | Look in the `runserver` terminal for the email with the 6-digit code, or click *Resend code*. Admins can verify users in Admin dashboard → Students. |
| Map is grey | Map tiles come from OpenStreetMap and need internet. Markers and search still work. |
| Uploaded images don't show | They are served only when `DJANGO_DEBUG=True`. In production serve `media/` via your web server. |
| MySQL `Access denied` / `Unknown database` | Re-check `.env` values and that the database and user exist (see MySQL section). |
| Port 8000 in use | `python manage.py runserver 8080` |
| `DJANGO_SECRET_KEY must be set` | You set `DJANGO_DEBUG=False`; also set a long random `DJANGO_SECRET_KEY` in `.env`. |

---

## 🐙 Pushing to GitHub
1. Create an **empty** repository on GitHub (don't add a README, .gitignore or licence).
2. In the project folder:
```powershell
git init
git add .
git commit -m "Initial commit: Campus Compass"
git branch -M main
git remote add origin https://github.com/<your-username>/campus-compass.git
git push -u origin main
```
`.gitignore` keeps `venv/`, `.env`, `db.sqlite3`, uploaded media and `__pycache__/` out of the repository. Anyone who clones it follows the Quick start above.

---

## 🔐 Security notes
CSRF on every state-changing request (AJAX sends `X-CSRFToken`), `@require_POST` on mutations, ownership checks on every edit/delete/status endpoint, role-based decorators (`admin_required`, `senior_required`), participant-only conversations, Pillow-verified image uploads with size/extension limits and random filenames, `https`-only LinkedIn/GitHub validators and `http(s)`-only external links (`rel="noopener noreferrer"`), open-redirect protection on notifications, CSV formula-injection escaping, hashed OTPs, secrets via environment variables, hardened cookies/HSTS when `DEBUG=False`.

## ⚠️ Known limitations
- Messaging and notifications use AJAX **polling** (every 3 s / 20 s), not WebSockets.
- No online payments (by design).
- Demo campus coordinates are fictional placeholders.
- Production deployment (gunicorn/nginx, static/media hosting) is not configured — run `python manage.py collectstatic` and serve `staticfiles/` and `media/` through your web server.
