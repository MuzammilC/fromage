-- add_session_cost used to do nothing for an unknown Session and to produce NULL
-- for a null amount. Fail loudly instead. CREATE OR REPLACE keeps the existing grants.

create or replace function public.add_session_cost(
  p_session_id uuid,
  p_usd numeric,
  p_breakdown jsonb default '{}'::jsonb
)
returns void
language plpgsql
set search_path = ''
as $$
begin
  if p_usd is null or p_usd < 0 then
    raise exception 'Cost must be a non-negative amount' using errcode = '22004';
  end if;

  update public.sessions s
  set
    cost_usd = s.cost_usd + p_usd,
    cost_breakdown = (
      select coalesce(jsonb_object_agg(
        k,
        coalesce((s.cost_breakdown ->> k)::numeric, 0) + coalesce((p_breakdown ->> k)::numeric, 0)
      ), '{}'::jsonb)
      from (
        select jsonb_object_keys(s.cost_breakdown) as k
        union
        select jsonb_object_keys(coalesce(p_breakdown, '{}'::jsonb))
      ) keys
    )
  where s.id = p_session_id;

  if not found then
    raise exception 'Session % not found', p_session_id using errcode = 'P0002';
  end if;
end;
$$;
