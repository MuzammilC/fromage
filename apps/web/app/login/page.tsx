import Link from "next/link";
import { Suspense } from "react";
import { logIn } from "../actions";
import { AuthForm } from "../auth-form";

async function VerificationError({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>;
}) {
  const { error } = await searchParams;
  return error === "verification-failed" ? (
    <p role="alert">
      We could not sign you in from that link. If you already verified your
      email, log in below.
    </p>
  ) : null;
}

export default function LoginPage(props: PageProps<"/login">) {
  return (
    <>
      <h1>Log in</h1>
      <Suspense>
        <VerificationError searchParams={props.searchParams} />
      </Suspense>
      <AuthForm action={logIn} submitLabel="Log in" />
      <p>
        New here? <Link href="/signup">Sign up</Link>
      </p>
    </>
  );
}
