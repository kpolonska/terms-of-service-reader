# Implementation Plan — Planned Features

This document specifies how each planned feature should be implemented across all three system components. Read `README.md` for feature descriptions and motivation.

Each feature lists:
- Files to create or modify
- API contract changes (if any)
- Implementation notes
- Dependencies on other features

---

## Feature 1 — ToS version diffing

**Goal:** Detect when a previously analyzed domain updates its ToS and show what changed.

### Backend — `backend/`

**Modify** `models/schemas.py`:
```python
class AnalyzeResponse(BaseModel):
    tldr: str
    clauses: list[Clause]
    cached: bool
    analyzed_at: str
    score: str | None = None          # added by Feature 6
    diff: VersionDiff | None = None   # new

class VersionDiff(BaseModel):
    previous_analyzed_at: str
    changed_clauses: list[ChangedClause]

class ChangedClause(BaseModel):
    category: str
    previous_severity: str
    current_severity: str
    direction: str  # "worse" | "better" | "new" | "removed"
```

**Modify** `ai_pipeline/cache.py`:
- Add `version INTEGER DEFAULT 1` column to `analyses` table
- Add `get_previous_result(domain)` function — returns the second-most-recent row for a domain
- Modify `store_result` to increment version instead of `DO NOTHING` on conflict when hash differs

**Create** `backend/services/diff_service.py`:
```python
def compute_diff(previous: dict, current: dict) -> dict | None:
    """Compare two analysis results, return diff or None if identical."""
```

**Modify** `backend/routes/analyze.py`:
- After getting result, call `diff_service.compute_diff(previous, current)`
- Include diff in `AnalyzeResponse`

### Extension — `extension/`

**Modify** `popup/popup.js`:
- If `response.diff` is present, show a "What changed" section at the top
- Color-code direction: red arrow for "worse", green for "better", blue for "new"

**Modify** `popup/popup.css`:
- Add `.diff-card`, `.diff-worse`, `.diff-better`, `.diff-new` styles

---

## Feature 2 — User risk profile

**Goal:** Let users select a profile that reweights which findings are most relevant to them.

### Extension — `extension/`

**Modify** `popup/popup.html`:
- Add profile selector dropdown before or after analysis result: General / Journalist / Activist / Business

**Modify** `popup/popup.js`:
- Save selected profile to `chrome.storage.local`
- Pass `profile` field in the request sent by service worker

**Modify** `background/service-worker.js`:
- Read profile from storage, include it in `POST /analyze` body

### Backend — `backend/`

**Modify** `models/schemas.py`:
```python
VALID_PROFILES = {"general", "journalist", "activist", "business"}

class AnalyzeRequest(BaseModel):
    text: str
    domain: str | None = None
    profile: str = "general"

    @field_validator("profile")
    @classmethod
    def validate_profile(cls, v):
        if v not in VALID_PROFILES:
            raise ValueError(f"Invalid profile. Must be one of: {VALID_PROFILES}")
        return v
```

**Modify** `backend/services/ai_service.py`:
- Pass `profile` to `analyze_tos(text, domain, profile)`

### AI Pipeline — `ai_pipeline/`

**Modify** `prompt.py`:
- Accept `profile` param in `build_prompt(tos_text, profile="general")`
- Append profile-specific instruction to system prompt:

```python
PROFILE_INSTRUCTIONS = {
    "journalist": "Pay special attention to clauses about anonymity, source protection, data disclosure to governments, and account termination.",
    "activist": "Prioritize clauses about data sharing with law enforcement, account suspension, and content moderation.",
    "business": "Focus on clauses about intellectual property, content ownership, and liability.",
    "general": "",
}
```

**Modify** `pipeline.py`:
- Accept and pass `profile` param through to `build_prompt`

---

## Feature 3 — Alternatives recommendation

**Goal:** When a ToS is high-risk, suggest privacy-respecting alternative services.

### Backend — `backend/`

**Create** `backend/data/alternatives.json`:
```json
{
  "google.com": [
    {"name": "Proton", "url": "proton.me", "reason": "End-to-end encryption, no ad targeting"},
    {"name": "Tutanota", "url": "tuta.com", "reason": "Zero-knowledge encryption"}
  ],
  "docs.google.com": [
    {"name": "Cryptpad", "url": "cryptpad.fr", "reason": "Zero-knowledge collaborative editing"},
    {"name": "Notion", "url": "notion.so", "reason": "Less aggressive data collection"}
  ]
}
```

**Create** `backend/services/alternatives_service.py`:
```python
def get_alternatives(domain: str, score: str) -> list[dict]:
    """Return alternatives if score is D or F, else empty list."""
```

**Modify** `models/schemas.py`:
```python
class Alternative(BaseModel):
    name: str
    url: str
    reason: str

class AnalyzeResponse(BaseModel):
    ...
    alternatives: list[Alternative] = []
```

**Modify** `routes/analyze.py`:
- Call `alternatives_service.get_alternatives(domain, score)` and include in response

### Extension — `extension/`

**Modify** `popup/popup.js`:
- If `response.alternatives` is non-empty, render "Consider these alternatives" section
- Each alternative shows name, URL (as link), and reason

---

## Feature 4 — Change alerts

**Goal:** Notify the user when a previously analyzed ToS has changed.

### Backend — `backend/`

**Create** `backend/routes/subscribe.py`:
```python
@router.post("/subscribe")
async def subscribe(domain: str, url: str):
    """Store domain + URL for periodic re-analysis."""

@router.delete("/subscribe")
async def unsubscribe(domain: str):
    """Remove domain from watch list."""

@router.get("/subscriptions")
async def list_subscriptions():
    """Return all watched domains."""
```

**Modify** `ai_pipeline/cache.py`:
- Add `subscriptions` table: `(domain TEXT, url TEXT, last_hash TEXT, subscribed_at TIMESTAMP)`

**Create** `backend/services/watcher_service.py`:
- `check_all_subscriptions()` — iterates subscriptions, fetches URL, extracts text, computes hash, compares to `last_hash`, triggers notification if changed
- Run on a schedule (APScheduler or a simple background thread on startup)

**Modify** `backend/main.py`:
- Start watcher background task on app startup using `lifespan` context manager

**Create** `backend/routes/notifications.py`:
- `GET /notifications` — returns pending change notifications for the extension to poll

### Extension — `extension/`

**Modify** `background/service-worker.js`:
- Poll `GET /notifications` every 30 minutes using `chrome.alarms`
- Call `chrome.notifications.create()` when changes detected

**Modify** `popup/popup.js`:
- Add subscribe/unsubscribe toggle button after analysis

---

## Feature 5 — Deep-explain mode

**Goal:** On-demand deeper explanation of a single clause with a real-world example.

### Backend — `backend/`

**Create** `backend/routes/explain.py`:
```python
@router.post("/explain")
async def explain_clause(request: ExplainRequest) -> ExplainResponse:
    ...
```

**Modify** `models/schemas.py`:
```python
class ExplainRequest(BaseModel):
    quote: str
    category: str
    domain: str | None = None
    profile: str = "general"

class ExplainResponse(BaseModel):
    detailed_explanation: str
    real_world_example: str
    what_you_can_do: str
```

**Create** `backend/services/explain_service.py`:
- Calls `ai_pipeline` with a focused prompt for one clause

### AI Pipeline — `ai_pipeline/`

**Create** `ai_pipeline/explain_prompt.py`:
```python
def build_explain_prompt(quote: str, category: str, profile: str) -> tuple[str, str]:
    """Build a prompt that asks Claude to explain one clause in depth."""
```

**Modify** `pipeline.py` or create `explain_pipeline.py`:
- `explain_clause(quote, category, domain, profile) -> dict`

### Extension — `extension/`

**Modify** `popup/popup.js`:
- Add "Explain more" button to each clause card
- On click: send `POST /explain` with clause data, show expanded explanation below card

---

## Feature 6 — Overall privacy score (A–F)

**Goal:** Single letter grade summarizing the overall risk of a ToS.

### Backend — `backend/`

**Create** `backend/services/scoring_service.py`:
```python
def compute_score(clauses: list[dict]) -> str:
    """
    Scoring logic:
    - Count high/medium/low severity clauses
    - Weight by category danger (data_sharing_third_parties and behavioral_analysis weighted higher)
    - Map weighted score to A/B/C/D/F
    Returns letter grade.
    """
```

Scoring table:
| Weighted score | Grade |
|----------------|-------|
| 0–10 | A |
| 11–25 | B |
| 26–45 | C |
| 46–65 | D |
| 66+ | F |

Weight per severity: high=10, medium=4, low=1. Category multipliers: `behavioral_analysis` ×1.5, `data_sharing_third_parties` ×1.5, others ×1.0.

**Modify** `models/schemas.py`:
```python
class AnalyzeResponse(BaseModel):
    ...
    score: str  # "A" | "B" | "C" | "D" | "F"
```

**Modify** `routes/analyze.py`:
- Call `scoring_service.compute_score(result["clauses"])` and include in response

### Extension — `extension/`

**Modify** `popup/popup.js`:
- Show score badge at top of popup (large letter, color-coded)

**Modify** `popup/popup.css`:
- `.score-a { background: #2ecc71 }`, `.score-b { background: #27ae60 }`, `.score-c { background: #f39c12 }`, `.score-d { background: #e67e22 }`, `.score-f { background: #e74c3c }`

*Feature 6 is a prerequisite for Features 3 and 7.*

---

## Feature 7 — Toolbar badge color

**Goal:** Show colored icon badge automatically when on a ToS page, without opening popup.

### Extension — `extension/`

**Modify** `background/service-worker.js`:
- After receiving analysis result, call:
```js
const SCORE_COLORS = { A: '#2ecc71', B: '#27ae60', C: '#f39c12', D: '#e67e22', F: '#e74c3c' }
chrome.action.setBadgeText({ text: result.score, tabId })
chrome.action.setBadgeBackgroundColor({ color: SCORE_COLORS[result.score], tabId })
```

*Requires Feature 6 (score field in response).*

---

## Feature 8 — Statistics dashboard

**Goal:** Aggregated view across all analyzed ToS documents stored in local cache.

### Backend — `backend/`

**Create** `backend/routes/stats.py`:
```python
@router.get("/stats")
async def get_stats() -> StatsResponse:
    ...
```

**Modify** `models/schemas.py`:
```python
class StatsResponse(BaseModel):
    total_analyzed: int
    most_dangerous_domains: list[dict]   # [{domain, score, analyzed_at}]
    category_distribution: dict[str, int]  # {category: count}
    concept_distribution: dict[str, int]   # {concept: count}
    severity_distribution: dict[str, int]  # {high: N, medium: N, low: N}
    average_score: str
```

**Create** `backend/services/stats_service.py`:
- Query SQLite `analyses` table
- Parse stored `result_json` to aggregate category/concept/severity counts
- Sort domains by score

**Modify** `ai_pipeline/cache.py`:
- Add helper `get_all_results() -> list[dict]` for stats queries

### Extension — `extension/`

**Create** `popup/stats.html` — new popup page (linked from main popup header)
**Create** `popup/stats.js` — fetches `GET /stats`, renders charts using plain JS canvas or SVG (no external libs — CSP blocks CDNs)
**Create** `popup/stats.css`

**Modify** `popup/popup.html`:
- Add "Stats" link/button in popup header

---

## Feature 9 — PDF report export

**Goal:** Download a formatted PDF of the full ToS analysis.

### Backend — `backend/`

**Add to** `backend/requirements.txt`:
```
reportlab==4.2.2
```

**Create** `backend/routes/report.py`:
```python
@router.get("/report/{domain}")
async def export_report(domain: str):
    """Generate and return PDF report for the most recent analysis of a domain."""
    ...
    return Response(content=pdf_bytes, media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename={domain}-tos-report.pdf"})
```

**Create** `backend/services/report_service.py`:
```python
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, ...

def generate_pdf(domain: str, result: dict) -> bytes:
    """Build PDF with: header, score badge, TLDR, clauses table, metadata footer."""
```

PDF layout:
1. Title: "ToS Analysis — {domain}" + analyzed date
2. Overall score (colored)
3. TLDR paragraph
4. Table of clauses: Quote | Plain English | Category | Severity | Concept
5. Footer: "Generated by ToS Reader"

### Extension — `extension/`

**Modify** `popup/popup.js`:
- Add "Download Report" button after analysis renders
- On click: open `GET /report/{domain}` in new tab (browser handles PDF download)

---

## Implementation order (recommended)

Dependencies flow bottom-up. Implement in this order to avoid blocked work:

```
Feature 6 (score)
    ├── Feature 3 (alternatives — needs score)
    └── Feature 7 (badge — needs score)

Feature 1 (version diff) — independent
Feature 2 (risk profile) — independent
Feature 5 (deep explain) — independent
Feature 8 (stats) — independent
Feature 9 (PDF) — independent
Feature 4 (alerts) — independent, most complex
```

Suggested sequence:
1. Feature 6 — small, pure backend, unblocks others
2. Feature 7 — small, pure extension, immediate visual value
3. Feature 1 — core value, medium complexity
4. Feature 8 — high academic value, medium complexity
5. Feature 5 — good UX, medium complexity
6. Feature 9 — good for presentations, medium complexity
7. Feature 2 — medium complexity, good research angle
8. Feature 3 — low complexity once score exists
9. Feature 4 — most complex, leave for last

---

## Files created/modified summary

| File | Action | Feature(s) |
|------|--------|-----------|
| `backend/models/schemas.py` | modify | 1, 2, 3, 5, 6, 8 |
| `backend/routes/analyze.py` | modify | 1, 3, 6 |
| `backend/routes/explain.py` | create | 5 |
| `backend/routes/stats.py` | create | 8 |
| `backend/routes/report.py` | create | 9 |
| `backend/routes/subscribe.py` | create | 4 |
| `backend/routes/notifications.py` | create | 4 |
| `backend/services/diff_service.py` | create | 1 |
| `backend/services/scoring_service.py` | create | 6 |
| `backend/services/alternatives_service.py` | create | 3 |
| `backend/services/explain_service.py` | create | 5 |
| `backend/services/stats_service.py` | create | 8 |
| `backend/services/report_service.py` | create | 9 |
| `backend/services/watcher_service.py` | create | 4 |
| `backend/data/alternatives.json` | create | 3 |
| `backend/requirements.txt` | modify | 9 |
| `backend/main.py` | modify | 4 |
| `ai_pipeline/cache.py` | modify | 1, 4, 8 |
| `ai_pipeline/prompt.py` | modify | 2 |
| `ai_pipeline/pipeline.py` | modify | 2, 5 |
| `ai_pipeline/explain_prompt.py` | create | 5 |
| `extension/popup/popup.js` | modify | 1, 2, 3, 4, 5, 6, 7, 9 |
| `extension/popup/popup.html` | modify | 1, 2, 3, 4, 5, 6, 8 |
| `extension/popup/popup.css` | modify | 1, 3, 6 |
| `extension/popup/stats.html` | create | 8 |
| `extension/popup/stats.js` | create | 8 |
| `extension/popup/stats.css` | create | 8 |
| `extension/background/service-worker.js` | modify | 2, 4, 7 |
