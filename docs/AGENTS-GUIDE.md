# Leading an agent in a drill

## Start

- Claude Code: `cd harbor-books && claude`. Hooks record the session.
- Codex or another terminal agent: run `make record` first, then start the agent in that subshell.
- Cursor, Windsurf, VS Code agent mode: open the kit folder. Run `make checkpoint` after each step you want recorded.

`AGENTS.md` and `CLAUDE.md` in each kit give the agent the run, test and bench commands. They give no hints.

## Method

1. **Reproduce first.** Run `make bench` before any change. Write down the numbers for the large and the small tenant.
2. **Ground the agent.** Tell it which docs and logs to read. Ask it to explain the code path for one symptom, with file and line.
3. **State a cause before a fix.** Ask: what is different for the large tenant? A cause names a mechanism, not a location.
4. **One fault at a time.** Fix one fault. Prove it. Commit. Then go to the next.
5. **Prove each fix.** Re-run the bench or the test. Compare with the numbers from step 1.
6. **Check every claim.** When the agent says "fixed" or "faster", ask for the output that shows it.
7. **Keep fixes small.** Change only what the fault needs. Do not reseed or edit data to hide a symptom.
8. **Name the ceiling.** After the fixes, state the best possible design and how far your fix is from it.

## Prompt examples

Weak:

> Fix the performance issues.

Strong:

> Read BRIEFING.md and docs/ARCHITECTURE.md. For the first symptom, show the request path with file and line. Do not change code yet.

Strong:

> Re-run make bench. Show the dashboard time and query count for both tenants, before and after.
