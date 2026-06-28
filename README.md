# ToS Reader — Browser Extension

A Chrome extension that analyzes Terms of Service documents and explains what you're agreeing to in plain English. Built as a research project exploring surveillance capitalism, datafication, and platformization through the lens of real corporate legal documents.

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
├── extension/          ← Chrome extension (Person A)
├── backend/            ← FastAPI server (Person B)
├── ai_pipeline/        ← Claude integration + cache (Person C)
├── .env.example        ← environment variable template
└── .gitignore
```

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

Open three terminal windows:

**Terminal 1 — Backend:**
```bash
cd backend
venv\Scripts\activate   # or source venv/bin/activate on Mac/Linux
uvicorn main:app --reload
```

**Terminal 2 — AI pipeline (only needed for manual testing):**
```bash
cd ai_pipeline
venv\Scripts\activate
python -c "from pipeline import analyze_tos; print('pipeline ready')"
```

**Terminal 3 — Extension:**
No terminal needed. Load `extension/` in Chrome via `chrome://extensions` and test on a live ToS page.

---

## Planned features

The following enhancements are planned for future implementation. Each feature spans multiple parts of the system (extension, backend, ai\_pipeline). See `PLAN.md` for detailed implementation breakdown per feature.

### Data protection

**1. ToS version diffing**
Store each analyzed version of a ToS by domain. When the same domain is analyzed again and the text has changed, detect the diff and highlight which clauses changed severity (e.g. "data\_sharing\_third\_parties was medium → now high"). Requires: new `versions` table in SQLite, diff logic in backend, UI diff view in popup.

**2. User risk profile**
Let the user select a profile (General user / Journalist / Activist / Business) before or after analysis. Each profile reweights which clause categories are most important and adjusts the warnings shown. Requires: profile selector in popup, profile param in `POST /analyze`, adjusted scoring in ai\_pipeline.

**3. Alternatives recommendation**
When a ToS scores poorly overall, suggest privacy-respecting alternative services. Example: if Google Docs ToS is analyzed and scores D or F, suggest Notion or Cryptpad with a brief reason. Alternatives list can be a static lookup table keyed by domain category. Requires: new `alternatives` field in response schema, lookup table in backend, display card in popup.

**4. Change alerts**
User can opt in to be notified when a previously analyzed site updates its ToS. Backend periodically re-fetches and re-analyzes stored domains, compares hash to cached version, and triggers a Chrome notification if changed. Requires: `GET /subscribe` endpoint, background fetch job, Chrome notifications API in service worker.

### User understanding

**5. Deep-explain mode**
Clicking a clause card sends a follow-up request for a longer explanation with a concrete real-world example of how that clause could affect the user personally. Requires: new `POST /explain` endpoint, second Claude call with a focused prompt, expandable card UI in popup.

**6. Overall privacy score (A–F)**
Compute a letter grade for each analyzed ToS based on clause severity distribution: count of high/medium/low findings, presence of specific high-risk categories. Display prominently at the top of the popup. Requires: scoring function in backend, `score` field added to response schema, score badge in popup.

**7. Toolbar badge color**
Show a colored dot on the extension icon automatically when a ToS page is detected — red (high risk), yellow (medium), green (low or unknown). No click needed. Requires: backend returns score, service worker calls `chrome.action.setBadgeBackgroundColor` and `setBadgeText`.

### Academic / research value

**8. Statistics dashboard**
New popup tab showing aggregated stats across all analyzed sites stored in the local cache: most common clause categories, most dangerous domains, distribution across academic concepts (Zuboff / Van Dijck / Srnicek / Pasquale). Requires: new `GET /stats` endpoint on backend, aggregation queries on SQLite, new tab in popup UI.

**9. PDF report export**
Generate a formatted PDF of the full ToS analysis (TLDR, all clauses, score, metadata) that the user can download or share. Requires: PDF generation library in backend (e.g. `reportlab` or `weasyprint`), new `GET /report/{domain}` endpoint, download button in popup.

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
