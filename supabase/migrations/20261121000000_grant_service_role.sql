-- The agent and Grader connect as service_role. It bypasses RLS but still needs
-- table privileges, and this project does not grant them to new tables by default.
-- Grant only what is used today; later issues (e.g. the Grader) add what they need.
-- Users keep their narrow grants from the starter schema (see ADR 0009).

grant select, insert on public.transcript_turns to service_role;
-- update: add_session_cost (runs as the caller) and, later, completing a Session.
grant select, update on public.sessions to service_role;
grant select on public.profiles to service_role;
