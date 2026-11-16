import { notFound } from "next/navigation";
import { Suspense } from "react";
import { createClient } from "@/lib/supabase/server";
import { Chat } from "./chat";

async function SessionChat({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const supabase = await createClient();
  // Row-level security hides other Users' Sessions, so a stranger gets a 404.
  const { data } = await supabase
    .from("sessions")
    .select("id, status")
    .eq("id", id)
    .maybeSingle();
  if (!data) notFound();
  return <Chat sessionId={data.id} />;
}

export default function SessionPage(props: PageProps<"/session/[id]">) {
  return (
    <>
      <h1>Session</h1>
      <Suspense fallback={<p>Loading…</p>}>
        <SessionChat params={props.params} />
      </Suspense>
    </>
  );
}
