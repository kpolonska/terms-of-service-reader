from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root():
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>ToS Reader API</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
           max-width: 640px; margin: 60px auto; padding: 24px; line-height: 1.6;
           color: #1a1a1a; }
    h1 { margin-bottom: 8px; }
    .tagline { color: #666; margin-bottom: 32px; }
    h3 { margin-top: 32px; margin-bottom: 12px; }
    ul { padding-left: 20px; }
    li { margin-bottom: 6px; }
    a { color: #6366f1; }
    code { background: #f3f4f6; padding: 2px 6px; border-radius: 4px; font-size: 0.9em; }
    footer { margin-top: 48px; padding-top: 24px; border-top: 1px solid #e5e7eb;
             color: #888; font-size: 14px; }
  </style>
</head>
<body>
  <h1>ToS Reader API</h1>
  <p class="tagline">Analyses Terms of Service documents. Backend for the ToS Reader Chrome extension.</p>

  <h3>Try it interactively</h3>
  <ul>
    <li><a href="/docs">/docs</a> &mdash; Swagger UI (click "Try it out" on any endpoint)</li>
    <li><a href="/redoc">/redoc</a> &mdash; ReDoc alternative view</li>
  </ul>

  <h3>Endpoints</h3>
  <ul>
    <li><code>POST /analyze</code> &mdash; analyse a ToS document</li>
    <li><code>POST /explain</code> &mdash; deep-explain a single clause</li>
    <li><code>GET /report/{domain}</code> &mdash; download PDF report</li>
    <li><code>GET /stats</code> &mdash; usage statistics</li>
    <li><code>POST /subscribe</code> &mdash; subscribe to change alerts</li>
    <li><a href="/health">GET /health</a> &mdash; health check</li>
  </ul>

  <footer>
    Source: <a href="https://github.com/kpolonska/terms-of-service-reader">github.com/kpolonska/terms-of-service-reader</a>
  </footer>
</body>
</html>"""
