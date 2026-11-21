import type { ExamDefinition } from "./index";
import { topicTaxonomySchema, type TopicTaxonomy } from "./taxonomy-generated";

export type { TopicTaxonomy };

export class TaxonomyError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "TaxonomyError";
  }
}

/**
 * Validates against the generated schema, then the checks JSON Schema cannot express.
 * Pass the Exam Definition to also check the Parts line up with it.
 */
export function parseTaxonomy(
  data: unknown,
  definition?: ExamDefinition,
): TopicTaxonomy {
  const result = topicTaxonomySchema.safeParse(data);
  if (!result.success) {
    const lines = result.error.issues.map(
      (i) => `${i.path.join(".")}: ${i.message}`,
    );
    throw new TaxonomyError(`Invalid Topic Taxonomy:\n${lines.join("\n")}`);
  }
  const taxonomy = result.data;
  const problems: string[] = [];

  const partKeys = taxonomy.parts.map((p) => p.key);
  for (const key of duplicates(partKeys))
    problems.push(`Duplicate Part key '${key}'`);
  for (const part of taxonomy.parts) {
    for (const key of duplicates(part.themes.map((t) => t.key))) {
      problems.push(`Duplicate theme key '${key}' in Part '${part.key}'`);
    }
  }

  if (definition) {
    const expectedRef = `${definition.id}@${definition.version}`;
    if (taxonomy.exam_definition !== expectedRef) {
      problems.push(
        `exam_definition '${taxonomy.exam_definition}' does not match '${expectedRef}'`,
      );
    }
    const defined = definition.parts.map((p) => p.key);
    for (const key of partKeys) {
      if (!defined.includes(key)) {
        problems.push(
          `Part '${key}' is not a Part of '${expectedRef}': [${defined.join(", ")}]`,
        );
      }
    }
    for (const key of defined) {
      if (!partKeys.includes(key)) {
        problems.push(`Part '${key}' of '${expectedRef}' has no themes`);
      }
    }
  }

  if (problems.length > 0) {
    throw new TaxonomyError(`Invalid Topic Taxonomy:\n${problems.join("\n")}`);
  }
  return taxonomy;
}

function duplicates(items: string[]): string[] {
  return [...new Set(items.filter((item, i) => items.indexOf(item) !== i))];
}
