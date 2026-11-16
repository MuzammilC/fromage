import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { parse } from "yaml";
import { parseExamDefinition } from "./index";
import { ItemError, parseItem } from "./item";

const root = resolve(__dirname, "../../../..");
const yamlFile = (...path: string[]): unknown =>
  parse(readFileSync(resolve(root, ...path), "utf8"));
const fixture = (name: string): unknown =>
  yamlFile("schema/fixtures/items", name);
const a2 = () => parseExamDefinition(yamlFile("content/exams/delf-a2-tp.yaml"));

describe("the DELF A2 Exam Definition", () => {
  it("validates, with Band Points that add up to 25", () => {
    const definition = a2();
    expect(definition.id).toBe("delf-a2-tp");
    expect(definition.grid.reduce((sum, c) => sum + c.band_points[3], 0)).toBe(
      25,
    );
  });

  it("has the three A2 Parts with their Turn Modes", () => {
    expect(a2().parts.map((p) => [p.key, p.turn_mode])).toEqual([
      ["entretien_dirige", "interactive"],
      ["monologue_suivi", "listen_only"],
      ["exercice_en_interaction", "interactive"],
    ]);
  });

  it("uses the A2 Band Points", () => {
    const points = Object.fromEntries(
      a2().grid.map((c) => [c.key, c.band_points]),
    );
    expect(points).toEqual({
      entretien_dirige: [0, 1, 2.5, 4],
      monologue_suivi: [0, 1, 2.5, 4],
      exercice_en_interaction: [0, 1, 2.5, 4],
      lexique: [0, 1, 3, 5],
      morphosyntaxe: [0, 1, 2.5, 4],
      phonologie: [0, 1, 2.5, 4],
    });
  });

  it("describes Bands 1 to 3 of every Criterion and links its sources", () => {
    const definition = a2();
    for (const criterion of definition.grid) {
      expect(criterion.descriptors, criterion.key).toBeDefined();
    }
    expect(definition.provenance.links?.length).toBeGreaterThan(0);
  });
});

describe("parseItem", () => {
  it.each([
    ["valid-question-bank.yaml", "question_bank"],
    ["valid-monologue-subject.yaml", "monologue_subject"],
    ["valid-interaction-situation.yaml", "interaction_situation"],
  ])("accepts %s", (file, type) => {
    expect(parseItem(fixture(file)).type).toBe(type);
  });

  it("accepts an Item whose Part exists in its Exam Definition", () => {
    expect(
      parseItem(fixture("valid-interaction-situation.yaml"), a2()).part_key,
    ).toBe("exercice_en_interaction");
  });

  it.each([
    ["invalid-missing-examiner-role.yaml", /examiner_role/],
    ["invalid-status.yaml", /status/],
    ["invalid-exam-definition-ref.yaml", /exam_definition/],
    ["invalid-type.yaml", /type/],
    ["invalid-generation-date.yaml", /generation\.date.*not a real date/],
    ["invalid-missing-teacher-reviewed.yaml", /teacher_reviewed/],
    ["invalid-teacher-reviewed-true.yaml", /teacher_reviewed/],
  ])("rejects %s with a clear error", (file, message) => {
    expect(() => parseItem(fixture(file))).toThrow(ItemError);
    expect(() => parseItem(fixture(file))).toThrow(message);
  });

  it("rejects an Item for a Part its Exam Definition lacks", () => {
    const data = fixture("valid-question-bank.yaml") as { part_key: string };
    data.part_key = "dialogue_simule";
    expect(() => parseItem(data, a2())).toThrow(/dialogue_simule.*Part/);
  });

  it("rejects an Item that points at another Exam Definition", () => {
    const data = fixture("valid-question-bank.yaml") as {
      exam_definition: string;
    };
    data.exam_definition = "delf-a2-tp@2";
    expect(() => parseItem(data, a2())).toThrow(/delf-a2-tp@2.*delf-a2-tp@1/);
  });
});
