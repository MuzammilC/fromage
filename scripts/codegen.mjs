// Regenerates zod (apps/web) and Pydantic (packages/exam_definition) types from the
// Exam Definition JSON Schema. Run with `pnpm codegen`.
import { execFileSync } from "node:child_process";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import $RefParser from "@apidevtools/json-schema-ref-parser";
import { jsonSchemaToZod } from "json-schema-to-zod";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const schemaPath = resolve(root, "schema/exam-definition.schema.json");
const zodOut = resolve(root, "apps/web/lib/exam-definition/generated.ts");
const pydanticOut = resolve(
  root,
  "packages/exam_definition/src/fromage_exam_definition/generated.py",
);

const dereferenced = await $RefParser.dereference(
  JSON.parse(readFileSync(schemaPath, "utf8")),
);
const zod = jsonSchemaToZod(dereferenced, {
  name: "examDefinitionSchema",
  module: "esm",
  type: "ExamDefinition",
});
mkdirSync(dirname(zodOut), { recursive: true });
writeFileSync(
  zodOut,
  `// GENERATED from schema/exam-definition.schema.json by scripts/codegen.mjs. Do not edit.\n${zod}`,
);

execFileSync(
  "uv",
  [
    "run",
    "datamodel-codegen",
    "--input",
    schemaPath,
    "--input-file-type",
    "jsonschema",
    "--output",
    pydanticOut,
    "--output-model-type",
    "pydantic_v2.BaseModel",
    "--disable-timestamp",
    "--formatters",
    "black",
    "isort",
    "--use-annotated",
    "--target-python-version",
    "3.11",
  ],
  { cwd: root, stdio: "inherit" },
);

execFileSync("pnpm", ["exec", "prettier", "--write", zodOut], {
  cwd: root,
  stdio: "inherit",
});
execFileSync("uv", ["run", "ruff", "format", pydanticOut], {
  cwd: root,
  stdio: "inherit",
});
