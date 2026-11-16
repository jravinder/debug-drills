"""Jinja2 environment, filters and the tenant lookup shared by the routes."""
import os

from fastapi.templating import Jinja2Templates

from brookmeter import db

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))


class TenantNotFound(Exception):
    def __init__(self, slug):
        self.slug = slug


def money(cents, decimals=False):
    if cents is None:
        return "-"
    v = cents / 100
    return f"${v:,.2f}" if decimals else f"${v:,.0f}"


def num(n):
    return "-" if n is None else f"{n:,}"


def compact(cents):
    v = (cents or 0) / 100
    for div, suffix in ((1e6, "M"), (1e3, "k")):
        if abs(v) >= div:
            return f"${v / div:.1f}{suffix}"
    return f"${v:,.0f}"


templates.env.filters["money"] = money
templates.env.filters["num"] = num
templates.env.filters["compact"] = compact


def load_tenant(conn, slug):
    t = db.tenant_by_slug(conn, slug)
    if t is None:
        raise TenantNotFound(slug)
    return t


def render(request, name, conn, tenant, **ctx):
    ctx.update(tenant=tenant, tenants=db.all_tenants(conn), section=ctx.get("section", ""))
    return templates.TemplateResponse(request, name, ctx)
