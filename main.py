import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from routes import router as api_router

app = FastAPI(title="Bookmark Buddy Lite", version="0.1.0")

# Health check
@app.get("/health", response_class=JSONResponse)
async def health() -> dict:
    return {"status": "ok"}

# Root landing page – dark themed inline CSS
@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request) -> str:
    html = f"""
    <!DOCTYPE html>
    <html lang='en'>
    <head>
      <meta charset='UTF-8'>
      <title>Bookmark Buddy Lite</title>
      <style>
        body {{ background:#111; color:#eee; font-family:Arial,Helvetica,sans-serif; padding:2rem; }}
        a {{ color:#4ea5d9; }}
        h1 {{ color:#fff; }}
        .section {{ margin-bottom:1.5rem; }}
        pre {{ background:#222; padding:0.5rem; overflow:auto; }}
      </style>
    </head>
    <body>
      <h1>Bookmark Buddy Lite</h1>
      <p>Fast, private web‑page saver – one click, no frills.</p>

      <div class='section'>
        <h2>API Endpoints</h2>
        <ul>
          <li><strong>GET</strong> <code>/health</code> – health check</li>
          <li><strong>POST</strong> <code>/api/bookmarks</code> – add a bookmark</li>
          <li><strong>GET</strong> <code>/api/bookmarks</code> – list/search bookmarks</li>
          <li><strong>GET</strong> <code>/api/bookmarks/export</code> – export all as JSON</li>
          <li><strong>POST</strong> <code>/api/bookmarks/{{id}}/ai-tags</code> – generate AI tags</li>
          <li><strong>POST</strong> <code>/api/bookmarks/{{id}}/ai-summarize</code> – generate AI summary</li>
        </ul>
      </div>

      <div class='section'>
        <h2>Tech Stack</h2>
        <ul>
          <li>FastAPI 0.115.0 (Python 3.12+)</li>
          <li>PostgreSQL via SQLAlchemy 2.0.35</li>
          <li>DigitalOcean Serverless Inference (model: {os.getenv('DO_INFERENCE_MODEL', 'openai-gpt-oss-120b')})</li>
          <li>Tailwind CSS (frontend) – not shown here</li>
        </ul>
      </div>

      <div class='section'>
        <p>OpenAPI docs: <a href='{request.url_for('openapi')}'>/docs</a> • <a href='{request.url_for('redoc')}'>/redoc</a></p>
      </div>
    </body>
    </html>
    """
    return html

# Include API router under /api prefix
app.include_router(api_router, prefix="/api")
