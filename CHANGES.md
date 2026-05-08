# KidWall – Change Log

## Session: May 4, 2026

---

### 1. Backend Server – `main.py`

- Added `uvicorn.run("main:app", host="0.0.0.0", port=8010, reload=True)` so the server starts when running `python main.py`
- Moved `_ensure_requirements()` inside `if __name__ == "__main__"` to prevent crash on uvicorn hot-reload worker spawn
- Changed port from `8000` → `8010` to avoid conflict with Docker container also listening on 8000
- Added routes: `GET /` (service info), `GET /health`, `GET /favicon.ico` (204)

---

### 2. Database Models – `models.py`

- Fixed import order: all imports moved to top of file (was causing `NameError: 'Base' not defined`)
- Renamed `relationship` column in `EmergencyContact` → `relation` (was shadowing SQLAlchemy's `relationship()` function)
- Added `get_db()` session generator
- Added aliases at bottom: `UserType = UserRole`, `Parent = User`, `Merchant = User`
- Added two new columns to `User` model:
  - `temp_password_hash = Column(String, nullable=True)`
  - `temp_password_expires = Column(DateTime, nullable=True)`

---

### 3. Database Migration – Alembic

**`alembic/versions/fab364c0fc47_add_temp_password_fields_to_users.py`** *(new)*

- Adds `temp_password_hash` (String, nullable) to `users` table
- Adds `temp_password_expires` (DateTime, nullable) to `users` table
- Applied with: `.venv\Scripts\alembic upgrade head`

**`alembic/env.py`** *(rewritten)*

- Loads `.env` via `python-dotenv`
- Builds `sqlalchemy.url` from env vars (`POSTGRES_USER`, `POSTGRES_PASSWORD`, etc.) — overrides `alembic.ini`
- Automatically remaps `POSTGRES_HOST=db` (Docker service name) → `localhost` when running from host machine
- Default port set to `5433` (matches `docker-compose.yml` host-mapped port `5433:5432`)
- Default password set to `Palo1010`

**`alembic.ini`**

- `sqlalchemy.url` set to `postgresql+psycopg2://colepago:Palo1010@localhost:5433/colepago` (fallback; `env.py` overrides at runtime)

---

### 4. Password Reset Flow – Backend

**`colepago/api/router.py`**

- Added import: `from email_utils import send_temp_password_email`
- Added helper: `_generate_temp_password(length=10)` — cryptographically random alphanumeric string
- Added Pydantic models: `ForgotPasswordRequest`, `ResetPasswordRequest`
- Added endpoint `POST /api/auth/forgot-password`:
  - Generates 10-char temp password, bcrypt-hashes it, sets 2-hour expiry on user record
  - Sends email via SMTP
  - Rolls back temp password if email send fails
  - Always returns the same message (prevents email enumeration)
- Added endpoint `POST /api/auth/reset-password`:
  - Validates temp password against hash
  - Checks expiry (rejects and clears if expired)
  - Enforces minimum 8-character new password
  - Sets new `password_hash`, clears temp password fields

---

### 5. Email Utility

**`email_utils.py`** *(new — in `d:\kidwall\`)*  
**`colepago/email_utils.py`** *(new — copy for colepago package import resolution)*

- `send_temp_password_email(to_email, name, temp_password)` — sends HTML password-reset email
- SMTP config from env vars: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM`, `SMTP_USE_TLS`
- Uses STARTTLS on port 587

---

### 6. Environment Variables – `.env`

SMTP_HOST=mailout.easymail.ca
SMTP_PORT=587
SMTP_USER=drcarloni
SMTP_PASS=Lapiedra2314SMTP_FROM=<admin@drsrv.net.ar>
SMTP_USE_TLS=true

- SMTP credentials are configured via local `.env` (do not commit real values)

---

### 7. Flutter – API Service – `lib/api_service.dart`

- Added `APP_ENV` dart-define support: `local` / `staging` / `prod`
- URL routing:
  - `local` (default) → `http://192.168.1.8:8010/api` (LAN IP for mobile devices)
  - `staging` / `prod` → `https://drsrv.drsrv.net.ar:8000`
- Added method `forgotPassword(String email)`
- Added method `resetPassword({email, tempPassword, newPassword})`

---

### 8. Flutter – Password Reset Screens

**`lib/screens/forgot_password_screen.dart`** *(new)*

- Email input form
- Calls `ApiService.forgotPassword()`
- Shows confirmation message with link to `ResetPasswordScreen`

**`lib/screens/reset_password_screen.dart`** *(new)*

- Fields: temp password + new password + confirm password
- Validates: min 8 chars, passwords must match
- Calls `ApiService.resetPassword()`

**`lib/screens/login_screen.dart`**

- Added import for `forgot_password_screen.dart`
- Added "Forgot password?" `TextButton` that navigates to `ForgotPasswordScreen`

---

### 9. Pylance / VS Code – `colepago/.vscode/settings.json`

- Added `"python.analysis.extraPaths": ["d:/kidwall"]` so Pylance resolves `models`, `email_utils` imports that are loaded from the parent `d:\kidwall` directory at runtime

---

### 10. Deployment Script – `deploy_all.ps1`

Added steps to manage the local backend:

1. `docker-compose up -d db` — starts the Postgres container
2. Waits until `pg_isready` confirms Postgres is accepting connections
3. `.venv\Scripts\alembic upgrade head` — applies any pending migrations
4. Kills existing `python main.py` process (if any) and starts a fresh backend on port 8010

---

### How to run locally

```powershell
cd D:\kidwall
.venv\Scripts\Activate.ps1

# Start DB
docker-compose up -d db

# Run migrations
.venv\Scripts\alembic upgrade head

# Start backend
.venv\Scripts\python main.py
# → http://127.0.0.1:8010  /  http://192.168.1.8:8010
```

Or run everything at once:

```powershell
powershell deploy_all.ps1
```
