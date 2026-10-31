"""Harbor Books web app. Run: uvicorn harbor.app:app --port 8765"""
import logging
import os
import time

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from harbor import db
from harbor.logging_setup import configure, kv
from harbor.routes import api, pages
from harbor.templating import TenantNotFound, templates

configure()
log = logging.getLogger("harbor.http")

app = FastAPI(title="Harbor Books", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")
app.include_router(pages.router)
app.include_router(api.router)


@app.middleware("http")
async def timing(request: Request, call_next):
    box = db.start_request_counter()
    t = time.perf_counter()
    response = await call_next(request)
    ms = (time.perf_counter() - t) * 1000
    response.headers["X-Query-Count"] = str(box[0])
    response.headers["X-Response-Time-Ms"] = f"{ms:.1f}"
    if not request.url.path.startswith("/static"):
        log.info(kv(event="request", method=request.method, path=request.url.path, status=response.status_code,
                    ms=f"{ms:.1f}", queries=box[0]))
    return response


@app.exception_handler(TenantNotFound)
async def tenant_not_found(request: Request, exc: TenantNotFound):
    if request.url.path.startswith("/api/"):
        return JSONResponse({"error": "unknown tenant", "tenant": exc.slug}, status_code=404)
    return templates.TemplateResponse(request, "404.html", {"slug": exc.slug, "tenant": None, "tenants": []},
                                      status_code=404)


@app.get("/healthz")
def healthz():
    conn = db.connect()
    try:
        version = conn.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0]
        tenants = conn.execute("SELECT COUNT(*) FROM tenants").fetchone()[0]
    finally:
        conn.close()
    return {"status": "ok", "schema_version": version, "tenants": tenants}


@app.get("/", response_class=HTMLResponse)
def index():
    conn = db.connect()
    try:
        first = db.all_tenants(conn)[0]["slug"]
    finally:
        conn.close()
    return RedirectResponse(f"/t/{first}/dashboard")
