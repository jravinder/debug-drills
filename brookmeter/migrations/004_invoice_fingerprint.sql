-- 004: invoice fingerprints, so a re-run of the invoice job does not issue the same invoice twice (2025-02).
-- Invoices issued before this migration have no fingerprint.
ALTER TABLE invoices ADD COLUMN fingerprint TEXT;
CREATE UNIQUE INDEX idx_invoices_fingerprint ON invoices (tenant_id, fingerprint);
