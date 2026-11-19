"""The echo Examiner: paraphrases each Candidate message back in simple French.

This is the pure core. The LLM, the database and the clock are injected, so it is
tested without any network. Adapters live in `llm.py`, `store.py` and `worker.py`.
"""

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

MODEL = "claude-haiku-5-5"
# USD per token, for prompts up to 100K tokens.
INPUT_USD_PER_TOKEN = 0.10 / 1_000_000
OUTPUT_USD_PER_TOKEN = 0.50 / 1_000_000


@dataclass(frozen=True)
class Usage:
    input_tokens: int
    output_tokens: int


@dataclass(frozen=True)
class Paraphrase:
    text: str
    usage: Usage


def cost_usd(usage: Usage) -> float:
    return usage.input_tokens * INPUT_USD_PER_TOKEN + usage.output_tokens * OUTPUT_USD_PER_TOKEN


class Paraphraser(Protocol):
    async def paraphrase(self, session_id: str, text: str) -> Paraphrase: ...


class TranscriptStore(Protocol):
    async def next_seq(self, session_id: str) -> int: ...

    async def add_turn(
        self,
        session_id: str,
        seq: int,
        speaker: str,
        text: str,
        started_at: datetime,
        ended_at: datetime | None,
    ) -> None: ...

    async def add_cost(self, session_id: str, usd: float, breakdown: dict[str, float]) -> None: ...


class EchoExaminer:
    def __init__(
        self,
        session_id: str,
        paraphraser: Paraphraser,
        store: TranscriptStore,
        clock: Callable[[], datetime],
    ) -> None:
        self._session_id = session_id
        self._paraphraser = paraphraser
        self._store = store
        self._clock = clock
        self._seq: int | None = None
        # Messages are handled one at a time so turns land in order.
        self._lock = asyncio.Lock()

    async def on_candidate_message(self, text: str) -> str | None:
        """Save the Candidate's turn, paraphrase it, save and return the reply."""
        text = text.strip()
        if not text:
            return None
        async with self._lock:
            if self._seq is None:
                self._seq = await self._store.next_seq(self._session_id)

            now = self._clock()
            await self._save("candidate", text, now)

            started = self._clock()
            result = await self._paraphraser.paraphrase(self._session_id, text)
            await self._save("examiner", result.text, started)

            usd = cost_usd(result.usage)
            await self._store.add_cost(self._session_id, usd, {"llm": usd})
            return result.text

    async def _save(self, speaker: str, text: str, started_at: datetime) -> None:
        seq = self._seq
        assert seq is not None
        await self._store.add_turn(self._session_id, seq, speaker, text, started_at, self._clock())
        self._seq = seq + 1
