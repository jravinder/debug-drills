# Brookmeter

Billing back office for software companies that bill their own customers: plans, subscriptions, metered usage, invoices, an MRR dashboard and the nightly invoice run. Multi-tenant; each software company is an account.

> **Fictional.** Brookmeter, its customers and everyone named here are made up for a debugging exercise.

## The story so far

Brookmeter started in 2022 billing a handful of small SaaS teams. The original developer built it quickly and carefully enough, then moved on in the summer. You have inherited it.

Last quarter we signed our first enterprise account, **Halvard Cloud** (~60k subscriptions, about a million usage events a month, many annual contracts). Their data was migrated in a few weeks ago. Since then the support inbox has not been quiet. Read `BRIEFING.md` first.

Our oldest customer, **Pinecrest Labs** (~200 subscriptions), says everything is fine.

## Open in your agent of choice

You lead; the agent types. Any of these work:

- Claude Code: `cd brookmeter && claude`
- Codex: `codex` in this folder
- Cursor / Windsurf / VS Code + Copilot: open the folder, use agent mode

`AGENTS.md` / `CLAUDE.md` hold the commands an agent needs.

## Quickstart

Requires Python 3.12+ and `make`.

```
make up        # creates .venv, installs pinned deps, seeds brookmeter.db (~20 s), serves :8767
```

Open http://127.0.0.1:8767/ and use the account switcher top right.

In a second terminal:

```
make bench     # timings per tenant against the running app, plus one invoice run each
make test      # pytest
```

The invoice run bills subscriptions anchored on today's day of the month; on the 29th-31st nothing is due, so pass `--date` to run a specific day.

Docker instead: `docker compose up` (serves on 8767).

## Layout

| Path | What |
|---|---|
| `brookmeter/app.py` | FastAPI app, request logging, `X-Query-Count` header |
| `brookmeter/routes/` | `pages.py` (server-rendered), `api.py` (JSON) |
| `brookmeter/services/` | metrics (MRR), subscriptions, invoices, usage, rating, invoicing |
| `brookmeter/templates/`, `brookmeter/static/` | Jinja2 templates, CSS |
| `jobs/invoice_run.py` | nightly invoice run per tenant, see `deploy/crontab` |
| `migrations/` | numbered `.sql` files + `migrate.py` runner |
| `seed.py` | deterministic demo data (Faker, fixed seed) |
| `settings.py` | config, overridable with `BROOK_*` env vars |
| `docs/` | `ARCHITECTURE.md`, `known-issues.md` |
| `logs/app.log` | key=value logs with ms timings and query counts |

## Working on the drill

Recording is local, in `.drill/`, only inside this folder. Nothing is sent anywhere. Claude Code hooks (`.claude/settings.json`) log your prompts, tool calls and replies; `make bench` and `make test` log their results. For other agents, `make record` starts a bash subshell that logs each command run in it.

`make up` creates a local git repo tagged `drill-start`. Claude Code hooks commit a checkpoint after each reply (`make checkpoint` does the same for other agents); a pre-commit hook refuses anything that looks like a secret. Nothing is ever pushed.

`make submit` (alias `make report`) writes `.drill/submit.json`, which YOU choose whether to upload on the practice page. Secrets and absolute home paths are removed from it. `make reset` returns to the starting state.
