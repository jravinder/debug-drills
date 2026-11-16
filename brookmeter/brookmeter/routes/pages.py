"""Server-rendered pages."""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse

import settings
from brookmeter.db import get_conn
from brookmeter.services import invoices, metrics, subscriptions, usage
from brookmeter.templating import load_tenant, render

router = APIRouter()


def bars(values, key):
    top = max((v[key] for v in values), default=0) or 1
    return [{**v, "pct": round(v[key] / top * 100, 1)} for v in values]


@router.get("/t/{slug}/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, slug: str, conn=Depends(get_conn)):
    tenant = load_tenant(conn, slug)
    days = settings.KPI_WINDOW_DAYS
    return render(request, "dashboard.html", conn, tenant, section="dashboard", days=days,
                  kpis=metrics.kpis(conn, tenant["id"], days),
                  months=bars(metrics.invoiced_by_month(conn, tenant["id"], settings.CHART_MONTHS), "cents"),
                  plans=bars(metrics.mrr_by_plan(conn, tenant["id"]), "mrr_cents"),
                  top=metrics.top_customers(conn, tenant["id"]),
                  recent=invoices.recent(conn, tenant["id"]))


@router.get("/t/{slug}/subscriptions", response_class=HTMLResponse)
def subscriptions_index(request: Request, slug: str, q: str = "", status: str = "", page: int = 1,
                        conn=Depends(get_conn)):
    tenant = load_tenant(conn, slug)
    result = subscriptions.list_subscriptions(conn, tenant["id"], q=q.strip(), status=status, page=page)
    return render(request, "subscriptions.html", conn, tenant, section="subscriptions", q=q, status=status,
                  statuses=subscriptions.STATUSES, **result)


@router.get("/t/{slug}/invoices", response_class=HTMLResponse)
def invoices_index(request: Request, slug: str, status: str = "", page: int = 1, conn=Depends(get_conn)):
    tenant = load_tenant(conn, slug)
    result = invoices.invoices_page(conn, tenant["id"], page=page, status=status)
    return render(request, "invoices.html", conn, tenant, section="invoices", status=status, **result)


@router.get("/t/{slug}/invoices/{number}", response_class=HTMLResponse)
def invoice_detail(request: Request, slug: str, number: str, conn=Depends(get_conn)):
    tenant = load_tenant(conn, slug)
    inv, lines = invoices.invoice_detail(conn, tenant["id"], number)
    if inv is None:
        raise HTTPException(404, "invoice not found")
    return render(request, "invoice_detail.html", conn, tenant, section="invoices", inv=inv, lines=lines)


@router.get("/t/{slug}/usage", response_class=HTMLResponse)
def usage_index(request: Request, slug: str, conn=Depends(get_conn)):
    tenant = load_tenant(conn, slug)
    days = settings.USAGE_WINDOW_DAYS
    return render(request, "usage.html", conn, tenant, section="usage", days=days,
                  meters=usage.meter_totals(conn, tenant["id"], days),
                  series=bars(usage.daily(conn, tenant["id"], days), "quantity"))
