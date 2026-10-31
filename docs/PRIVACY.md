# Privacy

## What stays on your machine

- The app makes no network calls. `make up` downloads pinned Python packages from PyPI one time. The browser loads Chart.js from cdnjs.
- The session record is in `.drill/` and in the kit's local git history.
- The kit never pushes the local git repository. It has no remote.

## What `make submit` removes

- Values that look like secrets: API keys, tokens, `KEY=`, `SECRET=`, `TOKEN=` assignments, bearer tokens.
- Absolute paths in your home folder.

A local pre-commit hook also refuses a checkpoint that adds a value that looks like a secret.

## What you share

You choose if you share `submit.json`. The companion report reads the file in your browser. It does not upload the file to a server.

## Your agent

Your agent (Claude Code, Codex, Cursor) sends your code and prompts to its own provider. That is the agent's normal behavior, not the kit's. The kit code and data are fictional, so the kit adds no sensitive data to those requests.
