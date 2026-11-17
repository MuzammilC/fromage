"use client";

import { Room, RoomEvent } from "livekit-client";
import { useEffect, useRef, useState } from "react";

type Message = { from: "you" | "examiner" | "other"; text: string };
const TOPIC = "chat";
const LABELS = {
  you: "You",
  examiner: "Examiner",
  other: "Participant",
} as const;

export function Chat({ sessionId }: { sessionId: string }) {
  const roomRef = useRef<Room | null>(null);
  const [status, setStatus] = useState<"connecting" | "connected" | "error">(
    "connecting",
  );
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState("");

  useEffect(() => {
    const room = new Room();
    roomRef.current = room;
    let cancelled = false;

    room.registerTextStreamHandler(TOPIC, async (reader, participant) => {
      const text = await reader.readAll();
      setMessages((m) => [
        ...m,
        {
          from: room.remoteParticipants.get(participant.identity)?.isAgent
            ? "examiner"
            : "other",
          text,
        },
      ]);
    });
    room.on(RoomEvent.Disconnected, () => !cancelled && setStatus("error"));

    (async () => {
      try {
        const res = await fetch("/api/livekit/token", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ sessionId }),
        });
        if (!res.ok) throw new Error(`token request failed: ${res.status}`);
        const { token } = await res.json();
        const url = process.env.NEXT_PUBLIC_LIVEKIT_URL;
        if (!url) throw new Error("NEXT_PUBLIC_LIVEKIT_URL is not set");
        await room.connect(url, token);
        if (!cancelled) setStatus("connected");
      } catch {
        if (!cancelled) setStatus("error");
      }
    })();

    return () => {
      cancelled = true;
      void room.disconnect();
    };
  }, [sessionId]);

  async function send(e: React.FormEvent) {
    e.preventDefault();
    const text = draft.trim();
    const room = roomRef.current;
    if (!text || !room) return;
    await room.localParticipant.sendText(text, { topic: TOPIC });
    setMessages((m) => [...m, { from: "you", text }]);
    setDraft("");
  }

  return (
    <section aria-label="Chat">
      <p role="status">
        {status === "connecting" && "Connecting…"}
        {status === "connected" && "Connected"}
        {status === "error" && "Could not connect. Reload to try again."}
      </p>
      <ul className="messages">
        {messages.map((m, i) => (
          <li key={i}>
            <strong>{LABELS[m.from]}:</strong> {m.text}
          </li>
        ))}
      </ul>
      <form onSubmit={send} className="row">
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          aria-label="Message"
          disabled={status !== "connected"}
        />
        <button
          type="submit"
          disabled={status !== "connected" || !draft.trim()}
        >
          Send
        </button>
      </form>
    </section>
  );
}
