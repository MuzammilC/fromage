import Link from "next/link";

export default function Home() {
  return (
    <>
      <h1>Practise your French speaking exam</h1>
      <p>
        Original mock exams in the DELF A2 format, with an AI examiner and an
        estimated score.
      </p>
      <p className="row">
        <Link href="/signup">Sign up</Link>
        <Link href="/login">Log in</Link>
      </p>
    </>
  );
}
