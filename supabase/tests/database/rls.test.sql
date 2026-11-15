begin;
create extension if not exists pgtap with schema extensions;
select plan(23);

-- Two Users. The trigger creates their profiles.
insert into auth.users (id, instance_id, aud, role, email, email_confirmed_at)
values
  ('aaaaaaaa-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000000', 'authenticated', 'authenticated', 'alice@example.com', now()),
  ('bbbbbbbb-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000000', 'authenticated', 'authenticated', 'bob@example.com', now());

select is((select count(*)::int from public.profiles), 2, 'signing up creates a profile per user');

-- Seed Sessions and turns as the table owner (bypasses RLS, like the service role).
insert into public.sessions (id, owner_id, exam_definition_ref, mode, medium)
values
  ('aaaaaaaa-1111-0000-0000-000000000001', 'aaaaaaaa-0000-0000-0000-000000000001', 'delf-a2@1', 'mock', 'text'),
  ('bbbbbbbb-1111-0000-0000-000000000002', 'bbbbbbbb-0000-0000-0000-000000000002', 'delf-a1@2', 'practice', 'voice'),
  ('bbbbbbbb-1111-0000-0000-000000000003', 'bbbbbbbb-0000-0000-0000-000000000002', 'delf-a1@2', 'mock', 'text');
insert into public.transcript_turns (session_id, seq, speaker, text, started_at)
values
  ('aaaaaaaa-1111-0000-0000-000000000001', 0, 'examiner', 'Bonjour.', now()),
  ('bbbbbbbb-1111-0000-0000-000000000002', 0, 'candidate', 'Bonjour', now());

-- Act as Bob.
set local role authenticated;
select set_config('request.jwt.claims', '{"sub":"bbbbbbbb-0000-0000-0000-000000000002","role":"authenticated"}', true);

-- Isolation: reading.
select is((select count(*)::int from public.sessions where id = 'aaaaaaaa-1111-0000-0000-000000000001'), 0, 'Bob cannot read Alice''s Session');
select is((select count(*)::int from public.transcript_turns where session_id = 'aaaaaaaa-1111-0000-0000-000000000001'), 0, 'Bob cannot read Alice''s turns');
select is((select count(*)::int from public.profiles), 1, 'Bob only sees his own profile');
select is((select count(*)::int from public.transcript_turns), 1, 'Bob reads his own turn');

-- Isolation: writing.
select throws_ok(
  $$insert into public.sessions (owner_id, exam_definition_ref, mode, medium)
    values ('aaaaaaaa-0000-0000-0000-000000000001', 'delf-a2@1', 'mock', 'text')$$,
  '42501', null, 'Bob cannot create a Session owned by Alice');
select is_empty(
  $$update public.sessions set status = 'abandoned' where id = 'aaaaaaaa-1111-0000-0000-000000000001' returning 1$$,
  'Bob cannot update Alice''s Session');
select is_empty(
  $$delete from public.sessions where id = 'aaaaaaaa-1111-0000-0000-000000000001' returning 1$$,
  'Bob cannot delete Alice''s Session');
select is_empty(
  $$update public.profiles set display_name = 'hacked' where id = 'aaaaaaaa-0000-0000-0000-000000000001' returning 1$$,
  'Bob cannot update Alice''s profile');

-- Transcripts are read-only for Users, even in their own Session.
select throws_ok(
  $$insert into public.transcript_turns (session_id, seq, speaker, text, started_at)
    values ('bbbbbbbb-1111-0000-0000-000000000002', 1, 'candidate', 'Salut', now())$$,
  '42501', null, 'Bob cannot add a turn, even to his own Session');
select throws_ok(
  $$update public.transcript_turns set text = 'edited'$$,
  '42501', null, 'Bob cannot edit a turn');
select throws_ok(
  $$delete from public.transcript_turns$$,
  '42501', null, 'Bob cannot delete a turn');

-- Users cannot tamper with cost fields, ownership, ended_at or profile ids.
select throws_ok(
  $$update public.sessions set cost_usd = 0 where id = 'bbbbbbbb-1111-0000-0000-000000000002'$$,
  '42501', null, 'Bob cannot write cost fields');
select throws_ok(
  $$update public.sessions set owner_id = 'aaaaaaaa-0000-0000-0000-000000000001' where id = 'bbbbbbbb-1111-0000-0000-000000000002'$$,
  '42501', null, 'Bob cannot give his Session away');
select throws_ok(
  $$update public.sessions set ended_at = now() where id = 'bbbbbbbb-1111-0000-0000-000000000002'$$,
  '42501', null, 'Bob cannot write ended_at');
select throws_ok(
  $$update public.profiles set id = 'cccccccc-0000-0000-0000-000000000003'$$,
  '42501', null, 'Bob cannot change his profile id');
select lives_ok(
  $$update public.profiles set display_name = 'Bob'$$,
  'Bob can change his display name');

-- Bad references are rejected.
select throws_ok(
  $$insert into public.sessions (owner_id, exam_definition_ref, mode, medium)
    values ('bbbbbbbb-0000-0000-0000-000000000002', 'delf-a2', 'mock', 'text')$$,
  '23514', null, 'exam_definition_ref must look like id@version');

-- Session status only moves forward, and a User can only abandon.
select throws_ok(
  $$update public.sessions set status = 'completed' where id = 'bbbbbbbb-1111-0000-0000-000000000003'$$,
  '42501', null, 'Bob cannot complete a Session himself');
update public.sessions set status = 'abandoned' where id = 'bbbbbbbb-1111-0000-0000-000000000002';
select ok(
  (select status = 'abandoned' and ended_at is not null from public.sessions where id = 'bbbbbbbb-1111-0000-0000-000000000002'),
  'Bob can abandon his Session and ended_at is set for him');
select throws_ok(
  $$update public.sessions set status = 'in_progress' where id = 'bbbbbbbb-1111-0000-0000-000000000002'$$,
  '23514', null, 'an abandoned Session cannot be reopened');

-- Anonymous visitors see nothing.
reset role;
set local role anon;
select throws_ok($$select * from public.sessions$$, '42501', null, 'anon cannot read sessions');
select throws_ok($$select * from public.transcript_turns$$, '42501', null, 'anon cannot read turns');

select * from finish();
rollback;
