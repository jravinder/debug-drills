# Known issues

Collected from support tickets and ops alerts. Symptoms only; nobody has had time to dig in.

| # | Reported | Symptom | Who |
|---|---|---|---|
| 1 | Oct | Dashboard MRR and ARR look far too high next to "Invoiced by month". Finance says the gap appeared when the Halvard migration landed. | Halvard |
| 2 | Oct | Duplicate invoices for the same subscription and period, totals a few cents apart. Always on nights the invoice run was restarted by ops. | Halvard |
| 3 | Oct | Usage line amount on invoices is not quantity x unit price; account-wide usage billing runs below the Usage page's "Charges" column. | Halvard |
| 4 | Oct | Invoice run for Halvard takes many seconds locally and hits the 900 s cron timeout in production on heavy anchor days. `logs/app.log` shows `due=` and `usage_records=` per run. | Halvard |
| 5 | Sep | Usage page is in UTC; some customers expect their local day boundaries. Product says UTC is intended. | Pinecrest |
| 6 | Aug | Subscriptions that start on the 29th-31st are anchored on an earlier day (anchors are 1-28 by design). Nothing is invoiced on the 29th-31st. | - |
| 7 | Jul | Trialing subscriptions are not counted in "Live subscriptions". Intended. | - |
