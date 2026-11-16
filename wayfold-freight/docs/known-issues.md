# Known issues

Collected from support tickets and ops alerts. Symptoms only; nobody has had time to dig in.

| # | Reported | Symptom | Who |
|---|---|---|---|
| 1 | Oct | On-time % far below the carrier's own telematics numbers. West Coast terminals worst, a few East Coast terminals read high. Brookhollow numbers match their reports. | Ironvale |
| 2 | Oct | Depots page: the 7 / 30 / 90-day selector appears to do nothing. Dashboard "Depots needing attention" sometimes disagrees with the Depots page. | Ironvale |
| 3 | Oct | Nightly manifest (cron 07:30 UTC) rejected every night since go-live. Ops mail shows `manifest_rejected ... lines sum to X, subtotal says Y`, always off by a cent or two. | Ironvale |
| 4 | Oct | Tracking widget / route API slow (~0.5-1 s) for every shipment, including one-leg ones. Getting slower as volume grows. `logs/app.log` shows only 3 queries per call. | Ironvale |
| 5 | Sep | Drivers page has no search. | Brookhollow (cosmetic) |
| 6 | Aug | Seasonal depots count in the depot total. Product says this is intended. | - |
