import Link from "next/link";
import { signUp } from "../actions";
import { AuthForm } from "../auth-form";

export default function SignUpPage() {
  return (
    <>
      <h1>Sign up</h1>
      <AuthForm action={signUp} submitLabel="Create account" newPassword />
      <p>
        Already have an account? <Link href="/login">Log in</Link>
      </p>
    </>
  );
}
