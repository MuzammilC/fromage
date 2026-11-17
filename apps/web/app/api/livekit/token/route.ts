import { AccessToken } from "livekit-server-sdk";
import { NextResponse } from "next/server";
import { issueSessionToken } from "@/lib/livekit/session-token";
import { createClient } from "@/lib/supabase/server";

export async function POST(request: Request) {
  const body = await request.json().catch(() => null);
  const supabase = await createClient();

  let result;
  try {
    result = await issueSessionToken(
      {
        getUser: async () => {
          const { data } = await supabase.auth.getUser();
          return data.user;
        },
        // Row-level security already limits this to the caller's own Sessions;
        // the owner filter keeps the intent explicit.
        findOwnedSession: async (sessionId, userId) => {
          const { data, error } = await supabase
            .from("sessions")
            .select("id, status")
            .eq("id", sessionId)
            .eq("owner_id", userId)
            .maybeSingle();
          if (error) throw error;
          return data;
        },
        mintToken: async ({ identity, room }) => {
          const apiKey = process.env.LIVEKIT_API_KEY;
          const apiSecret = process.env.LIVEKIT_API_SECRET;
          if (!apiKey || !apiSecret)
            throw new Error("LiveKit is not configured");
          const token = new AccessToken(apiKey, apiSecret, {
            identity,
            ttl: "1h",
          });
          token.addGrant({
            roomJoin: true,
            room,
            canPublish: false,
            canPublishData: true,
            canSubscribe: true,
          });
          return token.toJwt();
        },
      },
      body?.sessionId,
    );
  } catch (error) {
    console.error("LiveKit token request failed", error);
    return NextResponse.json(
      { error: "Could not issue a token" },
      { status: 500 },
    );
  }

  if (!result.ok) {
    return NextResponse.json(
      { error: result.error },
      { status: result.status },
    );
  }
  return NextResponse.json({ token: result.token, room: result.room });
}
