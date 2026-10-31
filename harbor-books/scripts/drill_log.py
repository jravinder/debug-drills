"""Session log + git checkpoints for the drill. Local only; nothing is sent anywhere.

Hook usage: python3 scripts/drill_log.py <prompt|tool|stop|checkpoint|once ...>
Hook JSON is read from stdin. Never fails: errors are swallowed, exit code is always 0.
"""
import datetime, json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, ".drill")
LOG = os.path.join(D, "session.jsonl")
HOME = os.path.expanduser("~")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drill_config as cfg

PATTERNS = [
    (re.compile(r"(?i)\b([A-Z0-9_]*(?:KEY|TOKEN|SECRET|PASSWORD|PASSWD)[A-Z0-9_]*)\s*[=:]\s*\S+"), r"\1=[removed]"),
    (re.compile(r"sk-[A-Za-z0-9_\-]{10,}"), "[removed]"),
    (re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"), "[removed]"),
    (re.compile(r"(?i)Bearer\s+[A-Za-z0-9._\-]+"), "Bearer [removed]"),
    (re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"), "[removed]"),
]


def scrub(x):
    if isinstance(x, str):
        for rx, rep in PATTERNS:
            x = rx.sub(rep, x)
        x = x.replace(HOME, "~")
        return re.sub(r"/(?:Users|home)/[^/\s]+", "/~user", x)
    if isinstance(x, list):
        return [scrub(i) for i in x]
    if isinstance(x, dict):
        return {k: scrub(v) for k, v in x.items()}
    return x


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def read_events():
    out = []
    try:
        with open(LOG) as f:
            for line in f:
                try:
                    out.append(json.loads(line))
                except ValueError:
                    pass
    except OSError:
        pass
    return out


def append(event):
    os.makedirs(D, exist_ok=True)
    event = scrub({"t": now(), **event})
    with open(LOG, "a") as f:
        f.write(json.dumps(event) + "\n")


def append_once(event):
    for e in read_events():
        if e.get("tool") == event.get("tool") and e.get("command") == event.get("command"):
            return
    append(event)


def append_run(kind, payload):
    """Record a bench/test run as a session event and as .drill/runs/<ts>-<kind>.json."""
    ev = {"kind": kind, **payload}
    append(ev)
    os.makedirs(os.path.join(D, "runs"), exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    with open(os.path.join(D, "runs", f"{stamp}-{kind}.json"), "w") as f:
        json.dump(scrub({"at": now(), **ev}), f)


def git(*args):
    return subprocess.run(["git", "-c", "user.name=drill", "-c", "user.email=drill@example.com", *args],
                          cwd=ROOT, capture_output=True, text=True)


def checkpoint():
    if not os.path.isdir(os.path.join(ROOT, ".git")):
        return
    if not git("status", "--porcelain").stdout.strip():
        return
    prompts = [e.get("text", "") for e in read_events() if e.get("kind") == "prompt"]
    last = prompts[-1] if prompts else ""
    subject = "checkpoint: " + (" ".join(last.split())[:72] or "(no prompt)")
    git("add", "-A")
    git("commit", "-q", "-m", subject, "-m", f"prompt: {last}\nat: {now()}")


def rel(path):
    p = os.path.realpath(path if os.path.isabs(path) else os.path.join(ROOT, path))
    root = os.path.realpath(ROOT)
    if p == root or p.startswith(root + os.sep):
        return os.path.relpath(p, root)
    return None


def last_assistant_text(transcript):
    last = None
    with open(transcript) as f:
        for line in f:
            try:
                o = json.loads(line)
            except ValueError:
                continue
            msg = o.get("message") or {}
            if o.get("type") != "assistant" and msg.get("role") != "assistant":
                continue
            c = msg.get("content")
            if isinstance(c, str):
                text = c
            else:
                text = "\n".join(b.get("text", "") for b in c or [] if isinstance(b, dict) and b.get("type") == "text")
            if text.strip():
                last = text
    return last


def handle(event, data):
    if event == "prompt":
        append({"kind": "prompt", "text": str(data.get("prompt", ""))})
    elif event == "tool":
        ti = data.get("tool_input") or {}
        ev = {"kind": "tool", "tool": data.get("tool_name", "")}
        if ti.get("command"):
            ev["command"] = str(ti["command"])
        fp = ti.get("file_path") or ti.get("path")
        if fp:
            r = rel(str(fp))
            if r is None:
                return
            ev["file"] = r
        tr = data.get("tool_response")
        if isinstance(tr, dict):
            code = tr.get("exit_code", tr.get("exitCode"))
            if isinstance(code, int):
                ev["exit"] = code
        append(ev)
    elif event == "shell":
        append({"kind": "tool", "tool": "shell", "command": os.environ.get("DRILL_CMD", "")})
    elif event == "stop":
        try:
            text = last_assistant_text(data.get("transcript_path", ""))
            if text:
                append({"kind": "assistant", "text": text[:2000]})
        finally:
            checkpoint()
    elif event == "checkpoint":
        checkpoint()


if __name__ == "__main__":
    try:
        ev = sys.argv[1]
        if ev == "once":
            append_once({"kind": "tool", "tool": sys.argv[2], "command": sys.argv[3]})
        else:
            data = {}
            if ev in ("prompt", "tool", "stop"):
                data = json.load(sys.stdin)
            handle(ev, data)
    except BaseException:
        pass
    sys.exit(0)
