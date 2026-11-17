"use client";

import { useActionState } from "react";
import type { FormState } from "./actions";

export function AuthForm({
  action,
  submitLabel,
  newPassword,
}: {
  action: (state: FormState, formData: FormData) => Promise<FormState>;
  submitLabel: string;
  newPassword?: boolean;
}) {
  const [state, formAction, pending] = useActionState(action, undefined);
  return (
    <form action={formAction} className="stack">
      <label>
        Email
        <input name="email" type="email" autoComplete="email" required />
      </label>
      <label>
        Password
        <input
          name="password"
          type="password"
          autoComplete={newPassword ? "new-password" : "current-password"}
          minLength={newPassword ? 10 : undefined}
          required
        />
      </label>
      {newPassword && (
        <p className="hint">
          At least 10 characters, with lower case, upper case and digits.
        </p>
      )}
      {state?.error && <p role="alert">{state.error}</p>}
      <button type="submit" disabled={pending}>
        {pending ? "Please wait…" : submitLabel}
      </button>
    </form>
  );
}
