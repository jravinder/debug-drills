# Metrics

All reference bars are our estimate for a strong senior engineer on the Harbor Books kit. They are not measured on real users yet. We will replace them with measured values when we have data.

## Headline numbers

| Metric | Unit | Reference bar |
|---|---|---|
| Time to root cause | minutes from the first event to the first correct cause | 20 |
| Average prompt score | 0 to 5 | 4 |
| Pickup score | 0 to 100 | 80 |

## Speed

| Metric | Reference bar |
|---|---|
| First run of the app or bench | 5 min |
| Fault reproduced in numbers | 10 min |
| Root cause named | 20 min |
| One fault from first edit to proven fix | 10 min |
| Faults fixed per hour | 3 |

A gap of more than 8 minutes with no progress counts as a stuck stretch.

For each fault, the report gives the time when you named the cause, fixed it and proved the fix.

## Prompt score

Each prompt gets 0 to 5. The score is the average of five checks. Each check is pass or fail. Rules, not a model, do the scoring.

| Check | Passes when the prompt |
|---|---|
| Grounded | points to a real source: a file, a line, a log, the docs, bench output |
| Specific | states the outcome and the limits ("only", "do not", "until") |
| Evidence | asks for proof: numbers, timings, file and line, a diff |
| Scoped | asks for one thing, not "fix everything" |
| Checks | asks to verify the agent's last claim: re-run, prove, confirm |

The report also shows:

- the strongest and weakest prompt, with a rewrite of the weakest,
- wasted prompts: no progress after the prompt,
- unchecked claims: the agent claimed a result and nothing ran before your next prompt.

## Pickup score

Pickup measures how fast you learn an unfamiliar codebase.

| Part | Weight |
|---|---|
| Map check: three questions about the codebase, with answers and time | 40 |
| Targeted reads: 4 or fewer files read before the first correct cause | 25 |
| First cause you state is correct | 20 |
| Few re-reads of the same file | 15 |

## Fix quality

- Lines and files changed. A large change for a small fault counts as sprawling.
- Reverted commits count as wrong turns.

## Limits

- Rule-based scoring can miss a good prompt that uses unusual words.
- Without timestamps (pasted prompts only), the report cannot measure speed.
