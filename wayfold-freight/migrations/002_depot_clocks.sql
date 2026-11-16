-- 002: depots record their own UTC offset so carriers can span time zones (2026-08)
ALTER TABLE depots ADD COLUMN utc_offset_min INTEGER NOT NULL DEFAULT -480;
