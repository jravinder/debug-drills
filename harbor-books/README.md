# Harbor Books

Back office for independent bookstore chains: sales, stores, stock and the nightly reorder file buyers send to suppliers. Multi-tenant; each chain is an account.

> **Fictional.** Harbor Books, its customers and everyone named here are made up for a debugging exercise.

## The story so far

Harbor Books started in 2021 as a side project for one six-shop chain on the coast. It grew by word of mouth to a few dozen independents. The original developer built it fast and well enough, then left in the spring. You have inherited it.

Last quarter we signed our first enterprise account, **Lanternfield Booksellers** (140 stores, ~40k titles). Their data was migrated in two weeks ago. Since then the support inbox has not been quiet. Read `BRIEFING.md` first.

Our oldest customer, **Tidewater Books** (3 stores), says everything is fine.

## Open in your agent of choice

You lead; the agent types. Any of these work:

- Claude Code: `cd harbor-books && claude`
- Codex: `codex` in this folder
- Cursor / Windsurf / VS Code + Copilot: open the folder, use agent mode

`AGENTS.md` / `CLAUDE.md` hold the commands an agent needs.

## Quickstart

Requires Python 3.12+ and `make`.

```
make up        # creates .venv, installs pinned deps, seeds harbor.db (~15 s), serves :8765
```

Open http://127.0.0.1:8765/ and use the account switcher top right.

In a second terminal:

```
make bench     # timings per tenant against the running app
make test      # pytest
```

Docker instead: `docker compose up` (serves on 8765).

## Layout

| Path | What |
|---|---|
| `harbor/app.py` | FastAPI app, request logging, `X-Query-Count` header |
| `harbor/routes/` | `pages.py` (server-rendered), `api.py` (chart JSON) |
| `harbor/services/` | queries: metrics, stores, sales |
| `harbor/templates/`, `harbor/static/` | Jinja2 templates, CSS, chart scripts (Chart.js 4.4.1 from cdnjs) |
| `jobs/reorder_export.py` | nightly reorder CSV per tenant, see `deploy/crontab` |
| `migrations/` | numbered `.sql` files + `migrate.py` runner |
| `seed.py` | deterministic demo data (Faker, fixed seed) |
| `settings.py` | config, overridable with `HARBOR_*` env vars |
| `docs/` | `ARCHITECTURE.md`, `known-issues.md` |
| `logs/app.log` | key=value logs with ms timings and query counts |

## Working on the drill

Recording is local, in `.drill/`, only inside this folder. Nothing is sent anywhere. Claude Code hooks (`.claude/settings.json`) log your prompts, tool calls and replies; `make bench` and `make test` log their results. For other agents, `make record` starts a bash subshell that logs each command run in it.

`make up` creates a local git repo tagged `drill-start`. Claude Code hooks commit a checkpoint after each reply (`make checkpoint` does the same for other agents); a pre-commit hook refuses anything that looks like a secret. Nothing is ever pushed.

`make submit` (alias `make report`) writes `.drill/submit.json`, which YOU choose whether to upload on the practice page. Secrets and absolute home paths are removed from it. `make reset` returns to the starting state.
