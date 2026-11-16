# Users write little: column grants, a status trigger and a service role for everything else

Supabase exposes tables to the browser through PostgREST, so every grant and policy is a public API. The starter schema (`profiles`, `sessions`, `transcript_turns`) keeps Users to the narrowest writes the product needs. Row-level security (RLS) decides which rows a User can touch, and column grants decide which columns.

- **Rows:** a User reads and writes only rows they own. `transcript_turns` follows its Session's owner. The `anon` role gets no access.
- **Transcript is read-only for Users.** The Grader judges the Transcript and quotes it as Evidence, so a User who could insert turns could write their own fluent answers. Only the service role (the agent) writes turns.
- **Cost fields are service-role only.** `cost_usd` and `cost_breakdown` feed the budget kill switch (ADR 0008). A User can create a Session with an `owner_id`, `exam_definition_ref`, Mode and Medium, and can update only `status`.
- **Status moves one way.** A trigger allows `in_progress` to `completed` or `abandoned` and nothing after that. A User can only abandon. Completing a Session hands it to the Grader (ADR 0006), so that is the service role's job. The trigger sets `ended_at`, and a check constraint keeps `ended_at` set exactly when the Session has left `in_progress`.
- **Profiles:** a User can read their row and change `display_name`, nothing else. A trigger creates the row on sign-up.
- **Accounts:** email verification is required, passwords need at least 10 characters with lower case, upper case and digits.

Column grants were chosen over a `security definer` function per write. They are plain SQL, they sit next to the table definition, and the pgTAP tests in `supabase/tests/database` cover each rule.

## Not built yet

- Rate limiting and the daily voice-Session limit from ADR 0008.
- `grading_jobs` (ADR 0006) and the report tables.
- A way for the agent to prove it is the one completing a Session beyond holding the service key.
- Deleting a User cascades to their Sessions and Transcripts. Whether Candidates can export or delete their own data is undecided.
