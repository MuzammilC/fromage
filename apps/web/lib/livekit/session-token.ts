const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export type TokenDeps = {
  getUser: () => Promise<{ id: string } | null>;
  /** Must only return a Session the given user owns. */
  findOwnedSession: (
    sessionId: string,
    userId: string,
  ) => Promise<{ id: string; status: string } | null>;
  mintToken: (grant: { identity: string; room: string }) => Promise<string>;
};

export type TokenResult =
  | { ok: true; token: string; room: string }
  | { ok: false; status: 400 | 401 | 404 | 409; error: string };

export function roomNameFor(sessionId: string): string {
  return `session-${sessionId}`;
}

export async function issueSessionToken(
  deps: TokenDeps,
  sessionId: unknown,
): Promise<TokenResult> {
  const user = await deps.getUser();
  if (!user) return { ok: false, status: 401, error: "Not logged in" };

  if (typeof sessionId !== "string" || !UUID.test(sessionId)) {
    return { ok: false, status: 400, error: "Invalid Session id" };
  }

  const session = await deps.findOwnedSession(sessionId, user.id);
  if (!session) return { ok: false, status: 404, error: "Session not found" };
  if (session.status !== "in_progress") {
    return { ok: false, status: 409, error: "Session has ended" };
  }

  const room = roomNameFor(session.id);
  const token = await deps.mintToken({ identity: user.id, room });
  return { ok: true, token, room };
}
