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
