// Regenerates zod (apps/web) and Pydantic (packages/exam_definition) types from the
// Exam Definition and Item JSON Schemas. Run with `pnpm codegen`.
import { execFileSync } from "node:child_process";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import $RefParser from "@apidevtools/json-schema-ref-parser";
import { jsonSchemaToZod } from "json-schema-to-zod";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const webOut = resolve(root, "apps/web/lib/exam-definition");
const pyOut = resolve(
  root,
  "packages/exam_definition/src/fromage_exam_definition",
);

const targets = [
  {
    schema: "exam-definition.schema.json",
    zod: {
      file: "generated.ts",
      name: "examDefinitionSchema",
      type: "ExamDefinition",
    },
    pydantic: "generated.py",
  },
  {
    schema: "item.schema.json",
    zod: { file: "item-generated.ts", name: "itemSchema", type: "Item" },
    pydantic: "item_generated.py",
  },
];

for (const target of targets) {
  const schemaPath = resolve(root, "schema", target.schema);
  const zodPath = resolve(webOut, target.zod.file);
  const pydanticPath = resolve(pyOut, target.pydantic);

  const dereferenced = await $RefParser.dereference(
    JSON.parse(readFileSync(schemaPath, "utf8")),
  );
  const zod = jsonSchemaToZod(dereferenced, {
    name: target.zod.name,
    module: "esm",
    type: target.zod.type,
  });
  mkdirSync(dirname(zodPath), { recursive: true });
  writeFileSync(
    zodPath,
    `// GENERATED from schema/${target.schema} by scripts/codegen.mjs. Do not edit.\n${zod}`,
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
      pydanticPath,
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

  execFileSync("pnpm", ["exec", "prettier", "--write", zodPath], {
    cwd: root,
    stdio: "inherit",
  });
  execFileSync("uv", ["run", "ruff", "format", pydanticPath], {
    cwd: root,
    stdio: "inherit",
  });
}
