"""JSON endpoints: dashboard chart and the route feed used by the customer tracking widget."""
from fastapi import APIRouter, Depends, HTTPException

import settings
from wayfold.db import get_conn
from wayfold.services import metrics, shipments
from wayfold.templating import load_tenant

router = APIRouter(prefix="/api")


@router.get("/t/{slug}/on-time-series")
def on_time_series(slug: str, days: int = settings.CHART_WINDOW_DAYS, conn=Depends(get_conn)):
    tenant = load_tenant(conn, slug)
    days = max(1, min(days, 365))
    points = metrics.on_time_series(conn, tenant["id"], days)
    return {"tenant": slug, "days": days, "points": points}


@router.get("/t/{slug}/shipments/{pro}/route")
def shipment_route(slug: str, pro: str, conn=Depends(get_conn)):
    tenant = load_tenant(conn, slug)
    s = shipments.get_shipment(conn, tenant["id"], pro)
    if s is None:
        raise HTTPException(404, "shipment not found")
    return {"tenant": slug, "pro": pro, "status": s["status"], "legs": shipments.route(conn, tenant["id"], s["id"])}
