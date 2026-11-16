import { isRealDate, type ExamDefinition } from "./index";
import { itemSchema, type Item } from "./item-generated";

export type { Item };

export class ItemError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ItemError";
  }
}

/**
 * Validates against the generated schema, then the checks JSON Schema cannot express.
 * Pass the Exam Definition the Item belongs to, to also check that the Item points at it
 * and names one of its Parts.
 */
export function parseItem(data: unknown, definition?: ExamDefinition): Item {
  // Pick the variant by `type` so errors name the failing field, not just "Invalid input".
  const variantsByType = new Map<unknown, (typeof itemSchema.options)[number]>(
    itemSchema.options.map((v) => [v.shape.type.value, v]),
  );
  const itemType = (data as { type?: unknown } | null)?.type;
  const variant = variantsByType.get(itemType);
  if (!variant) {
    throw new ItemError(
      `Invalid Item:\ntype: must be one of ${[...variantsByType.keys()].join(", ")}`,
    );
  }
  const result = variant.safeParse(data);
  if (!result.success) {
    const lines = result.error.issues.map(
      (i) => `${i.path.join(".")}: ${i.message}`,
    );
    throw new ItemError(`Invalid Item:\n${lines.join("\n")}`);
  }
  const item = result.data;
  const problems: string[] = [];

  if (!isRealDate(item.generation.date)) {
    problems.push(
      `generation.date '${item.generation.date}' is not a real date`,
    );
  }
  if (definition) {
    const expectedRef = `${definition.id}@${definition.version}`;
    if (item.exam_definition !== expectedRef) {
      problems.push(
        `exam_definition '${item.exam_definition}' does not match ` +
          `the Exam Definition it is checked against, '${expectedRef}'`,
      );
    }
    const part = definition.parts.find((p) => p.key === item.part_key);
    if (!part) {
      const partKeys = definition.parts.map((p) => p.key);
      problems.push(
        `part_key '${item.part_key}' is not a Part of '${expectedRef}': [${partKeys.join(", ")}]`,
      );
    } else if (part.item_type && part.item_type !== item.type) {
      problems.push(
        `Item type '${item.type}' does not fit Part '${part.key}', ` +
          `which takes '${part.item_type}' Items`,
      );
    }
  }

  if (problems.length > 0) {
    throw new ItemError(`Invalid Item:\n${problems.join("\n")}`);
  }
  return item;
}
