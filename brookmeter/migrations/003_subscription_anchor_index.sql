-- 003: the invoice run selects subscriptions by anchor day (2024-03, "invoice run slow" ticket)
CREATE INDEX idx_subscriptions_anchor ON subscriptions (tenant_id, anchor_day);
CREATE INDEX idx_usage_subscription ON usage_records (subscription_id, recorded_at);
CREATE INDEX idx_invoices_subscription ON invoices (subscription_id, period_start);
