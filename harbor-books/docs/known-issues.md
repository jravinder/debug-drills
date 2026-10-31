# Known issues

Collected from support tickets and ops alerts. Symptoms only; nobody has had time to dig in.

| # | Reported | Symptom | Who |
|---|---|---|---|
| 1 | Oct | Dashboard load time grows with account size. Lanternfield 4-5 s, Tidewater instant. `logs/app.log` shows a very high `queries=` count on the dashboard request. | Lanternfield |
| 2 | Oct | Stores table: sorting by Revenue shows a different leader on each page. Some stores never appear when paging through. | Lanternfield |
| 3 | Oct | Nightly reorder export (cron 02:20) fails for Lanternfield since the supplier feed v2 import. Ops mail shows a traceback. Run takes a few seconds and memory climbs before it dies. | Lanternfield |
| 4 | Oct | Dashboard revenue chart slow to appear; browser memory high on that page; slow on store Wi-Fi. | Lanternfield |
| 5 | Sep | Sales page filter only lists store codes, not names. | Tidewater (cosmetic) |
| 6 | Aug | Renovating stores are still counted in the Stores total. Product says this is intended. | - |
