-- Local Supabase grants service_role everything on new tables by default; the hosted
-- project does not. That mismatch hid a missing-grant bug until production. Reset to
-- exactly what the agent and Grader need, so every environment behaves the same.

revoke all on public.profiles, public.sessions, public.transcript_turns from service_role;

grant select on public.profiles to service_role;
-- update: add_session_cost (runs as the caller) and, later, completing a Session.
grant select, update on public.sessions to service_role;
grant select, insert on public.transcript_turns to service_role;
