// GENERATED from schema/topic-taxonomy.schema.json by scripts/codegen.mjs. Do not edit.
import { z } from "zod";

export const topicTaxonomySchema = z
  .object({
    exam_definition: z
      .string()
      .regex(new RegExp("^[a-z0-9]+(-[a-z0-9]+)*@[1-9][0-9]*$"))
      .describe(
        "The Exam Definition this taxonomy belongs to, as `id@version`.",
      ),
    parts: z
      .array(
        z
          .object({
            key: z.string().regex(new RegExp("^[a-z0-9]+(_[a-z0-9]+)*$")),
            themes: z
              .array(
                z
                  .union([
                    z
                      .object({
                        key: z
                          .string()
                          .regex(new RegExp("^[a-z0-9]+(_[a-z0-9]+)*$")),
                        label: z
                          .object({
                            en: z.string().regex(new RegExp("\\S")).min(1),
                            fr: z.string().regex(new RegExp("\\S")).min(1),
                          })
                          .strict(),
                        source: z.literal("research"),
                        research_theme: z
                          .string()
                          .regex(new RegExp("\\S"))
                          .min(1),
                      })
                      .strict()
                      .describe(
                        "A theme named in docs/research/delf-speaking-coach.md §A.2.",
                      ),
                    z
                      .object({
                        key: z
                          .string()
                          .regex(new RegExp("^[a-z0-9]+(_[a-z0-9]+)*$")),
                        label: z
                          .object({
                            en: z.string().regex(new RegExp("\\S")).min(1),
                            fr: z.string().regex(new RegExp("\\S")).min(1),
                          })
                          .strict(),
                        source: z.literal("personal_sphere"),
                        justification: z
                          .string()
                          .regex(new RegExp("\\S"))
                          .min(1),
                      })
                      .strict()
                      .describe(
                        "Ordinary A2 personal-sphere content that the research doc does not name.",
                      ),
                  ])
                  .describe(
                    "One theme. `key` is what an Item's `topics` list refers to. Every theme is traceable: it either names a research-doc theme or is justified as personal-sphere A2 content.",
                  ),
              )
              .min(1),
          })
          .strict(),
      )
      .min(1),
  })
  .strict()
  .describe(
    "The themes for each Part of one Exam Definition that original Items are written against. Themes only, no prompt text.",
  );
export type TopicTaxonomy = z.infer<typeof topicTaxonomySchema>;
