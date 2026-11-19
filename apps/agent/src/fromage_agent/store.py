"""Supabase adapter (service role) for transcript turns and Session cost."""

import os
from datetime import datetime

from supabase import AsyncClient, acreate_client


async def create_store() -> "SupabaseStore":
    client = await acreate_client(
        os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    )
    return SupabaseStore(client)


class SupabaseStore:
    def __init__(self, client: AsyncClient) -> None:
        self._client = client

    async def next_seq(self, session_id: str) -> int:
        res = (
            await self._client.table("transcript_turns")
            .select("seq")
            .eq("session_id", session_id)
            .order("seq", desc=True)
            .limit(1)
            .execute()
        )
        return res.data[0]["seq"] + 1 if res.data else 0

    async def add_turn(
        self,
        session_id: str,
        seq: int,
        speaker: str,
        text: str,
        started_at: datetime,
        ended_at: datetime | None,
    ) -> None:
        await (
            self._client.table("transcript_turns")
            .insert(
                {
                    "session_id": session_id,
                    "seq": seq,
                    "speaker": speaker,
                    "text": text,
                    "started_at": started_at.isoformat(),
                    "ended_at": ended_at.isoformat() if ended_at else None,
                }
            )
            .execute()
        )

    async def add_cost(self, session_id: str, usd: float, breakdown: dict[str, float]) -> None:
        await self._client.rpc(
            "add_session_cost",
            {"p_session_id": session_id, "p_usd": usd, "p_breakdown": breakdown},
        ).execute()
