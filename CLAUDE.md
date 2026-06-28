# ToS Reader — Project Context for Claude

## CRITICAL RULE
Never run `git commit` or `git push`. Only write git commands as text for the user to run manually.

---

## What exists

### Ecosystem overview
Three separate components that form one product:

1. **`ai_pipeline/`** — standalone Python AI module
2. **`backend/`** — FastAPI server that wraps the pipeline
3. **`extension/`** — Chrome extension (Manifest V3)
4. **`website/`** — dark SaaS landing page + live demo tool

---

### `ai_pipeline/`

Core AI logic. Runs independently of the backend (can be used as a library).

| File | Purpose |
|---|---|
| `pipeline.py` | Entry point: `analyze_tos(text, domain, profile)` and `generate_alternatives()`, `explain_clause()` |
| `tos_models.py` | Pydantic models: `Clause`, `AnalysisResult`. Also defines `CATEGORIES`, `CONCEPTS`, `SEVERITY_LEVELS` constants |
| `prompt.py` | Builds system prompt + user message. `PROFILE_ADDITIONS` dict for journalist/activist/business/general profiles |
| `parser.py` | Parses raw LLM JSON response into `AnalysisResult` |
| `cache.py` | SQLite cache (`analyses.db`). Tables: `analyses`, `alternatives_cache`, `subscriptions`. Also `init_db()` at module level |
| `alternatives_prompt.py` | Builds prompt for generating alternative service suggestions |
| `explain_prompt.py` | Builds prompt for clause deep-explanation |

**DB path**: resolved via `DATABASE_PATH` env var; defaults to `ai_pipeline/analyses.db` (absolute path set in service files).

**LLM**: OpenAI-compatible client pointing to `https://api.llmapi.ai/v1`, model `claude-haiku-4-5`. Key: `LLMAPI_KEY` env var.

**Concepts** (validated strictly, with author suffix):
- `Surveillance Capitalism (Zuboff)`
- `Datafication (Van Dijck)`
- `Platformization (Srnicek)`
- `Algorithmic Opacity (Pasquale)`
- `General Power Asymmetry`

Validator accepts short names (e.g. `"Surveillance Capitalism"`) and maps them to full names.

---

### `backend/`

FastAPI server. Run from `backend/` directory.

```bash
cd backend
source venv/bin/activate   # Python 3.14 venv
uvicorn main:app --reload
```

Listens on `http://localhost:8000`.

| Route | Method | Purpose |
|---|---|---|
| `/analyze` | POST | Main analysis endpoint |
| `/explain` | POST | Deep-explain a single clause |
| `/report/{domain}` | GET | Download PDF report |
| `/stats` | GET | Usage statistics |
| `/health` | GET | Health check |
| `/subscribe` | POST | Subscribe to domain change alerts |
| `/subscribe/{domain}` | DELETE | Unsubscribe |
| `/subscriptions` | GET | List subscriptions |

**Services:**
- `ai_service.py` — wraps `pipeline.analyze_tos`. Does sys.path manipulation to load ai_pipeline modules. Uses `load_dotenv(override=True)` — critical, otherwise shell env vars shadow .env.
- `scoring_service.py` — computes risk score (1–10) and label (SAFE/CAUTION/RISKY/DANGEROUS)
- `alternatives_service.py` — wraps `pipeline.generate_alternatives`
- `diff_service.py` — compares two most recent analyses for a domain
- `subscription_service.py` — wraps cache subscription functions

**sys.path / modules conflict** (solved):
- `backend/models/` is a Python package
- `ai_pipeline/models.py` was renamed to `ai_pipeline/tos_models.py` to avoid collision
- `ai_service.py` clears `sys.modules` entries for `("tos_models", "prompt", "pipeline", "cache", "parser")` before importing pipeline
- `diff_service.py` and `subscription_service.py` both do `sys.path.insert(0, ai_pipeline_path)` at module level — this runs before routes import, but since ai_pipeline no longer has `models.py`, no conflict

**Python version**: 3.14. `pydantic>=2.11.0` required (pydantic-core 2.46.4+ supports py3.14).

---

### `extension/`

Chrome extension, Manifest V3.

```
extension/
  manifest.json
  content/content.js       ← runs in page context
  background/service-worker.js
  popup/popup.html
  popup/popup.js
  popup/popup.css
  popup/stats.js
  icons/
```

**Flow:**
1. `content.js` runs in page on load (with 2.5s delay for SPA rendering)
2. Also listens for `GET_TOS_TEXT` message from popup (on-demand extraction)
3. Popup opens → checks service worker for cached result → if none, sends `GET_TOS_TEXT` to content script → sends `TOS_TEXT_FROM_POPUP` to service worker with explicit `tabId`
4. Service worker calls backend `/analyze` → stores result in `chrome.storage.session` keyed by `result_{tabId}`
5. Popup listens for `chrome.storage.onChanged` → renders result when ready

**Text extraction** (`content.js`):
- Removes `script`, `style`, `noscript`, `nav`, `header`, `footer`, `aside`, cookie banners
- Uses `textContent` (not `innerText` — which is undefined on cloned off-document nodes)
- Prefers `<main>` / `<article>` / `[role='main']`, falls back to full body
- Max 15,000 chars

**ToS detection**: URL contains "terms"/"tos"/"privacy"/"legal" OR heading text matches.

**Permissions**: `tabs`, `activeTab`, `storage`, `notifications`, `http://localhost:8000/*`

**Design**: light dashboard — white bg, slate grays, indigo accent `#6366f1`.

**Loading while browsing**: for static pages, 2.5s setTimeout fires and sends text to service worker automatically. For SPAs (React, etc.), on-demand extraction from popup is the primary path.

---

### `website/`

Static dark SaaS landing page. Open `website/index.html` directly in browser (no server needed).

- **`index.html`** — landing page: hero, 9-feature grid, 3-step process, academic context section, live "Try online" panel
- **`style.css`** — dark design: `--bg: #030712`, `--accent: #7c3aed` (purple)
- **`app.js`** — handles live demo: POST to `http://localhost:8000/analyze`, renders results

The live demo requires the backend to be running.

---

## How to run

```bash
# 1. Backend
cd backend
source venv/bin/activate
uvicorn main:app --reload

# 2. Website (no server needed)
open website/index.html

# 3. Extension
# chrome://extensions → Load unpacked → select extension/ folder
# After code changes: reload extension in chrome://extensions
```

`.env` must be in project root with:
```
LLMAPI_KEY=...
LLMAPI_BASE_URL=https://api.llmapi.ai/v1
DATABASE_PATH=analyses.db   # overridden to absolute path by service files
```

---

## Known issues / gotchas

### Extension
- **SPA pages** (Facebook, Google, etc.): text extraction happens on-demand when popup opens (page is rendered by then). The 2.5s auto-send is a fallback for static pages only.
- **Result caching per tab**: result stored in `chrome.storage.session` keyed by `result_{tabId}`. If user navigates to a different ToS on same tab, old result may show briefly.
- **Debug print in ai_service.py**: `print(f"[ai_service] ...")` still present from debugging. Can be removed when stable.

### Backend
- `load_dotenv(override=True)` is required. Without `override=True`, if `LLMAPI_KEY` is set in shell env (e.g. from a previous session), `.env` values are ignored → 401 errors.
- `init_db()` runs at import time in `cache.py` (line 125). This is intentional.
- Uvicorn `--reload` only watches `backend/` directory. Changes to `ai_pipeline/` require manual restart.

### AI / pipeline
- LLM sometimes returns concept names without author suffix (e.g. `"Datafication"` instead of `"Datafication (Van Dijck)"`). Validator normalizes via prefix match.
- LLM may return fewer than 5 clauses for very short texts — no minimum enforced.

---

## What needs to be done

- [ ] Remove debug `print()` statements from `ai_service.py`
- [ ] Test extension on non-React ToS pages (e.g. `twitter.com/tos`, `apple.com/legal/internet-services/terms/site.html`)
- [ ] Fix UI bug: popup sometimes shows spinner AND result simultaneously (state transition race)
- [ ] `alternatives` always returns `[]` — `generate_alternatives` may need debugging
- [ ] Version diffing (`diff`) only works after 2 analyses of the same domain — first time always `null`
- [ ] Subscription notifications need testing (requires two analyses of subscribed domain)
- [ ] Website live demo: hardcoded `http://localhost:8000` — won't work when deployed
- [ ] PDF report endpoint (`/report/{domain}`) — verify reportlab generates correctly
- [ ] Extension icon in toolbar sometimes shows badge from old tab analysis
