# Exam Definitions and Items are versioned data files in a monorepo

Exam Definitions (Parts, timings, Turn Modes, Grid) and Items live as YAML files in `content/`, validated by a JSON Schema. TypeScript types (zod) and Python types (Pydantic) are generated from that schema, and Supabase rows refer to definitions by `id@version`.

Both the TypeScript web app and the Python agent and Grader read the same definitions, so everything lives in one monorepo: `apps/web`, `apps/agent`, `apps/grader`, `content/`. Storing definitions in the database was rejected. Files can be reviewed in PRs, diffed and pinned to a version, and a new exam format such as TCF Canada becomes a new file instead of new code.
