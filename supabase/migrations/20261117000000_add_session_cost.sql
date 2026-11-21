-- Atomically add cost to a Session. The agent and Grader call this with the
-- service role, so concurrent writers never overwrite each other's totals.
-- cost_breakdown maps a cost source (e.g. "llm") to the USD it has accrued.

create function public.add_session_cost(
  p_session_id uuid,
  p_usd numeric,
  p_breakdown jsonb default '{}'::jsonb
)
returns void
language sql
set search_path = ''
as $$
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
        select jsonb_object_keys(p_breakdown)
      ) keys
    )
  where s.id = p_session_id;
$$;

-- Service role only: a User must never write their own cost.
revoke all on function public.add_session_cost(uuid, numeric, jsonb) from public, anon, authenticated;
grant execute on function public.add_session_cost(uuid, numeric, jsonb) to service_role;
