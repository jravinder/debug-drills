-- 004: relay legs are looked up by the leg they continue (2026-09)
CREATE INDEX idx_legs_parent ON legs (parent_leg_id);
