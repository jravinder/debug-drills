-- 002: supplier feed v2 sends case pack sizes so reorders can be rounded to full cases (2023-06)
ALTER TABLE titles ADD COLUMN case_pack INTEGER NOT NULL DEFAULT 1;
