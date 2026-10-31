#!/bin/sh
# Initialise a local repo in the kit folder: baseline commit, drill-start tag, secret-refusing pre-commit hook.
set -e
cd "$(dirname "$0")/.."
[ -d .git ] && exit 0
git init -q
git add -A
git -c user.name=drill -c user.email=drill@example.com commit -q -m "drill start"
git tag "$(python3 scripts/drill_config.py start_tag)"
cat > .git/hooks/pre-commit <<'HOOK'
#!/bin/sh
# Local only: refuse commits that add secrets.
if git diff --cached -U0 | grep -E '^\+' | grep -v '^+++' | grep -v '\[removed\]' | \
   grep -E 'sk-[A-Za-z0-9_-]{10,}|gh[pousr]_[A-Za-z0-9]{20,}|AKIA[A-Z0-9]{16}|Bearer +[A-Za-z0-9._-]{8,}|[A-Z0-9_]*(KEY|SECRET|TOKEN)[A-Z0-9_]*=[^[:space:]]+' >/dev/null; then
  echo "pre-commit: refusing to commit what looks like a secret." >&2
  exit 1
fi
HOOK
chmod +x .git/hooks/pre-commit
echo "initialised git repo, tagged drill-start"
