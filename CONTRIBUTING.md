# Contributing

## Add a kit

1. Copy `harbor-books/` to a new folder.
2. Replace the product: domain, tables, pages, seed data. Keep the drill files: `Makefile`, `scripts/`, `.claude/settings.json`, `AGENTS.md`, `CLAUDE.md`, `bench.py`.
3. Edit `scripts/drill_config.py` for the new app: start command, seed command, port, tenants.
4. Plant 4 faults. Each fault must:
   - have a realistic cause,
   - show for the large tenant only,
   - show in `make bench` or `make test`,
   - have a minimal fix of less than about 30 lines.
5. Write `BRIEFING.md` as a customer escalation that lists symptoms only.
6. Write a private answer key. Do not commit it.
7. Run the kit from a fresh clone: `make up`, `make bench`, `make test`, `make submit`, `make reset`.

## Rules

- Fictional companies, people and data only. No real customer, employer or client names.
- No comments, TODOs or file names that point to a planted fault.
- No answer key in the repository.
- Pin all dependency versions.

## Pull requests

Open a pull request with the kit, a screenshot of the app, and the bench output before and after your reference fix.
