"""Server-rendered pages."""
import json

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse

import settings
from wayfold.db import get_conn
from wayfold.services import depots, metrics, shipments
from wayfold.templating import load_tenant, render

router = APIRouter()
WINDOWS = (7, 30, 90)


@router.get("/t/{slug}/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, slug: str, conn=Depends(get_conn)):
    tenant = load_tenant(conn, slug)
    days = settings.KPI_WINDOW_DAYS
    regions = metrics.stops_by_region(conn, tenant["id"], days)
    return render(request, "dashboard.html", conn, tenant, section="dashboard",
                  kpis=metrics.kpis(conn, tenant["id"], days), days=days,
                  chart_days=settings.CHART_WINDOW_DAYS,
                  regions_json=json.dumps(regions),
                  worst=depots.worst_depots(conn, tenant["id"], days),
                  late=metrics.recent_late(conn, tenant["id"]))


@router.get("/t/{slug}/depots", response_class=HTMLResponse)
def depots_index(request: Request, slug: str, region: str = "", days: int = 30, conn=Depends(get_conn)):
    tenant = load_tenant(conn, slug)
    days = days if days in WINDOWS else 30
    rows = depots.list_depots(conn, tenant["id"], days, region=region)
    deliveries = sum(r["deliveries"] for r in rows)
    on_time = sum(r["on_time"] for r in rows)
    return render(request, "depots.html", conn, tenant, section="depots", rows=rows, region=region, days=days,
                  windows=WINDOWS, regions=depots.regions(conn, tenant["id"]), deliveries=deliveries,
                  on_time_pct=round(on_time / deliveries * 100, 1) if deliveries else None)


@router.get("/t/{slug}/shipments", response_class=HTMLResponse)
def shipments_index(request: Request, slug: str, q: str = "", page: int = 1, conn=Depends(get_conn)):
    tenant = load_tenant(conn, slug)
    result = shipments.list_shipments(conn, tenant["id"], page, settings.SHIPMENTS_PER_PAGE, q=q.strip())
    return render(request, "shipments.html", conn, tenant, section="shipments", q=q, **result)


@router.get("/t/{slug}/shipments/{pro}", response_class=HTMLResponse)
def shipment_detail(request: Request, slug: str, pro: str, conn=Depends(get_conn)):
    tenant = load_tenant(conn, slug)
    s = shipments.get_shipment(conn, tenant["id"], pro)
    if s is None:
        raise HTTPException(404, "shipment not found")
    return render(request, "shipment_detail.html", conn, tenant, section="shipments", s=s,
                  legs=shipments.route(conn, tenant["id"], s["id"]), stops=shipments.stops(conn, s["id"]))


@router.get("/t/{slug}/drivers", response_class=HTMLResponse)
def drivers_index(request: Request, slug: str, page: int = 1, conn=Depends(get_conn)):
    tenant = load_tenant(conn, slug)
    since, _ = metrics.window(settings.KPI_WINDOW_DAYS)
    result = shipments.drivers_page(conn, tenant["id"], page, settings.DRIVERS_PER_PAGE, since)
    return render(request, "drivers.html", conn, tenant, section="drivers", days=settings.KPI_WINDOW_DAYS, **result)
