begin;
create extension if not exists pgtap with schema extensions;
select plan(10);

insert into auth.users (id, instance_id, aud, role, email, email_confirmed_at)
values ('aaaaaaaa-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000000', 'authenticated', 'authenticated', 'alice@example.com', now());
insert into public.sessions (id, owner_id, exam_definition_ref, mode, medium)
values ('aaaaaaaa-1111-0000-0000-000000000001', 'aaaaaaaa-0000-0000-0000-000000000001', 'delf-a2@1', 'mock', 'text');

select public.add_session_cost('aaaaaaaa-1111-0000-0000-000000000001', 0.0010, '{"llm": 0.0010}');
select public.add_session_cost('aaaaaaaa-1111-0000-0000-000000000001', 0.0025, '{"llm": 0.0005, "stt": 0.0020}');

select is((select cost_usd from public.sessions), 0.0035::numeric, 'cost_usd accumulates');
select is((select (cost_breakdown ->> 'llm')::numeric from public.sessions), 0.0015::numeric, 'breakdown sums per source');
select is((select (cost_breakdown ->> 'stt')::numeric from public.sessions), 0.0020::numeric, 'breakdown adds new sources');

set local role authenticated;
select set_config('request.jwt.claims', '{"sub":"aaaaaaaa-0000-0000-0000-000000000001","role":"authenticated"}', true);
select throws_ok(
  $$select public.add_session_cost('aaaaaaaa-1111-0000-0000-000000000001', 1, '{}')$$,
  '42501', null, 'a User cannot add cost');
select throws_ok(
  $$update public.sessions set cost_usd = 0$$,
  '42501', null, 'a User cannot write cost directly');

-- The agent connects as service_role. Run the same calls it makes, with realistic
-- amounts (one Haiku call costs ~$0.00002).
reset role;
set local role service_role;

select lives_ok(
  $$insert into public.transcript_turns (session_id, seq, speaker, text, started_at)
    values ('aaaaaaaa-1111-0000-0000-000000000001', 0, 'candidate', 'Bonjour', now())$$,
  'service_role can insert a turn');
select throws_ok(
  $$delete from public.transcript_turns$$,
  '42501', null, 'service_role cannot delete turns');

select public.add_session_cost('aaaaaaaa-1111-0000-0000-000000000001', 0.00002, '{"llm": 0.00002}');
select public.add_session_cost('aaaaaaaa-1111-0000-0000-000000000001', 0.00002, '{"llm": 0.00002}');
select is((select cost_usd from public.sessions), 0.00354::numeric, 'tiny costs are not rounded away');

select throws_ok(
  $$select public.add_session_cost('cccccccc-1111-0000-0000-000000000009', 0.00002, '{}')$$,
  'P0002', null, 'an unknown Session is an error');
select throws_ok(
  $$select public.add_session_cost('aaaaaaaa-1111-0000-0000-000000000001', null, '{}')$$,
  '22004', null, 'a null amount is an error');

select * from finish();
rollback;
