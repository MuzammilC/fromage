// GENERATED from schema/item.schema.json by scripts/codegen.mjs. Do not edit.
import { z } from "zod";

export const itemSchema = z
  .union([
    z
      .object({
        type: z.literal("question_bank"),
        id: z.string().regex(new RegExp("^[a-z0-9]+(-[a-z0-9]+)*$")),
        exam_definition: z
          .string()
          .regex(new RegExp("^[a-z0-9]+(-[a-z0-9]+)*@[1-9][0-9]*$"))
          .describe(
            "The Exam Definition this Item belongs to, as `id@version`.",
          ),
        part_key: z.string().regex(new RegExp("^[a-z0-9]+(_[a-z0-9]+)*$")),
        topics: z
          .array(z.string().regex(new RegExp("^[a-z0-9]+(_[a-z0-9]+)*$")))
          .min(1)
          .describe("Topic Taxonomy entries for this Item."),
        status: z.enum(["draft", "reviewed", "retired"]),
        version: z.number().int().gte(1),
        generation: z
          .object({
            model: z.string().min(1),
            prompt_version: z.string().min(1),
            date: z.string().regex(new RegExp("^\\d{4}-\\d{2}-\\d{2}$")),
          })
          .strict(),
        teacher_reviewed: z.literal(false),
        questions: z.array(z.string().min(1)).min(1),
      })
      .strict()
      .describe(
        "The questions the Examiner draws from in the guided interview (A2 Part 1).",
      ),
    z
      .object({
        type: z.literal("monologue_subject"),
        id: z.string().regex(new RegExp("^[a-z0-9]+(-[a-z0-9]+)*$")),
        exam_definition: z
          .string()
          .regex(new RegExp("^[a-z0-9]+(-[a-z0-9]+)*@[1-9][0-9]*$"))
          .describe(
            "The Exam Definition this Item belongs to, as `id@version`.",
          ),
        part_key: z.string().regex(new RegExp("^[a-z0-9]+(_[a-z0-9]+)*$")),
        topics: z
          .array(z.string().regex(new RegExp("^[a-z0-9]+(_[a-z0-9]+)*$")))
          .min(1)
          .describe("Topic Taxonomy entries for this Item."),
        status: z.enum(["draft", "reviewed", "retired"]),
        version: z.number().int().gte(1),
        generation: z
          .object({
            model: z.string().min(1),
            prompt_version: z.string().min(1),
            date: z.string().regex(new RegExp("^\\d{4}-\\d{2}-\\d{2}$")),
          })
          .strict(),
        teacher_reviewed: z.literal(false),
        candidate_brief: z.string().min(1),
        suggested_angles: z.array(z.string().min(1)).min(1),
      })
      .strict()
      .describe("A subject the Candidate speaks on continuously (A2 Part 2)."),
    z
      .object({
        type: z.literal("interaction_situation"),
        id: z.string().regex(new RegExp("^[a-z0-9]+(-[a-z0-9]+)*$")),
        exam_definition: z
          .string()
          .regex(new RegExp("^[a-z0-9]+(-[a-z0-9]+)*@[1-9][0-9]*$"))
          .describe(
            "The Exam Definition this Item belongs to, as `id@version`.",
          ),
        part_key: z.string().regex(new RegExp("^[a-z0-9]+(_[a-z0-9]+)*$")),
        topics: z
          .array(z.string().regex(new RegExp("^[a-z0-9]+(_[a-z0-9]+)*$")))
          .min(1)
          .describe("Topic Taxonomy entries for this Item."),
        status: z.enum(["draft", "reviewed", "retired"]),
        version: z.number().int().gte(1),
        generation: z
          .object({
            model: z.string().min(1),
            prompt_version: z.string().min(1),
            date: z.string().regex(new RegExp("^\\d{4}-\\d{2}-\\d{2}$")),
          })
          .strict(),
        teacher_reviewed: z.literal(false),
        candidate_brief: z.string().min(1),
        examiner_role: z.string().min(1),
        examiner_only_data: z
          .record(z.string(), z.any())
          .describe(
            "Facts only the Examiner knows, such as a price list or a timetable.",
          ),
        expected_speech_acts: z.array(z.string().min(1)).min(1),
        register: z.enum(["formal", "informal"]),
      })
      .strict()
      .describe(
        "An everyday situation the Candidate resolves with the Examiner (A2 Part 3).",
      ),
  ])
  .describe(
    "One original brief a Candidate can be given for a Part. The `type` says which kind.",
  );
export type Item = z.infer<typeof itemSchema>;
