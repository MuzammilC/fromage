import Link from "next/link";

export default function VerifyEmailPage() {
  return (
    <>
      <h1>Check your email</h1>
      <p>
        We sent you a link to verify your address. Open it, then{" "}
        <Link href="/login">log in</Link>.
      </p>
    </>
  );
}
