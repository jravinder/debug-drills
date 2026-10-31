# Why

## The problem

AI coding agents write most of the code in many teams now. The engineer's job changes. The engineer must:

- give the agent the correct context,
- set limits on what the agent changes,
- check each claim the agent makes,
- learn an unfamiliar codebase fast enough to know when the agent is wrong.

Interviews and training still test the old job. A take-home test or a whiteboard algorithm does not show if a person can lead an agent through a real fault in a real codebase.

## What a drill gives

A drill is a small product with real faults. You lead an agent to find and fix them. The kit records what you did. The record gives numbers that you can compare between attempts.

## Design principles

1. **Realistic, not a puzzle.** Each kit is a working product with docs, tests, history and some technical debt. The faults come from a real cause, such as a new customer with more data or a new data feed.
2. **Symptoms, not hints.** The briefing tells you what the customer sees. It does not tell you where the fault is. The code has no comments that point to a fault.
3. **One small customer works.** A small customer sees no problem. You must find what is different about the large customer.
4. **Proof is required.** A fix counts when a bench or a test shows it. The agent's statement that "it is fixed" does not count.
5. **Any agent.** Claude Code, Cursor and Codex all work. The kit does not depend on one vendor.
6. **Local and private.** The kit runs on your machine and sends nothing. You decide what to share.
7. **Measured, with honest bars.** Each metric has a reference bar. We state that the bars are estimates until real data replaces them.
8. **A ceiling exists.** Each kit has a better design than the minimum fix. The answer key names it, so a fast result is compared with the best result, not only with the starting point.
9. **Fictional data only.** No real company, customer or person is in any kit.
