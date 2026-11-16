# Wayfold

Back office for regional freight carriers: shipments, stops, drivers, depots, an on-time delivery dashboard and the nightly line-haul manifest. Multi-tenant; each carrier is an account.

> **Fictional.** Wayfold, its customers and everyone named here are made up for a debugging exercise.

## The story so far

Wayfold started in 2022 for one three-depot carrier in the Cascades. It grew by word of mouth to a few dozen regional carriers, all running out of a single time zone. The original developer built it quickly and well enough, then moved on in the summer. You have inherited it.

Last quarter we signed our first enterprise account, **Ironvale Freight Lines** (120 depots across four time zones, relay routes through regional hubs, roughly 500k stop events a year). Their data was migrated six weeks ago. Since then the support inbox has not been quiet. Read `BRIEFING.md` first.

Our oldest customer, **Brookhollow Cartage** (3 depots), says everything is fine.

## Open in your agent of choice

You lead; the agent types. Any of these work:

- Claude Code: `cd wayfold-freight && claude`
- Codex: `codex` in this folder
- Cursor / Windsurf / VS Code + Copilot: open the folder, use agent mode

`AGENTS.md` / `CLAUDE.md` hold the commands an agent needs.

## Quickstart

Requires Python 3.12+ and `make`.

```
make up        # creates .venv, installs pinned deps, seeds wayfold.db (~10 s), serves :8775
```

Open http://127.0.0.1:8775/ and use the account switcher top right.

In a second terminal:

```
make bench     # timings per tenant against the running app
make test      # pytest
```

Docker instead: `docker compose up` (serves on 8775).

## Layout

| Path | What |
|---|---|
| `wayfold/app.py` | FastAPI app, request logging, `X-Query-Count` header |
| `wayfold/routes/` | `pages.py` (server-rendered), `api.py` (chart + tracking JSON) |
| `wayfold/services/` | queries: metrics, depots, shipments |
| `wayfold/templates/`, `wayfold/static/` | Jinja2 templates, CSS, chart script (Chart.js 4.4.1 from cdnjs) |
| `jobs/manifest_export.py` | nightly line-haul manifest per tenant, see `deploy/crontab` |
| `migrations/` | numbered `.sql` files + `migrate.py` runner |
| `seed.py` | deterministic demo data (Faker, fixed seed) |
| `settings.py` | config, overridable with `WAYFOLD_*` env vars |
| `docs/` | `ARCHITECTURE.md`, `known-issues.md` |
| `logs/app.log` | key=value logs with ms timings and query counts |

## Working on the drill

Recording is local, in `.drill/`, only inside this folder. Nothing is sent anywhere. Claude Code hooks (`.claude/settings.json`) log your prompts, tool calls and replies; `make bench` and `make test` log their results. For other agents, `make record` starts a bash subshell that logs each command run in it.

`make up` creates a local git repo tagged `drill-start`. Claude Code hooks commit a checkpoint after each reply (`make checkpoint` does the same for other agents); a pre-commit hook refuses anything that looks like a secret. Nothing is ever pushed.

`make submit` (alias `make report`) writes `.drill/submit.json`, which YOU choose whether to upload on the practice page. Secrets and absolute home paths are removed from it. `make reset` returns to the starting state.
