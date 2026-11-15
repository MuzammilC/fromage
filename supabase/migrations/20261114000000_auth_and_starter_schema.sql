-- Starter schema: profiles, sessions, transcript_turns, with row-level security.
-- Vocabulary follows CONTEXT.md: a User is the account, a Session is one sitting.

create type public.session_mode as enum ('mock', 'practice');
create type public.session_medium as enum ('text', 'voice');
create type public.session_status as enum ('in_progress', 'completed', 'abandoned');
create type public.turn_speaker as enum ('examiner', 'candidate');

-- profiles: 1:1 with auth.users -------------------------------------------------

create table public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  display_name text,
  created_at timestamptz not null default now()
);

alter table public.profiles enable row level security;

create function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  insert into public.profiles (id) values (new.id);
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- sessions ---------------------------------------------------------------------

create table public.sessions (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references public.profiles (id) on delete cascade,
  -- Exam Definition reference, `id@version`, e.g. delf-a2@1 (see ADR 0002).
  exam_definition_ref text not null
    check (exam_definition_ref ~ '^[a-z0-9]+(-[a-z0-9]+)*@[1-9][0-9]*$'),
  mode public.session_mode not null,
  medium public.session_medium not null,
  status public.session_status not null default 'in_progress',
  -- Cost fields are written by the agent and Grader (service role), never by the User.
  cost_usd numeric(10, 4) not null default 0 check (cost_usd >= 0),
  cost_breakdown jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  ended_at timestamptz,
  -- A Session has ended exactly when it has left in_progress.
  check ((status = 'in_progress') = (ended_at is null))
);

create index sessions_owner_id_created_at_idx
  on public.sessions (owner_id, created_at desc);

alter table public.sessions enable row level security;

-- Status moves one way: in_progress -> completed | abandoned, and then stays put.
-- A User may abandon their own Session. Completing it (which hands it to the
-- Grader) is for the service role. ended_at is set here, never by the caller.
create function public.enforce_session_status_transition()
returns trigger
language plpgsql
as $$
begin
  if new.status is distinct from old.status then
    if old.status <> 'in_progress' then
      raise exception 'Session status % is final', old.status
        using errcode = 'check_violation';
    end if;
    if new.status = 'completed' and current_user in ('anon', 'authenticated') then
      raise exception 'Only the service role can complete a Session'
        using errcode = 'insufficient_privilege';
    end if;
    new.ended_at := now();
  end if;
  return new;
end;
$$;

create trigger sessions_enforce_status_transition
  before update of status on public.sessions
  for each row execute function public.enforce_session_status_transition();

-- transcript_turns -------------------------------------------------------------

create table public.transcript_turns (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null references public.sessions (id) on delete cascade,
  seq integer not null check (seq >= 0),
  speaker public.turn_speaker not null,
  text text not null,
  started_at timestamptz not null,
  ended_at timestamptz,
  unique (session_id, seq),
  check (ended_at is null or ended_at >= started_at)
);

alter table public.transcript_turns enable row level security;

-- Privileges -------------------------------------------------------------------
-- Users get the narrowest grants that the product needs. Everything else goes
-- through the service role (agent, Grader), which bypasses RLS. In particular
-- Users can read their Transcript but never write it, so it cannot be forged.

revoke all on public.profiles, public.sessions, public.transcript_turns
  from anon, authenticated;

grant select on public.profiles to authenticated;
grant update (display_name) on public.profiles to authenticated;

grant select on public.sessions to authenticated;
grant insert (owner_id, exam_definition_ref, mode, medium) on public.sessions to authenticated;
grant update (status) on public.sessions to authenticated;
grant delete on public.sessions to authenticated;

grant select on public.transcript_turns to authenticated;

-- Row-level security -----------------------------------------------------------

create policy "profiles: read own"
  on public.profiles for select to authenticated
  using (id = (select auth.uid()));

create policy "profiles: update own"
  on public.profiles for update to authenticated
  using (id = (select auth.uid()))
  with check (id = (select auth.uid()));

create policy "sessions: read own"
  on public.sessions for select to authenticated
  using (owner_id = (select auth.uid()));

create policy "sessions: create own"
  on public.sessions for insert to authenticated
  with check (owner_id = (select auth.uid()));

create policy "sessions: update own"
  on public.sessions for update to authenticated
  using (owner_id = (select auth.uid()))
  with check (owner_id = (select auth.uid()));

create policy "sessions: delete own"
  on public.sessions for delete to authenticated
  using (owner_id = (select auth.uid()));

create policy "transcript_turns: read own"
  on public.transcript_turns for select to authenticated
  using (exists (
    select 1 from public.sessions s
    where s.id = transcript_turns.session_id and s.owner_id = (select auth.uid())
  ));
