import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { parse } from "yaml";
import { parseExamDefinition } from "./index";
import { TaxonomyError, parseTaxonomy } from "./taxonomy";

const root = resolve(__dirname, "../../../..");
const yamlFile = (...path: string[]): unknown =>
  parse(readFileSync(resolve(root, ...path), "utf8"));
const fixture = (name: string): unknown =>
  yamlFile("schema/fixtures/taxonomy", name);
const fixtureExam = () =>
  parseExamDefinition(yamlFile("schema/fixtures/valid.yaml"));
const a2Exam = () =>
  parseExamDefinition(yamlFile("content/exams/delf-a2-tp.yaml"));

describe("Topic Taxonomy validation", () => {
  it("accepts the valid fixture against its Exam Definition", () => {
    const taxonomy = parseTaxonomy(fixture("valid.yaml"), fixtureExam());
    expect(taxonomy.parts.map((p) => p.key)).toEqual([
      "guided_interview",
      "monologue",
    ]);
  });

  it("rejects a duplicate theme key in a Part", () => {
    expect(() =>
      parseTaxonomy(fixture("invalid-duplicate-theme.yaml")),
    ).toThrow(/Duplicate theme key 'family'.*guided_interview/);
  });

  it("rejects a personal-sphere theme without a justification", () => {
    expect(() =>
      parseTaxonomy(fixture("invalid-missing-justification.yaml")),
    ).toThrow(TaxonomyError);
  });

  it("rejects a Part that is not in the Exam Definition", () => {
    expect(() =>
      parseTaxonomy(
        fixture("invalid-part-not-in-definition.yaml"),
        fixtureExam(),
      ),
    ).toThrow(/Part 'role_play' is not a Part/);
  });

  it("rejects an Exam Definition Part with no themes", () => {
    const data = fixture("valid.yaml") as { parts: unknown[] };
    data.parts.pop();
    expect(() => parseTaxonomy(data, fixtureExam())).toThrow(
      /Part 'monologue'.*has no themes/,
    );
  });

  it("rejects a taxonomy for a different Exam Definition version", () => {
    const data = fixture("valid.yaml") as { exam_definition: string };
    data.exam_definition = "fixture-a2@2";
    expect(() => parseTaxonomy(data, fixtureExam())).toThrow(
      /does not match 'fixture-a2@1'/,
    );
  });
});

describe("the A2 Topic Taxonomy", () => {
  const taxonomy = () =>
    parseTaxonomy(yamlFile("content/taxonomy/a2.yaml"), a2Exam());

  it("validates against the A2 Exam Definition", () => {
    expect(taxonomy().parts.map((p) => p.key)).toEqual([
      "entretien_dirige",
      "monologue_suivi",
      "exercice_en_interaction",
    ]);
  });

  it("has at least twelve themes per Part", () => {
    for (const part of taxonomy().parts) {
      expect(part.themes.length, part.key).toBeGreaterThanOrEqual(12);
    }
  });
});
