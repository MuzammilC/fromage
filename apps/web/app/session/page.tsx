import { Suspense } from "react";
import { logOut, startSession } from "../actions";
import { createClient } from "@/lib/supabase/server";

async function Account() {
  const supabase = await createClient();
  const { data } = await supabase.auth.getUser();
  return <p>Signed in as {data.user?.email}</p>;
}

export default function StartSessionPage() {
  return (
    <>
      <h1>Ready when you are</h1>
      <Suspense>
        <Account />
      </Suspense>
      <form action={startSession}>
        <button type="submit">Start Session</button>
      </form>
      <form action={logOut}>
        <button type="submit" className="link">
          Log out
        </button>
      </form>
    </>
  );
}
