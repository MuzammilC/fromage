# Fromage agent

A LiveKit Agents worker that joins a Session room (`session-<sessionId>`). For each
Candidate text message (text stream, topic `chat`) it asks `claude-haiku-5-5` to
paraphrase it in simple French, replies on the same topic, saves both turns to
`transcript_turns`, adds the call's cost to the Session, and traces the call in Langfuse.

Layout: `echo.py` is the pure core (tested with fakes); `llm.py`, `store.py` and
`worker.py` are the Anthropic/Langfuse, Supabase and LiveKit adapters.

## Environment

Copy `.env.example` to `.env.local` in this directory (it is gitignored) and fill it in.

| Variable                                                          | Notes                                                                           |
| ----------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`            | Cloud project, or the local dev server values below                             |
| `ANTHROPIC_API_KEY`                                               |                                                                                 |
| `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL` |                                                                                 |
| `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`                       | Service role bypasses RLS: keep it server-side. Locally, from `supabase status` |

On LiveKit Cloud the `LIVEKIT_*` values are injected for you; the others are secrets (below).

## Run locally (no cloud minutes)

Needs [uv](https://docs.astral.sh/uv/), the [LiveKit server](https://docs.livekit.io/home/self-hosting/local/)
and the [Supabase CLI](https://supabase.com/docs/guides/local-development) with Docker.

From the repo root:

```bash
supabase start && supabase db reset        # local database, includes migrations
livekit-server --dev                       # ws://localhost:7880, key "devkey", secret "secret"
uv sync --all-packages
```

Point both apps at the local servers: in `apps/agent/.env.local` set
`LIVEKIT_URL=ws://localhost:7880`, `LIVEKIT_API_KEY=devkey`, `LIVEKIT_API_SECRET=secret`,
`SUPABASE_URL=http://127.0.0.1:54321`, the local service role key, plus your Anthropic and Langfuse keys.
In `apps/web/.env.local` set `NEXT_PUBLIC_LIVEKIT_URL=ws://localhost:7880` and the same
`LIVEKIT_API_KEY` / `LIVEKIT_API_SECRET`. Then:

```bash
uv run --env-file apps/agent/.env.local python -m fromage_agent.worker dev   # terminal 1
pnpm --filter web dev                                                         # terminal 2
```

Sign up, start a Session, and type a message: the Examiner answers and both turns
appear in `transcript_turns`. The Langfuse trace is named `paraphrase`.

## Deploy to LiveKit Cloud

Install the [`lk` CLI](https://docs.livekit.io/home/cli/) and `lk cloud auth`, then from `apps/agent`:

```bash
lk agent create          # first time only: writes livekit.toml
lk agent update-secrets --secrets-file .env.secrets   # restarts the agent; `lk agent secrets` lists them
lk agent deploy          # later deploys
```

`.env.secrets` holds `KEY=VALUE` lines for the variables in the table above, except `LIVEKIT_*`. It is gitignored (`.env*`).

The agent has no `agent_name`, so LiveKit dispatches it automatically to every new room.

## Tests

```bash
uv run pytest apps/agent
```
