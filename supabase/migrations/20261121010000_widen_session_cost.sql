-- One Haiku call costs ~$0.00002, so numeric(10,4) rounded every addition to 0.
-- Keep 8 decimals so small per-call costs accumulate.
alter table public.sessions alter column cost_usd type numeric(14, 8);
