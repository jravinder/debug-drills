# Escalation: Halvard Cloud

**From:** Ines Okafor, VP Finance, Halvard Cloud
**To:** Brookmeter support
**Priority:** P1 (enterprise SLA)

> We moved all 60,000 of our subscriptions onto Brookmeter last quarter. Month-end close is next week and I cannot sign off on anything coming out of it:
>
> 1. The **dashboard MRR** is several times what our own revenue model says, and ARR is in the billions. Our monthly invoicing on the same dashboard is a fraction of the MRR figure. A draft board deck nearly went out with your numbers.
> 2. Some of our customers received **two invoices for the same month**, a few cents apart. Support has been issuing credit notes by hand. Your ops team says the invoice run "had to be re-run" on those nights.
> 3. **Usage charges on invoices do not match the Usage page.** Take any API customer: invoiced quantity times our price never comes out to the amount on the invoice, and across the account we are consistently billing less than the Usage page says we should. Our auditors have flagged it.
> 4. The **nightly invoice run** for us takes far longer than anything else on the platform, and on heavy nights it is killed by the timeout and restarted.
>
> We are reviewing the contract at the end of the month.

**Internal note (account lead):** Pinecrest Labs reports none of this. Priority is the duplicate invoices and the usage amounts (money leaving or not reaching customers), then the dashboard figure, then run time. Please leave a short write-up of what you changed and why. Do not reseed or edit production data to make symptoms go away.
