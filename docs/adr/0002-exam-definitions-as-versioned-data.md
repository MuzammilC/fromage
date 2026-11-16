# Exam Definitions and Items are versioned data files in a monorepo

Exam Definitions (Parts, timings, Turn Modes, Grid) and Items live as YAML files in `content/`, validated by a JSON Schema. TypeScript types (zod) and Python types (Pydantic) are generated from that schema, and Supabase rows refer to definitions by `id@version`.

Both the TypeScript web app and the Python agent and Grader read the same definitions, so everything lives in one monorepo: `apps/web`, `apps/agent`, `apps/grader`, `content/`. Storing definitions in the database was rejected. Files can be reviewed in PRs, diffed and pinned to a version, and a new exam format such as TCF Canada becomes a new file instead of new code.

## Where the schema and generated types live

- `schema/` holds the two JSON Schemas (`exam-definition.schema.json`, `item.schema.json`) and the test fixtures (valid and invalid Exam Definitions, and example Items in `fixtures/items/`). An Item points at its Exam Definition as `id@version`. Real Exam Definitions and Items go in `content/`, not here.
- `packages/exam_definition` is a shared Python package with the generated Pydantic models and the validator. The agent and the Grader both depend on it, so the Python side has one copy of the models.
- `apps/web/lib/exam-definition` holds the generated zod types and the TypeScript validator.
- `pnpm codegen` regenerates both sets of types from the schema. `pnpm codegen:check` runs in CI and fails if the generated files are stale.

JSON Schema cannot express some rules: the top-Band Band Points must add up to 25, Band Points start at 0 and never decrease, a Criterion scoped to a Part must name a Part that exists, keys are unique, a duration range's min is at most its max, Prep Time covers only Parts that exist and no Part twice, and the retrieval date must be a real date. When an Item is checked against its Exam Definition, it must point at that `id@version`, name a Part that exists, and be of the `item_type` that Part takes. These are written by hand in each validator, so a new rule needs an edit in both the TypeScript and the Python validator.

## How timings and Items attach to Parts

- A Part's `target_duration_seconds` is a `{min, max}` range. Use the same number for both when the exam gives one approximate time.
- Prep Time is a list of `prep_periods`, each with a time and the Parts it covers, because one period can be shared (A2 has one 10-minute period for Parts 2 and 3). A Part with no period has no Prep Time.
- A Part's optional `item_type` says which Item type it takes. When it is set, an Item checked against the definition must match it.

## Not built yet

- The real DELF A1 Exam Definition. The A2 one is `content/exams/delf-a2-tp.yaml`.
- Item types for A1 (Cards, role-play with a Wallet). `schema/item.schema.json` covers the three A2 types: question bank, monologue subject, interaction situation. The A1 Parts will need `item_type` values for them.
- A guard against the two validators drifting apart, such as shared test cases that both run.
