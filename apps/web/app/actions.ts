"use server";

import { headers } from "next/headers";
import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";

export type FormState = { error?: string } | undefined;

// The only Exam Definition in Phase 1 slice 1.0; later slices let the Candidate choose.
const EXAM_DEFINITION_REF = "delf-a2@1";

async function origin() {
  const h = await headers();
  return h.get("origin") ?? `https://${h.get("host")}`;
}

function credentials(formData: FormData) {
  return {
    email: String(formData.get("email") ?? "").trim(),
    password: String(formData.get("password") ?? ""),
  };
}

export async function signUp(
  _: FormState,
  formData: FormData,
): Promise<FormState> {
  const { email, password } = credentials(formData);
  const supabase = await createClient();
  const { error } = await supabase.auth.signUp({
    email,
    password,
    options: { emailRedirectTo: `${await origin()}/auth/callback` },
  });
  if (error) return { error: error.message };
  redirect("/verify-email");
}

export async function logIn(
  _: FormState,
  formData: FormData,
): Promise<FormState> {
  const { email, password } = credentials(formData);
  const supabase = await createClient();
  const { error } = await supabase.auth.signInWithPassword({ email, password });
  if (error) {
    return {
      error:
        error.code === "email_not_confirmed"
          ? "Verify your email first. Check your inbox for the link."
          : "Wrong email or password.",
    };
  }
  redirect("/session");
}

export async function logOut() {
  const supabase = await createClient();
  await supabase.auth.signOut();
  redirect("/");
}

export async function startSession() {
  const supabase = await createClient();
  const { data: auth } = await supabase.auth.getUser();
  if (!auth.user) redirect("/login");

  const { data, error } = await supabase
    .from("sessions")
    .insert({
      owner_id: auth.user.id,
      exam_definition_ref: EXAM_DEFINITION_REF,
      mode: "mock",
      medium: "text",
    })
    .select("id")
    .single();
  if (error) throw new Error(`Could not start a Session: ${error.message}`);
  redirect(`/session/${data.id}`);
}
