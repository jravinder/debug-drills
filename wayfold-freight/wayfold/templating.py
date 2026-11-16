"""Jinja2 environment, filters and the tenant lookup shared by the routes."""
import os

from fastapi.templating import Jinja2Templates

from wayfold import db

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))


class TenantNotFound(Exception):
    def __init__(self, slug):
        self.slug = slug


def pct(v):
    return "-" if v is None else f"{v:.1f}%"


def clock(offset_min):
    h, m = divmod(abs(offset_min), 60)
    return f"UTC{'-' if offset_min < 0 else '+'}{h}" + (f":{m:02d}" if m else "")


def num(n):
    return "-" if n is None else f"{n:,}"


templates.env.filters["pct"] = pct
templates.env.filters["clock"] = clock
templates.env.filters["num"] = num


def load_tenant(conn, slug):
    t = db.tenant_by_slug(conn, slug)
    if t is None:
        raise TenantNotFound(slug)
    return t


def render(request, name, conn, tenant, **ctx):
    ctx.update(tenant=tenant, tenants=db.all_tenants(conn), section=ctx.get("section", ""))
    return templates.TemplateResponse(request, name, ctx)
