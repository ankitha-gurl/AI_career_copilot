# AI Career Copilot

A full-stack AI-powered career intelligence platform. Upload a resume, paste a
job description, get an AI-assisted match score, skill-gap analysis, a
personalized roadmap, interview practice, and a conversational AI Career
Copilot — all backed by a real PostgreSQL database and JWT authentication.

This build was verified end-to-end before delivery: the backend test suite
passes (7/7), the server boots and every route registers correctly, and the
frontend builds without errors.

---

## 1. Architecture

```
Browser (React)
    │  fetch/axios + JWT bearer token
    ▼
FastAPI (backend/app)
    │
    ├── api/          route handlers (auth, profile, resumes, jobs, skills,
    │                 roadmap, interview, copilot) — thin, no business logic
    ├── services/      ai_service.py (the ONLY file that calls OpenAI),
    │                 file_service.py (resume upload/parsing),
    │                 career_service.py (context retrieval for the chat agent)
    ├── models/        SQLAlchemy ORM models (one file per domain)
    ├── schemas/       Pydantic request/response schemas
    ├── security.py    password hashing (bcrypt) + JWT
    └── database.py    SQLAlchemy engine/session (PostgreSQL)
```

Every AI call goes through `app/services/ai_service.py`. No route file talks
to OpenAI directly. Every AI method asks the model for structured JSON,
parses it safely, and raises a clean `AIServiceError` on failure — routes
turn that into an HTTP 502 instead of crashing.

---

## 2. Tech stack

**Backend:** FastAPI, SQLAlchemy, PostgreSQL, Pydantic v2, JWT (python-jose),
bcrypt (direct, not passlib — see note below), pypdf + python-docx for resume
parsing, OpenAI Python SDK (current `client.chat.completions.create` API).

**Frontend:** React 18 + Vite, React Router, Axios.

### Why bcrypt directly instead of Passlib?

Your original project used Passlib + bcrypt, which is where the
`AttributeError: module 'bcrypt' has no attribute '__about__'` error came
from — Passlib's bcrypt backend has known incompatibilities with
`bcrypt>=4.1`. This build calls `bcrypt` directly (`bcrypt.hashpw` /
`bcrypt.checkpw`), which is simpler, has no such compatibility issue, and is
still the same secure algorithm. Password length is explicitly capped at 72
bytes with a clear `400` error instead of a cryptic crash.

---

## 3. Environment variables

Copy `backend/.env.example` to `backend/.env` and fill in real values:

```
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/career_copilot
JWT_SECRET_KEY=<generate with: openssl rand -hex 32>
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini
ENVIRONMENT=development
FRONTEND_ORIGIN=http://localhost:5173
MAX_UPLOAD_MB=5
```

**Never commit `.env`.** It's already in `.gitignore`.

Copy `frontend/.env.example` to `frontend/.env`:

```
VITE_API_BASE_URL=http://127.0.0.1:8000
```

---

## 4. Database setup (PostgreSQL)

You need a running PostgreSQL server and an empty database. In `psql` or
pgAdmin:

```sql
CREATE DATABASE career_copilot;
```

Then point `DATABASE_URL` in `backend/.env` at it. The app creates all
tables automatically on startup via `Base.metadata.create_all()` — this is
intentional for an MVP/portfolio project. If you later want proper schema
migrations, introduce Alembic once the app is stable (not before).

---

## 5. Backend setup (Windows PowerShell)

```powershell
cd ai-career-copilot\backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Now edit `.env` with your real `DATABASE_URL`, `JWT_SECRET_KEY`, and
`OPENAI_API_KEY`.

Run the server:

```powershell
python -m uvicorn app.main:app --reload
```

**Expected output:** `Uvicorn running on http://127.0.0.1:8000` with no
traceback.

**Success check:** open `http://127.0.0.1:8000/docs` — you should see the
"AI Career Copilot API" Swagger page listing all endpoints (auth, profile,
resumes, jobs, skills, roadmap, interview, copilot).

Run the backend test suite (uses an isolated SQLite file, never touches your
real Postgres database):

```powershell
python -m pytest -v
```

**Expected output:** `7 passed`.

---

## 6. Frontend setup (Windows PowerShell)

```powershell
cd ai-career-copilot\frontend
npm install
copy .env.example .env
npm run dev
```

**Expected output:** `Local: http://localhost:5173/`

Open that URL, register a new account, log in, and you'll land on the
dashboard.

---

## 7. Feature walkthrough

1. **Register / Login** — `/register`, `/login`. JWT stored in
   `localStorage`, sent as `Authorization: Bearer <token>` on every request.
2. **Profile** (`/profile`) — education, experience, preferred roles/tech,
   career goals.
3. **Resume** (`/resume`) — upload PDF/DOCX/TXT, then "Analyze with AI" to
   get structured skills/education/experience extraction. Analysis is
   cached — re-visiting doesn't re-call the AI.
4. **Jobs** (`/jobs`) — paste a job description, get an AI breakdown
   (required skills, seniority, responsibilities, etc.), then calculate a
   match score against your latest analyzed resume (`/jobs/:id/match`).
5. **Skills** (`/skills`) — track your skills manually, run an AI skill-gap
   analysis against any saved job.
6. **Roadmap** (`/roadmap`) — generate a phased learning roadmap for a
   target role, optionally informed by a specific job's skill gap.
7. **Interview** (`/interview`) — generate mixed technical/behavioral/coding
   questions for a target role, answer them, get AI-scored feedback.
8. **Copilot** (`/copilot`) — free-form chat that has access to your saved
   profile, latest resume analysis, skills, and latest job match — not your
   whole database.

---

## 8. API reference (auto-generated)

Full interactive docs live at `http://127.0.0.1:8000/docs` while the server
is running. Key routers:

```
POST   /auth/register
POST   /auth/login
GET    /auth/me

GET    /profile/me
PUT    /profile/me

POST   /resumes                       (multipart file upload)
GET    /resumes
POST   /resumes/{id}/analyze
GET    /resumes/{id}/analysis

POST   /jobs
GET    /jobs
GET    /jobs/{id}
POST   /jobs/{id}/match
GET    /jobs/{id}/matches

GET    /skills/me
POST   /skills/me/{skill_name}
POST   /skills/gap-analysis

POST   /roadmap
GET    /roadmap
GET    /roadmap/{id}

POST   /interview/questions
GET    /interview/sessions
POST   /interview/evaluate

POST   /copilot/chat
GET    /copilot/conversations
GET    /copilot/conversations/{id}
```

---

## 9. Security notes

- `JWT_SECRET_KEY`, `DATABASE_URL`, and `OPENAI_API_KEY` are only ever read
  from environment variables (`app/config.py`) — nothing is hardcoded.
- `password_hash` is never included in any API response (`UserOut` schema
  excludes it entirely).
- All career-data endpoints derive `user_id` from the JWT via
  `get_current_user`, never from a value the frontend sends.
- Uploaded resumes are validated for extension and size
  (`MAX_UPLOAD_MB`) before being written to disk.
- A global exception handler in `main.py` returns a generic `500` message —
  it never leaks stack traces, DB errors, or secrets to the client.
- The OpenAI API key is used only server-side inside `ai_service.py` and is
  never sent to the frontend.

---

## 10. Known limitations / next steps

This is a complete, working MVP — not yet "hardened for scale." If you want
to keep going toward a more production-grade deployment:

- Add Alembic migrations instead of `create_all()`.
- Add rate limiting on `/auth/login` and the AI-calling endpoints.
- Add refresh tokens (current JWTs are long-lived access tokens only).
- Move resume file storage to S3/Blob storage instead of local disk before
  deploying anywhere without persistent disk (e.g. most serverless hosts).
- Add OpenAI function/tool calling in `career_chat` if you want the Copilot
  to actively query the database mid-conversation instead of relying on the
  pre-fetched context in `career_service.py`.
- Add structured logging/monitoring for AI call failures and costs.

---

## 11. Troubleshooting your original PostgreSQL error

Your blocker was:

```
FATAL: could not load C:/Program Files/PostgreSQL/18/data/pg_hba.conf
```

This is a Windows PostgreSQL **service** problem, unrelated to this code —
it means the Postgres server process itself can't find/read its config, so
nothing this app does will fix it. Diagnose it with:

```powershell
Get-Service *postgres*
Get-CimInstance Win32_Service | Where-Object {$_.Name -like "*postgres*"} | Select-Object Name, State, PathName
Test-Path "C:\Program Files\PostgreSQL\18\data\pg_hba.conf"
Test-NetConnection localhost -Port 5432
```

Once PostgreSQL is confirmed running and reachable on port 5432, this
backend will connect to it with no code changes needed — `DATABASE_URL` in
`.env` is the only thing that has to match your real Postgres credentials.
#   A I _ c a r e e r _ c o p i l o t  
 