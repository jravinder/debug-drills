import glob, json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import drill_config as cfg
import drill_log

D = drill_log.D
git = drill_log.git
has_git = os.path.isdir(os.path.join(ROOT, ".git"))

commits, diff = [], ""
if has_git:
    log = git("log", f"{cfg.START_TAG}..HEAD", "--reverse", "--format=%H%x1f%aI%x1f%B%x1e").stdout
    for rec in filter(None, (r.strip("\n") for r in log.split("\x1e"))):
        sha, at, msg = rec.split("\x1f", 2)
        files, added, deleted = [], 0, 0
        for line in git("show", "--numstat", "--format=", sha).stdout.splitlines():
            a, d, f = line.split("\t", 2)
            if f.startswith(".drill/"):
                continue
            files.append(f)
            added += int(a) if a.isdigit() else 0
            deleted += int(d) if d.isdigit() else 0
        msg = msg.strip()
        commits.append({"sha": sha, "at": at, "message": msg, "files": files, "added": added,
                        "deleted": deleted, "reverted": msg.startswith("Revert")})
    diff = git("diff", f"{cfg.START_TAG}..HEAD", "--", ".", ":!.drill").stdout

runs = []
for p in sorted(glob.glob(os.path.join(D, "runs", "*.json"))):
    try:
        with open(p) as f:
            runs.append(json.load(f))
    except Exception:
        pass

out = drill_log.scrub({"drill": cfg.NAME, "version": cfg.SCHEMA_VERSION, "created": drill_log.now(),
                       "events": drill_log.read_events(), "commits": commits, "runs": runs, "diff": diff})
os.makedirs(D, exist_ok=True)
with open(os.path.join(D, "submit.json"), "w") as f:
    json.dump(out, f, indent=1)
if has_git and commits:
    git("bundle", "create", os.path.join(D, "submit.bundle"), f"{cfg.START_TAG}..HEAD")
print(os.path.join(D, "submit.json"))
print("Upload .drill/submit.json on the practice page. Nothing was sent.")
