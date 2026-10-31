"""JSON endpoints used by the dashboard charts."""
from fastapi import APIRouter, Depends

import settings
from harbor.db import get_conn
from harbor.services import sales
from harbor.templating import load_tenant

router = APIRouter(prefix="/api")


@router.get("/t/{slug}/revenue-series")
def revenue_series(slug: str, days: int = settings.CHART_WINDOW_DAYS, conn=Depends(get_conn)):
    tenant = load_tenant(conn, slug)
    # The chart can be filtered by store/category in the browser, so ship line-level rows.
    # TODO: add a store picker server-side and drop the client-side filtering.
    lines = sales.revenue_lines(conn, tenant["id"], days)
    return {"tenant": slug, "days": days, "count": len(lines), "lines": lines}
