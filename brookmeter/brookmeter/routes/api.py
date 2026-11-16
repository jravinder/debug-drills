"""JSON endpoints."""
from fastapi import APIRouter, Depends, Query

import settings
from brookmeter.db import get_conn
from brookmeter.services import metrics, usage
from brookmeter.templating import load_tenant

router = APIRouter(prefix="/api")


@router.get("/t/{slug}/usage-daily")
def usage_daily(slug: str, days: int = Query(settings.USAGE_WINDOW_DAYS, ge=1, le=366), conn=Depends(get_conn)):
    tenant = load_tenant(conn, slug)
    return {"tenant": slug, "days": days, "series": usage.daily(conn, tenant["id"], days)}


@router.get("/t/{slug}/mrr")
def mrr(slug: str, conn=Depends(get_conn)):
    tenant = load_tenant(conn, slug)
    k = metrics.kpis(conn, tenant["id"], settings.KPI_WINDOW_DAYS)
    return {"tenant": slug, "mrr_cents": k["mrr_cents"], "arr_cents": k["arr_cents"],
            "by_plan": metrics.mrr_by_plan(conn, tenant["id"])}
