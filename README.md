# debug-drills

Practice kits for one skill: lead an AI coding agent through an unfamiliar codebase, find the real faults, fix them, and prove each fix.

## Who it is for

- Engineers who use Claude Code, Cursor or Codex and want to measure how well they lead the agent.
- Engineers who prepare for a hands-on interview where they debug with an agent while someone watches.
- Teams who want a shared exercise with numbers, not opinions.

## Quickstart (5 minutes)

Requires Python 3.12+, `make` and git.

```sh
git clone https://github.com/jravinder/debug-drills.git
cd debug-drills/harbor-books
make up            # installs dependencies, seeds data (~15 s), serves http://127.0.0.1:8765
```

1. Read `BRIEFING.md`. It is the customer escalation.
2. Open the folder in your agent (`claude`, `codex`, or Cursor agent mode).
3. Run `make bench` in a second terminal to see the problem in numbers.
4. Find, fix and verify. Use `make bench` and `make test` to prove each fix.
5. Run `make submit`. It writes `.drill/submit.json`, your session record.

`make reset` returns the kit to the starting state.

## Kits

| Kit | Domain | Stack | Faults | Status |
|---|---|---|---|---|
| [harbor-books](harbor-books/) | Back office for bookstore chains: sales, stores, nightly reorder file | FastAPI, SQLite, Jinja2 | 4 | Available |
| [wayfold-freight](wayfold-freight/) | Freight carrier back office: shipments, depots, on-time delivery, driver manifests | FastAPI, SQLite, Jinja2 | 4 | Available |
| [brookmeter](brookmeter/) | Subscription billing: plans, metered usage, invoices, MRR (monthly recurring revenue) | FastAPI, SQLite, Jinja2 | 4 | Available |

All companies, people and data in the kits are fictional.

## How it works

Each kit is a small, working product with a history. A large customer arrived and the product stopped working for that customer only. A small customer still sees no problem.

You lead. The agent types. The kit records the session on your machine, in the kit's own git history and in `.drill/`. Details: [docs/HOW-IT-WORKS.md](docs/HOW-IT-WORKS.md).

## Metrics

The session record gives three headline numbers:

- Time to root cause, in minutes.
- Average prompt score, 0 to 5.
- Pickup score, 0 to 100: how fast you learn an unfamiliar codebase.

Each number has a reference bar. The bars are our estimate for a strong senior engineer. They are not yet measured on real users. Details: [docs/METRICS.md](docs/METRICS.md).

## Privacy

The app sends nothing over the network. The session record stays in the kit folder. You decide if you share `submit.json`. `make submit` removes secrets and home paths from it. Details: [docs/PRIVACY.md](docs/PRIVACY.md).

## More

- [WHY.md](WHY.md): why these kits exist and the design principles.
- [docs/AGENTS-GUIDE.md](docs/AGENTS-GUIDE.md): how to lead an agent in a drill.
- [CONTRIBUTING.md](CONTRIBUTING.md): how to build a new kit.
- [CHANGELOG.md](CHANGELOG.md)

A companion page that reads `submit.json` in your browser and shows the report is in progress.

## License

MIT. See [LICENSE](LICENSE).

Built by Ravinder Jilkapally, [aisoft.us](https://aisoft.us).
