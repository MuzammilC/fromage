# Fromage

Spoken-French exam coach. Vocabulary lives in [`CONTEXT.md`](CONTEXT.md); decisions in [`docs/adr/`](docs/adr/).

## Layout

- `apps/web` – Next.js (App Router, TypeScript) web app. pnpm workspace.
- `apps/agent` – Python LiveKit agent. uv workspace.
- `apps/grader` – Python grader. uv workspace.
- `content/` – Exam Definitions and Items as versioned data (ADR-0002).

## Develop

Requires Node 24, pnpm 10 and uv.

```bash
pnpm install && uv sync
pnpm lint        # ESLint, Prettier, Ruff
pnpm test        # Vitest
uv run pytest    # pytest (agent + grader)
```

CI (`.github/workflows/ci.yml`) runs the same on every PR.

`.github/workflows/supabase-keepalive.yml` queries Supabase every 3 days so the free-tier project never pauses (ADR-0008). It needs the repository secrets `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`; trigger it manually from the Actions tab to test.

## Environment

Copy `.env.example` to `.env` at the repo root. The web app, the agent and `gen-items` all read that one file.

## Generating draft Items

```bash
uv run gen-items --exam delf-a2-tp --part monologue_suivi --theme logement --n 3
```

It needs `ANTHROPIC_API_KEY` and the `LANGFUSE_*` keys from the repo-root `.env`.
Writes draft Items to `content/items/`, traces each call in Langfuse and prints the run's cost.
Generation prompts live in `packages/item_generator/src/fromage_item_generator/prompts/`; the
file's version (for example `monologue_subject-v1`) is stamped into every Item.
