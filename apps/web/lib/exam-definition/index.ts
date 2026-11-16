import { examDefinitionSchema, type ExamDefinition } from "./generated";

export type { ExamDefinition };
export const GRID_TOTAL_POINTS = 25;

export class ExamDefinitionError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ExamDefinitionError";
  }
}

/** Validates against the generated schema, then the checks JSON Schema cannot express. */
export function parseExamDefinition(data: unknown): ExamDefinition {
  const result = examDefinitionSchema.safeParse(data);
  if (!result.success) {
    const lines = result.error.issues.map(
      (i) => `${i.path.join(".")}: ${i.message}`,
    );
    throw new ExamDefinitionError(
      `Invalid Exam Definition:\n${lines.join("\n")}`,
    );
  }
  const definition = result.data;
  const problems: string[] = [];

  const partKeys = definition.parts.map((p) => p.key);
  for (const key of duplicates(partKeys))
    problems.push(`Duplicate Part key '${key}'`);
  for (const key of duplicates(definition.grid.map((c) => c.key))) {
    problems.push(`Duplicate Criterion key '${key}'`);
  }

  for (const part of definition.parts) {
    const { min, max } = part.target_duration_seconds;
    if (min > max) {
      problems.push(
        `Part '${part.key}': target duration min ${min} is above max ${max}`,
      );
    }
  }

  const covered: string[] = [];
  for (const period of definition.prep_periods ?? []) {
    for (const part of period.parts) {
      if (!partKeys.includes(part)) {
        problems.push(
          `Prep Time covers Part '${part}', ` +
            `which is not one of the Parts: [${partKeys.join(", ")}]`,
        );
      }
      covered.push(part);
    }
  }
  for (const key of duplicates(covered)) {
    problems.push(`Part '${key}' is covered by more than one Prep Time`);
  }

  for (const criterion of definition.grid) {
    const { scope, band_points: points } = criterion;
    if (scope.kind === "part" && !partKeys.includes(scope.part)) {
      problems.push(
        `Criterion '${criterion.key}' is scoped to Part '${scope.part}', ` +
          `which is not one of the Parts: [${partKeys.join(", ")}]`,
      );
    }
    if (points[0] !== 0 || points.some((p, i) => i > 0 && p < points[i - 1])) {
      problems.push(
        `Criterion '${criterion.key}': Band Points [${points.join(", ")}] must start at 0 and never decrease`,
      );
    }
  }

  const total = definition.grid.reduce(
    (sum, c) => sum + topBandPoints(c.band_points),
    0,
  );
  if (total !== GRID_TOTAL_POINTS) {
    problems.push(
      `The Band Points of the top Band must add up to ${GRID_TOTAL_POINTS}, got ${total}`,
    );
  }

  if (!isRealDate(definition.provenance.retrieved_on)) {
    problems.push(
      `provenance.retrieved_on '${definition.provenance.retrieved_on}' is not a real date`,
    );
  }

  if (problems.length > 0) {
    throw new ExamDefinitionError(
      `Invalid Exam Definition:\n${problems.join("\n")}`,
    );
  }
  return definition;
}

/** Points for Band 3, the top Band. */
function topBandPoints(bandPoints: number[]): number {
  return bandPoints[bandPoints.length - 1];
}

export function isRealDate(value: string): boolean {
  const date = new Date(`${value}T00:00:00Z`);
  return !Number.isNaN(date.getTime()) && date.toISOString().startsWith(value);
}

function duplicates(items: string[]): string[] {
  return [...new Set(items.filter((item, i) => items.indexOf(item) !== i))];
}
