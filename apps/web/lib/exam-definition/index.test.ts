import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { parse } from "yaml";
import { ExamDefinitionError, parseExamDefinition } from "./index";

const fixture = (name: string): unknown =>
  parse(
    readFileSync(
      resolve(__dirname, "../../../../schema/fixtures", name),
      "utf8",
    ),
  );

describe("parseExamDefinition", () => {
  it("accepts the valid fixture", () => {
    const definition = parseExamDefinition(fixture("valid.yaml"));
    expect(definition.id).toBe("fixture-a2");
    expect(definition.parts.map((p) => p.key)).toEqual([
      "guided_interview",
      "monologue",
    ]);
  });

  it("rejects a wrong Band Points total with a clear error", () => {
    expect(() =>
      parseExamDefinition(fixture("invalid-band-points-total.yaml")),
    ).toThrow(/Band Points.*25.*23/);
  });

  it("rejects a Criterion scoped to a missing Part with a clear error", () => {
    expect(() =>
      parseExamDefinition(fixture("invalid-missing-part.yaml")),
    ).toThrow(/monologue_achievement.*monologue/);
  });

  it("rejects schema violations", () => {
    const data = fixture("valid.yaml") as { grid: { band_points: number[] }[] };
    data.grid[0].band_points = [0, 1, 2];
    expect(() => parseExamDefinition(data)).toThrow(ExamDefinitionError);
    expect(() => parseExamDefinition(data)).toThrow(/band_points/);
  });

  it("rejects an impossible retrieval date", () => {
    const data = fixture("valid.yaml") as {
      provenance: { retrieved_on: string };
    };
    data.provenance.retrieved_on = "2026-99-99";
    expect(() => parseExamDefinition(data)).toThrow(
      /retrieved_on.*not a real date/,
    );
  });
});
