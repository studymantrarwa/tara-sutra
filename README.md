# Tara Sutra Astrology

Full-stack Vedic astrology project foundation.

## Stack
- Next.js + React + TypeScript + Tailwind-ready CSS
- Supabase Auth/Postgres/RLS/Realtime
- Python FastAPI + Swiss Ephemeris
- Sidereal/Lahiri calculations

## Important
This ZIP is a working project foundation, not a claim that every advanced astrology rule, payment flow, or production moderation workflow is already complete. The UI, database foundation, place-search flow, and astrology-engine foundation are included so development can continue safely feature-by-feature.

## Run web
npm install
npm run dev

## Astrology engine
cd astro-engine
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/Android terminal: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

Copy .env.example to .env.local and set:
NEXT_PUBLIC_SUPABASE_URL
NEXT_PUBLIC_SUPABASE_ANON_KEY
ASTRO_ENGINE_URL=http://127.0.0.1:8000

Never put a Supabase service-role key in browser code.
