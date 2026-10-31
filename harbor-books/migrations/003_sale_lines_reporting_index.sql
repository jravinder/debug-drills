-- 003: reporting queries filter by tenant and date range (2024-01, "dashboard is slow" ticket)
CREATE INDEX idx_sale_lines_tenant_sold ON sale_lines (tenant_id, sold_at);
