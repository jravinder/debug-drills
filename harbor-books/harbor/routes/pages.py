"""Server-rendered pages."""
import json

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse

import settings
from harbor.db import get_conn
from harbor.services import metrics, sales, stores
from harbor.templating import load_tenant, render

router = APIRouter()


@router.get("/t/{slug}/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, slug: str, conn=Depends(get_conn)):
    tenant = load_tenant(conn, slug)
    days = settings.KPI_WINDOW_DAYS
    categories = metrics.revenue_by_category(conn, tenant["id"], days)
    return render(request, "dashboard.html", conn, tenant, section="dashboard",
                  kpis=metrics.kpis(conn, tenant["id"], days), days=days,
                  chart_days=settings.CHART_WINDOW_DAYS,
                  categories_json=json.dumps(categories),
                  top=stores.top_stores(conn, tenant["id"], days),
                  low=metrics.low_stock(conn, tenant["id"], limit=8))


@router.get("/t/{slug}/stores", response_class=HTMLResponse)
def stores_index(request: Request, slug: str, q: str = "", region: str = "", sort: str = "name",
                 dir: str = "", page: int = 1, conn=Depends(get_conn)):
    tenant = load_tenant(conn, slug)
    result = stores.list_stores(conn, tenant["id"], q=q.strip(), region=region, sort=sort, direction=dir, page=page)
    return render(request, "stores.html", conn, tenant, section="stores", q=q, region=region,
                  regions=stores.regions(conn, tenant["id"]), days=settings.KPI_WINDOW_DAYS, **result)


@router.get("/t/{slug}/stores/{code}", response_class=HTMLResponse)
def store_detail(request: Request, slug: str, code: str, conn=Depends(get_conn)):
    tenant = load_tenant(conn, slug)
    store = stores.get_store(conn, tenant["id"], code)
    if store is None:
        raise HTTPException(404, "store not found")
    days = settings.KPI_WINDOW_DAYS
    perf = stores.store_performance(conn, tenant["id"], store["id"], days)
    series = stores.store_daily_revenue(conn, tenant["id"], store["id"], days)
    return render(request, "store_detail.html", conn, tenant, section="stores", store=store, perf=perf, days=days,
                  series_json=json.dumps(series),
                  titles=stores.store_top_titles(conn, tenant["id"], store["id"], days),
                  low=metrics.low_stock(conn, tenant["id"], limit=10, store_id=store["id"]))


@router.get("/t/{slug}/sales", response_class=HTMLResponse)
def sales_index(request: Request, slug: str, store: str = "", days: int = 30, page: int = 1, conn=Depends(get_conn)):
    tenant = load_tenant(conn, slug)
    days = days if days in (7, 30, 90) else 30
    result = sales.sale_lines_page(conn, tenant["id"], page, settings.SALES_PER_PAGE, store_code=store, days=days)
    store_codes = [r[0] for r in conn.execute("SELECT code FROM stores WHERE tenant_id = ? ORDER BY code", (tenant["id"],))]
    return render(request, "sales.html", conn, tenant, section="sales", store=store, days=days,
                  store_codes=store_codes, **result)


@router.get("/t/{slug}/inventory", response_class=HTMLResponse)
def inventory_index(request: Request, slug: str, page: int = 1, conn=Depends(get_conn)):
    tenant = load_tenant(conn, slug)
    per_page = 50
    total = metrics.kpis(conn, tenant["id"], settings.KPI_WINDOW_DAYS)["low_stock"]
    page_count = max(1, -(-total // per_page))
    page = min(max(1, page), page_count)
    rows = metrics.low_stock(conn, tenant["id"], limit=per_page, offset=(page - 1) * per_page)
    return render(request, "inventory.html", conn, tenant, section="inventory", rows=rows, total=total,
                  page=page, page_count=page_count)
