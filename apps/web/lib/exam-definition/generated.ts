// GENERATED from schema/exam-definition.schema.json by scripts/codegen.mjs. Do not edit.
import { z } from "zod";

export const examDefinitionSchema = z
  .object({
    id: z.string().regex(new RegExp("^[a-z0-9]+(-[a-z0-9]+)*$")),
    version: z.number().int().gte(1),
    level: z.enum(["A1", "A2", "B1", "B2", "C1", "C2"]),
    parts: z
      .array(
        z
          .object({
            key: z.string().regex(new RegExp("^[a-z0-9]+(_[a-z0-9]+)*$")),
            target_duration_seconds: z
              .object({
                min: z.number().int().gte(1),
                max: z.number().int().gte(1),
              })
              .strict()
              .describe(
                "Target live time in seconds. Use the same number for min and max when the exam gives a single approximate time.",
              ),
            turn_mode: z.enum(["interactive", "listen_only"]),
            item_type: z
              .enum([
                "question_bank",
                "monologue_subject",
                "interaction_situation",
              ])
              .describe("The one Item type a Candidate is given in this Part.")
              .optional(),
          })
          .strict(),
      )
      .min(1),
    prep_periods: z
      .array(
        z
          .object({
            time_seconds: z.number().int().gte(1),
            parts: z
              .array(z.string().regex(new RegExp("^[a-z0-9]+(_[a-z0-9]+)*$")))
              .min(1),
          })
          .strict()
          .describe(
            "One timed Prep Time before the live Parts, shared by the Parts it covers.",
          ),
      )
      .describe("Prep Time before the live Parts. Omit when the exam has none.")
      .optional(),
    grid: z
      .array(
        z
          .object({
            key: z.string().regex(new RegExp("^[a-z0-9]+(_[a-z0-9]+)*$")),
            scope: z.union([
              z
                .object({
                  kind: z.literal("part"),
                  part: z
                    .string()
                    .regex(new RegExp("^[a-z0-9]+(_[a-z0-9]+)*$")),
                })
                .strict(),
              z.object({ kind: z.literal("global") }).strict(),
            ]),
            band_points: z
              .array(z.number())
              .min(4)
              .max(4)
              .describe(
                "Points for Band 0, 1, 2 and 3, in order. Starts at 0 and never decreases.",
              ),
            descriptors: z
              .object({
                band_1: z.string().min(1),
                band_2: z.string().min(1),
                band_3: z.string().min(1),
              })
              .strict()
              .describe(
                "Paraphrased performance descriptors for Bands 1 to 3. Never copied from official text.",
              )
              .optional(),
          })
          .strict(),
      )
      .min(1),
    provenance: z
      .object({
        source_url: z.string().url(),
        retrieved_on: z.string().regex(new RegExp("^\\d{4}-\\d{2}-\\d{2}$")),
        links: z
          .array(
            z
              .object({ label: z.string().min(1), url: z.string().url() })
              .strict(),
          )
          .describe("Further sources the definition was built from.")
          .optional(),
      })
      .strict(),
  })
  .strict()
  .describe(
    "The versioned description of one exam format: its Level, its Parts in order, the timings and the Grid.",
  );
export type ExamDefinition = z.infer<typeof examDefinitionSchema>;
