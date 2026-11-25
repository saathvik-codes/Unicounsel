# UniCounsel

Study-abroad planner: find universities worldwide, compare what a country costs to live in, and work through
scholarships, visa paperwork and interview practice.

One repo, one backend:

| Folder | What it is | Run locally |
|---|---|---|
| `backend/` | Flask app. The only backend: accounts, database, the dashboard pages and the JSON API | `cd backend && pip install -r requirements.txt && python app.py` |
| `frontend/` | React + TypeScript landing site. Reads its numbers from the backend and sends sign-in, sign-up and the dashboard to it | `cd frontend && npm install && npm run dev` |

Set `VITE_APP_URL` in `frontend` to the backend's address (default is the deployed app; locally use `http://localhost:5000`).

## Data (all live, no keys)
- Universities and countries: OpenAlex
- Cost of living by country (US = 100): World Bank
- Currency conversion: open.er-api.com

`backend/adapters/` holds the sources and a stale-while-revalidate cache, so pages never wait on an outside API.
`backend/data/live_snapshot.json` is the fallback snapshot, refreshed daily by `.github/workflows/refresh-data.yml` (or run `python backend/scripts/refresh_snapshot.py`).

## Backend endpoints (public)
`/api/universities?country=CA&q=toronto&page=1`, `/api/countries`, `/api/cost-index?country=IN`,
`/api/convert?amount=100&from=USD&to=INR`, `/api/site-counts`

## Deploying
Two Vercel projects from this one repo: root directory `frontend` for the site, `backend` for the Flask app.

## Database
TiDB Cloud (MySQL-compatible, Starter plan, free, spending limit 0). The backend uses it whenever `TIDB_HOST`, `TIDB_USER`,
`TIDB_PASSWORD` (or a single `DATABASE_URL=mysql://...`) are set; see `backend/.env.example`. Without them it falls back to a
local SQLite file, which is handy for quick local runs. The SQL stays SQLite-style in the code; `backend/db_config.py`
translates it for TiDB and creates all tables on first start.
