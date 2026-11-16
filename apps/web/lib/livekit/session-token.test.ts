import { describe, expect, it, vi } from "vitest";
import { issueSessionToken, roomNameFor } from "./session-token";

const USER = { id: "user-1" };
const SESSION = {
  id: "11111111-1111-4111-8111-111111111111",
  status: "in_progress",
};

function deps(overrides = {}) {
  return {
    getUser: vi.fn().mockResolvedValue(USER),
    findOwnedSession: vi.fn().mockResolvedValue(SESSION),
    mintToken: vi.fn().mockResolvedValue("jwt"),
    ...overrides,
  };
}

describe("issueSessionToken", () => {
  it("refuses a request with no logged-in user", async () => {
    const d = deps({ getUser: vi.fn().mockResolvedValue(null) });
    const result = await issueSessionToken(d, SESSION.id);
    expect(result).toEqual({ ok: false, status: 401, error: "Not logged in" });
    expect(d.mintToken).not.toHaveBeenCalled();
  });

  it("refuses a Session the user does not own (or that does not exist)", async () => {
    const d = deps({ findOwnedSession: vi.fn().mockResolvedValue(null) });
    const result = await issueSessionToken(d, SESSION.id);
    expect(result).toEqual({
      ok: false,
      status: 404,
      error: "Session not found",
    });
    expect(d.mintToken).not.toHaveBeenCalled();
  });

  it("refuses a Session id that is not a UUID without touching the database", async () => {
    const d = deps();
    const result = await issueSessionToken(d, "not-a-uuid");
    expect(result).toMatchObject({ ok: false, status: 400 });
    expect(d.findOwnedSession).not.toHaveBeenCalled();
  });

  it("refuses a Session that has already ended", async () => {
    const d = deps({
      findOwnedSession: vi
        .fn()
        .mockResolvedValue({ ...SESSION, status: "abandoned" }),
    });
    const result = await issueSessionToken(d, SESSION.id);
    expect(result).toMatchObject({ ok: false, status: 409 });
    expect(d.mintToken).not.toHaveBeenCalled();
  });

  it("mints a token for the owner, scoped to that Session's room", async () => {
    const d = deps();
    const result = await issueSessionToken(d, SESSION.id);
    expect(result).toEqual({
      ok: true,
      token: "jwt",
      room: roomNameFor(SESSION.id),
    });
    expect(d.findOwnedSession).toHaveBeenCalledWith(SESSION.id, USER.id);
    expect(d.mintToken).toHaveBeenCalledWith({
      identity: USER.id,
      room: roomNameFor(SESSION.id),
    });
  });
});
