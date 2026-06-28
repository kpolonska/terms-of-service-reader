# ToS Reader — Browser Extension

A Chrome extension that analyzes Terms of Service documents and explains what you're agreeing to in plain English. Built as a research project exploring surveillance capitalism, datafication, and platformization through the lens of real corporate legal documents.

**Website:** [kpolonska.github.io/terms-of-service-reader](https://kpolonska.github.io/terms-of-service-reader) · **Repo:** [github.com/kpolonska/terms-of-service-reader](https://github.com/kpolonska/terms-of-service-reader)

---

## User journey

The intended flow for a new user:

```
1. Open the website
      ↓
2. Try the live demo — paste any ToS text, get instant analysis
   (no install needed, runs in the browser against localhost:8000)
      ↓
3. Want this on every website you visit?
   → Download the extension ZIP → load in Chrome (3 steps, ~60 seconds)
   → Start the local backend (double-click start.command / start.bat)
      ↓
4. Use the extension everywhere
   → Visit any /terms, /privacy, /legal page
   → Extension auto-detects and analyzes
   → Click the toolbar icon to see risk score, flagged clauses, TLDR
   → Pick a profile (General / Journalist / Activist / Business)
     before clicking Analyze for profile-tailored results
   → Subscribe to get notified when a site changes its ToS
```

### Starting the backend (no terminal needed)

The backend runs locally via Docker. Download the project ZIP and use the included launchers:

| OS | Launcher | What it does |
|----|----------|--------------|
| Mac | `start.command` (double-click) | Checks `.env`, checks Docker, runs `docker compose up --build -d`, opens website |
| Windows | `start.bat` (double-click) | Same flow with PowerShell dialogs |

Prerequisites: [Docker Desktop](https://www.docker.com/products/docker-desktop/) (free) + an [LLMAPI key](https://llmapi.ai) (free tier).

Setup once:
```bash
cp .env.example .env
# open .env, replace your_llmapi_key_here with your real key
```

Then double-click the launcher — it handles everything else.

---

## How it works

```
User on a ToS page
       │
       ▼
Chrome Extension (Person A)
  - Detects ToS pages
  - Extracts text from DOM
  - Sends to backend
       │
       ▼
Backend API (Person B)
  - Receives text
  - Checks cache
  - Calls AI pipeline
       │
       ▼
AI Pipeline (Person C)
  - Builds prompt
  - Calls Claude API
  - Parses + validates response
  - Stores result in cache
       │
       ▼
Extension popup displays:
  - TLDR summary
  - Flagged clauses with severity and plain-English explanation
```

---

## Project structure

```
terms-of-service-reader/
├── website/            ← Landing page + web analysis tool (static HTML)
├── extension/          ← Chrome extension (Person A)
├── backend/            ← FastAPI server (Person B)
├── ai_pipeline/        ← Claude integration + cache (Person C)
├── .env.example        ← environment variable template
└── .gitignore
```

---

## Quick start

### Option A — one-click (recommended for end users)

1. Download the project ZIP from [github.com/kpolonska/terms-of-service-reader](https://github.com/kpolonska/terms-of-service-reader/archive/refs/heads/main.zip) and unzip it
2. Copy `.env.example` → `.env` and add your `LLMAPI_KEY`
3. **Mac:** double-click `start.command` · **Windows:** double-click `start.bat`
4. The launcher checks Docker, starts the backend, and opens the website automatically

Prerequisites: [Docker Desktop](https://www.docker.com/products/docker-desktop/) + [LLMAPI key](https://llmapi.ai).

### Option B — manual (for developers)

**Step 1 — create `.env`:**

```bash
cp .env.example .env
# fill in LLMAPI_KEY and LLMAPI_BASE_URL
```

**Step 2 — start the backend** (from `backend/` directory):

```bash
cd backend
source venv/bin/activate      # Windows: venv\Scripts\activate
uvicorn main:app --reload
# → http://localhost:8000
```

Verify it works:
```bash
curl http://localhost:8000/health
```

**Step 3 — open the website:**

```bash
open website/index.html
# or: cd website && python3 -m http.server 3000
```

**Step 4 — load the extension in Chrome:**

1. Go to `chrome://extensions`
2. Enable **Developer mode** (top-right toggle)
3. Click **Load unpacked** → select the `extension/` folder

### API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/analyze` | Analyze ToS text |
| `POST` | `/explain` | Deep-explain a clause |
| `GET` | `/report/{domain}` | Download PDF report |
| `GET` | `/stats` | Aggregated statistics |
| `POST` | `/subscribe` | Subscribe to ToS change alerts |
| `DELETE` | `/subscribe/{domain}` | Unsubscribe |
| `GET` | `/subscriptions` | List subscribed domains |
| `GET` | `/health` | Health check |

Interactive API docs: `http://localhost:8000/docs`

---

## Shared setup (everyone does this first)

### 1. Clone the repo

```bash
git clone <repo-url>
cd terms-of-service-reader
```

### 2. Create your .env file

Copy the template and fill in the values:

```bash
cp .env.example .env
```

Open `.env` and set:

```
ANTHROPIC_API_KEY=your_key_here
```

Get an API key at [console.anthropic.com](https://console.anthropic.com). **Never commit `.env` to git** — it is already in `.gitignore`.

### 3. Git workflow

Each person works on their own branch:

| Person | Branch name |
|--------|-------------|
| A | `feature/extension` |
| B | `feature/backend` |
| C | `feature/ai-pipeline` |

```bash
git checkout -b feature/your-branch-name
```

Merge into `main` via pull request. Never push directly to `main`.

---

## Shared API contract

This is the single most important thing all three people must agree on. **Do not change this shape without telling everyone.**

### Request — Extension → Backend

```
POST http://localhost:8000/analyze
Content-Type: application/json

{
  "text": "<extracted ToS text, max 20 000 chars>",
  "domain": "google.com"
}
```

### Response — Backend → Extension

```json
{
  "tldr": "This service collects extensive personal data and shares it with third parties for advertising.",
  "clauses": [
    {
      "quote": "We may share your information with our affiliates and partners.",
      "plain_english": "The company can give your personal data to other businesses.",
      "category": "data_sharing_third_parties",
      "severity": "high",
      "concept": "Surveillance Capitalism (Zuboff)"
    }
  ],
  "cached": false,
  "analyzed_at": "2026-06-27T10:00:00+00:00"
}
```

### Valid values

**category** — one of:
`data_collection`, `data_sharing_third_parties`, `behavioral_analysis`, `algorithmic_decision`, `rights_modification`, `content_ownership`, `account_termination`, `legal_jurisdiction`

**severity** — one of:
`low`, `medium`, `high`

**concept** — one of:
`Surveillance Capitalism (Zuboff)`, `Datafication (Van Dijck)`, `Platformization (Srnicek)`, `Algorithmic Opacity (Pasquale)`, `General Power Asymmetry`

**risk** — object:
```json
{"score": 8, "label": "DANGEROUS"}
```
`score` is 1–10 (higher = more dangerous). `label` is one of `SAFE`, `CAUTION`, `RISKY`, `DANGEROUS`.

**alternatives** — array of privacy-respecting alternatives, returned only when `risk.score >= 7`:
```json
[{"name": "Signal", "url": "signal.org", "reason": "End-to-end encrypted, no metadata collection."}]
```
Alternatives are **AI-generated dynamically** by Claude based on the domain and the specific privacy risks found in the ToS analysis. Results are cached in SQLite so each domain is only analyzed once — subsequent requests return the cached alternatives instantly at no extra cost.

---

---

## Person A — Chrome Extension

**Files:** `extension/`
**Language:** JavaScript, HTML, CSS

### What you own

| File | Purpose |
|------|---------|
| `manifest.json` | Extension config — permissions, entry points |
| `content/content.js` | Runs on every page — detects ToS, extracts text, messages the background worker |
| `background/service-worker.js` | Calls the backend API, stores results per tab |
| `popup/popup.html` | UI shell |
| `popup/popup.css` | Styles — severity color coding, cards, spinner |
| `popup/popup.js` | Renders results, handles all UI states |

### How to load the extension in Chrome

1. Open Chrome and go to `chrome://extensions`
2. Enable **Developer mode** (top right toggle)
3. Click **Load unpacked**
4. Select the `extension/` folder in this repo

The extension icon will appear in your toolbar. Every time you edit a file, click the refresh icon on `chrome://extensions` to reload it.

### How to test it end-to-end

1. Start the backend (see Person B's section below) — the extension sends requests to `http://localhost:8000`
2. Navigate to any Terms of Service page (e.g. `https://policies.google.com/terms`)
3. Click the extension icon — the popup should show a loading spinner, then the analysis

### How to test the popup UI without the backend

Open `popup/popup.js` and temporarily hardcode a mock result at the top of `init()`:

```js
async function init() {
  // Temporary mock — remove before merging
  renderResult({
    tldr: "This is a test summary.",
    clauses: [{
      quote: "We may share your data.",
      plain_english: "They can give your info to other companies.",
      category: "data_sharing_third_parties",
      severity: "high",
      concept: "Surveillance Capitalism (Zuboff)"
    }]
  });
  return;
  // ... rest of function
}
```

### Key Chrome Extension concepts to know

- **Content scripts** run in the context of web pages but cannot directly access `chrome.*` APIs — they communicate with the background worker via `chrome.runtime.sendMessage`
- **Service workers** (background scripts) are the hub — they can call APIs and access `chrome.storage`
- **Manifest V3** is the current standard — do not use Manifest V2 patterns (no `background.persistent`, no `chrome.browserAction`)
- `chrome.storage.session` stores data only for the current browser session (cleared when browser closes)

### Things to implement / finish

- [ ] Add extension icons (`icons/icon16.png`, `icons/icon48.png`, `icons/icon128.png`) — any 16×16, 48×48, 128×128 PNG will work for dev
- [ ] Handle the `loading` state in `popup.js` — currently shows spinner but does not auto-refresh when the result arrives. Use `chrome.storage.onChanged` to listen for updates
- [ ] Test text extraction on at least 3 real ToS pages and verify it captures the right content

---

---

## Person B — Backend API

**Files:** `backend/`
**Language:** Python 3.11+

### What you own

| File | Purpose |
|------|---------|
| `main.py` | FastAPI app, CORS configuration |
| `routes/analyze.py` | `POST /analyze` endpoint |
| `routes/health.py` | `GET /health` endpoint |
| `services/ai_service.py` | Calls the ai_pipeline, handles retries |
| `models/schemas.py` | Pydantic models for request and response validation |
| `requirements.txt` | Python dependencies |

### Setup

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### Running the server

```bash
uvicorn main:app --reload
```

The server starts at `http://localhost:8000`. The `--reload` flag restarts it automatically when you save a file.

### Verify it works

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "ok", "timestamp": "2026-06-27T10:00:00+00:00"}
```

### Testing the analyze endpoint manually

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "We may collect your personal data including your name, email address, and browsing behavior. We share this information with our advertising partners to deliver targeted content. By using our service you agree to these terms.", "domain": "example.com"}'
```

You can also use the automatic interactive docs at `http://localhost:8000/docs` (FastAPI generates these for free).

### How the request flows through your code

```
POST /analyze
  → routes/analyze.py        validates the request body via Pydantic
  → services/ai_service.py   calls ai_pipeline, handles errors
  → ai_pipeline/pipeline.py  (Person C's code) checks cache, calls Claude, returns result
  ← routes/analyze.py        wraps result in AnalyzeResponse and returns it
```

### Connecting to Person C's code

`services/ai_service.py` imports from `ai_pipeline/`. While developing, the file uses a `_mock_api_call()` function so you do not need Person C's code ready to test your endpoints. When Person C's pipeline is ready, replace the mock:

```python
# In services/ai_service.py — swap this:
raw_response = _mock_api_call(text)

# For this:
from pipeline import analyze_tos
result = analyze_tos(text, domain)
return result
```

### Error handling reference

| Situation | HTTP status | When to return it |
|-----------|-------------|-------------------|
| Text too short or empty | 400 | Input validation fails |
| AI service is down | 503 | Claude API unreachable |
| Claude rate limit hit | 429 | Too many requests |
| Unexpected crash | 500 | Anything else |

### Deployment (when ready)

1. Create a free account on [Render](https://render.com) or [Railway](https://railway.app)
2. Connect the GitHub repo
3. Set root directory to `backend/`
4. Set start command to: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables in the dashboard (copy from `.env.example`)
6. Update `API_URL` in `extension/background/service-worker.js` to the deployed URL

---

---

## Person C — AI Pipeline + Data Layer

**Files:** `ai_pipeline/`
**Language:** Python 3.11+

### What you own

| File | Purpose |
|------|---------|
| `models.py` | Data types, valid category/concept/severity values |
| `prompt.py` | System prompt and user prompt builder |
| `parser.py` | Extract and validate JSON from Claude's response |
| `cache.py` | SQLite-based cache, SHA-256 keyed by ToS text |
| `pipeline.py` | Main entry point — `analyze_tos(text, domain)` |
| `tests/test_parser.py` | Unit tests for the parser |
| `tests/test_cache.py` | Unit tests for the cache |
| `tests/sample_tos/` | Real ToS fragments for manual testing |

### Setup

```bash
cd ai_pipeline
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
```

Make sure your `.env` file in the project root has `ANTHROPIC_API_KEY` set.

### Running the tests

```bash
pytest tests/ -v
```

All tests should pass without an API key — they test the parser and cache in isolation using mock data.

### Testing the full pipeline against a real ToS

1. Paste a fragment of a real ToS into `tests/sample_tos/google_fragment.txt`
2. Run this one-off script from `ai_pipeline/`:

```bash
python -c "
from dotenv import load_dotenv
load_dotenv('../.env')
from pipeline import analyze_tos

with open('tests/sample_tos/google_fragment.txt') as f:
    text = f.read()

result = analyze_tos(text, domain='google.com')
import json
print(json.dumps(result, indent=2))
"
```

### How the pipeline works

```
analyze_tos(text, domain)
  │
  ├─ compute_hash(text)          → SHA-256 fingerprint of the input
  ├─ get_cached(hash)            → return immediately if already analyzed
  │
  ├─ build_prompt(text)          → construct system + user messages
  ├─ _call_claude(...)           → send to Claude API, get raw string back
  ├─ parse_response(raw)         → extract JSON, validate with Pydantic
  ├─ store_result(hash, result)  → save to SQLite
  │
  └─ return result
```

### Working on the prompt

The prompt lives in `prompt.py`. The most important thing is that Claude returns **valid JSON every time** in exactly the schema everyone agreed on.

Tips for iterating:
- Test your prompt changes against all files in `tests/sample_tos/` before declaring it done
- If Claude adds prose before or after the JSON, the `parser.py` will handle it — but try to minimize this with clear instructions in the prompt
- Use phrases like "Return ONLY valid JSON. Do not include any text before or after the JSON object." in the system prompt
- Check that category, severity, and concept values in the output always match the allowed values in `models.py`

### Understanding the cache

The cache prevents paying for the same API call twice. When the backend receives a ToS text:
1. A SHA-256 hash of the text is computed
2. The DB is checked — if a row with that hash exists, the stored result is returned instantly
3. If not, Claude is called and the result is saved

The database file is `analyses.db` in the `ai_pipeline/` directory (created automatically on first run). In production, set `DATABASE_PATH` in `.env` to a PostgreSQL connection string.

### What good output looks like

Run the pipeline against Google, TikTok, and Meta ToS fragments and check:
- Does the TLDR accurately summarize the document in 2–3 sentences?
- Are the most important clauses being found (data collection, third-party sharing, rights modification)?
- Is the severity consistent — e.g. "we share your data with advertisers" should always be `high`?
- Are the concept labels accurate to the course framework?
- Does the parser handle the response without errors every single time?

---

---

## Running everything together locally

**Terminal 1 — Backend:**
```bash
cd backend
source venv/bin/activate      # Windows: venv\Scripts\activate
uvicorn main:app --reload
# Runs at http://localhost:8000
```

**Terminal 2 — Website:**
```bash
cd website
python3 -m http.server 3000
# Runs at http://localhost:3000
```

**Terminal 3 — Extension:**
No extra server needed. Load `extension/` in Chrome via `chrome://extensions` → Load unpacked.

The AI pipeline runs inside the backend process — no separate terminal needed. It is loaded automatically when the backend starts.

### Test the analyze endpoint directly

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "text": "We may collect your personal data and share it with advertising partners. We can terminate your account at any time for any reason.",
    "domain": "example.com",
    "profile": "general"
  }'
```

### Environment variables

| Variable | Description |
|----------|-------------|
| `LLMAPI_KEY` | API key for LLMapi (Claude access) |
| `LLMAPI_BASE_URL` | `https://api.llmapi.ai/v1` |
| `DATABASE_PATH` | Path to SQLite DB (default: `ai_pipeline/analyses.db`) |

---

## Implemented features

All 9 planned features are implemented. See `PLAN.md` for full technical breakdown.

| # | Feature | Where |
|---|---------|--------|
| 1 | Risk scoring (1–10 + SAFE/CAUTION/RISKY/DANGEROUS) | `backend/services/scoring_service.py` |
| 2 | Plain-English clause summaries | `ai_pipeline/prompt.py` |
| 3 | Deep-explain mode per clause | `POST /explain`, `ai_pipeline/explain_prompt.py` |
| 4 | PDF report export | `GET /report/{domain}`, `backend/services/report_service.py` |
| 5 | Privacy alternatives (AI-generated, cached) | `backend/services/alternatives_service.py` |
| 6 | User risk profiles (General / Journalist / Activist / Business) | `ai_pipeline/prompt.py` → `PROFILE_ADDITIONS` |
| 7 | Statistics dashboard | `GET /stats`, `extension/popup/stats.html` |
| 8 | Version diffing (detect ToS changes) | `backend/services/diff_service.py` |
| 9 | Change alerts (subscribe + Chrome notifications) | `POST /subscribe`, `extension/background/service-worker.js` |

---

## Common problems

**Extension popup says "No Terms of Service detected"**
The content script checks the URL and page headings. Try on a page with "terms" or "privacy" in the URL, or add a `console.log` in `content.js` to see what it detects.

**`POST /analyze` returns 400**
The text sent is either too short (under 100 chars) or too long (over 20 000 chars). Check what the content script is extracting.

**Claude returns malformed JSON**
The parser in `parser.py` tries three strategies to extract JSON. If all fail it raises a `ValueError` — add a `print(raw_response)` in `pipeline.py` before the parse call to see what Claude actually returned, then adjust the prompt.

**`ANTHROPIC_API_KEY` not found**
Make sure `.env` is in the project root (not inside `backend/` or `ai_pipeline/`) and that you ran `load_dotenv()` before importing the pipeline. The backend loads it via `python-dotenv` at startup.

**CORS error in the extension**
The extension's origin looks like `chrome-extension://abc123...`. In `backend/main.py`, `allow_origins=["*"]` covers this during development. If you restrict it later, you cannot set a specific `chrome-extension://` origin in CORS — instead, validate on the server side by checking a shared secret header.
