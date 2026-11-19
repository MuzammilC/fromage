begin;
create extension if not exists pgtap with schema extensions;
select plan(5);

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

select * from finish();
rollback;
