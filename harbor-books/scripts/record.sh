#!/bin/bash
# Optional: for agents without hooks. Starts a subshell that logs each command you (or the agent) run.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RC="$(mktemp)"
cat > "$RC" <<RCEOF
[ -f ~/.bashrc ] && . ~/.bashrc
cd "$ROOT"
__drill_log() {
  local c; c="\$(HISTTIMEFORMAT= history 1 | sed 's/^ *[0-9]* *//')"
  [ -n "\$c" ] && [ "\$c" != "\$__drill_last" ] && __drill_last="\$c" && \
    DRILL_CMD="\$c" python3 "$ROOT/scripts/drill_log.py" shell <<< '{}' 2>/dev/null
}
PROMPT_COMMAND="__drill_log"
echo "Recording commands to .drill/session.jsonl. Type exit to stop."
RCEOF
bash --rcfile "$RC" -i
rm -f "$RC"
