"""Quick timing table against the running app. App-specific values live in scripts/drill_config.py."""
import json, os, statistics, subprocess, sys, time, urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, "scripts"))
import drill_config as cfg


def hit(path):
    t = time.time()
    try:
        with urllib.request.urlopen(cfg.BASE_URL + path, timeout=120) as r:
            r.read()
            code, q = r.status, r.headers.get("X-Query-Count", "-")
    except Exception as e:
        code, q = getattr(e, "code", "ERR"), "-"
    return (time.time() - t) * 1000, q, code


def main():
    rows = []
    for tenant in cfg.TENANTS:
        for name, path, n in cfg.BENCH_ENDPOINTS:
            res = [hit(path.format(tenant=tenant)) for _ in range(n)]
            ms = [r[0] for r in res]
            rows.append((name, tenant, f"{min(ms):.0f}/{statistics.median(ms):.0f}", res[-1][1], res[-1][2]))
        for name, argv in cfg.BENCH_JOBS:
            argv = [a.format(tenant=tenant, python=sys.executable) for a in argv]
            t = time.time()
            p = subprocess.run(argv, cwd=BASE, capture_output=True, text=True)
            rows.append((name, tenant, f"{(time.time()-t)*1000:.0f}", "-", "ok" if p.returncode == 0 else "FAILED"))
    try:
        import drill_log
        out = [{"endpoint": r[0], "tenant": r[1], "ms_median": float(r[2].split("/")[-1]),
                "queries": None if r[3] == "-" else int(r[3]), "ok": r[4] in ("200", "ok")} for r in rows]
        os.makedirs(os.path.join(BASE, ".drill"), exist_ok=True)
        with open(os.path.join(BASE, ".drill", "bench.json"), "w") as f:
            json.dump(out, f)
        drill_log.append_run("bench", {"rows": out})
    except Exception:
        pass
    print(f"{'endpoint':<14}{'tenant':<20}{'ms min/med':<12}{'queries':<9}status")
    for r in rows:
        print(f"{r[0]:<14}{r[1]:<20}{r[2]:<12}{r[3]:<9}{r[4]}")


if __name__ == "__main__":
    main()
