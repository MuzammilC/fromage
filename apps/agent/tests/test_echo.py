from datetime import UTC, datetime

import pytest
from fromage_agent.echo import (
    EchoExaminer,
    Paraphrase,
    ParaphraseError,
    SeqConflict,
    Usage,
    cost_usd,
)


class FakeStore:
    def __init__(self, existing_turns=0, conflicts=0, cost_fails=False):
        self.turns = []
        self.costs = []
        self._existing = existing_turns
        self._conflicts = conflicts
        self._cost_fails = cost_fails

    async def next_seq(self, session_id):
        return self._existing

    async def add_turn(self, session_id, seq, speaker, text, started_at, ended_at):
        if self._conflicts:
            self._conflicts -= 1
            self._existing += 1  # the other writer's turn
            raise SeqConflict
        self.turns.append((session_id, seq, speaker, text))

    async def add_cost(self, session_id, usd, breakdown):
        if self._cost_fails:
            raise RuntimeError("db down")
        self.costs.append((session_id, usd, breakdown))


class FakeParaphraser:
    def __init__(self, fail=False, empty=False):
        self.calls = []
        self.fail = fail
        self.empty = empty

    async def paraphrase(self, session_id, text):
        self.calls.append(text)
        if self.fail:
            raise RuntimeError("llm down")
        if self.empty:
            raise ParaphraseError("empty", Usage(1000, 200))
        return Paraphrase(text=f"Vous dites : {text}", usage=Usage(1000, 200))


def clock():
    return datetime(2026, 1, 1, tzinfo=UTC)


def make(store=None, paraphraser=None):
    store = store or FakeStore()
    paraphraser = paraphraser or FakeParaphraser()
    return EchoExaminer("s1", paraphraser, store, clock), store, paraphraser


def test_cost_usd_uses_haiku_rates():
    # $0.10 / 1M input, $0.50 / 1M output
    assert cost_usd(Usage(1_000_000, 1_000_000)) == pytest.approx(0.60)
    assert cost_usd(Usage(0, 0)) == 0


async def test_replies_with_the_paraphrase():
    ex, _, _ = make()
    assert await ex.on_candidate_message("Je mange du pain") == "Vous dites : Je mange du pain"


async def test_saves_both_turns_in_order():
    ex, store, _ = make()
    await ex.on_candidate_message("Bonjour")
    assert store.turns == [
        ("s1", 0, "candidate", "Bonjour"),
        ("s1", 1, "examiner", "Vous dites : Bonjour"),
    ]


async def test_seq_continues_across_messages_and_after_restart():
    ex, store, _ = make(FakeStore(existing_turns=4))
    await ex.on_candidate_message("a")
    await ex.on_candidate_message("b")
    assert [t[1] for t in store.turns] == [4, 5, 6, 7]


async def test_adds_cost_to_the_session():
    ex, store, _ = make()
    await ex.on_candidate_message("Bonjour")
    [(sid, usd, breakdown)] = store.costs
    assert sid == "s1"
    assert usd == pytest.approx(cost_usd(Usage(1000, 200)))
    assert breakdown == {"llm": usd}


async def test_candidate_turn_is_saved_even_if_the_llm_fails():
    ex, store, _ = make(paraphraser=FakeParaphraser(fail=True))
    with pytest.raises(RuntimeError):
        await ex.on_candidate_message("Bonjour")
    assert store.turns == [("s1", 0, "candidate", "Bonjour")]
    assert store.costs == []


async def test_reply_is_returned_even_if_recording_cost_fails():
    ex, store, _ = make(FakeStore(cost_fails=True))
    assert await ex.on_candidate_message("Bonjour") == "Vous dites : Bonjour"
    assert len(store.turns) == 2


async def test_cost_is_recorded_when_the_llm_reply_is_unusable():
    ex, store, _ = make(paraphraser=FakeParaphraser(empty=True))
    with pytest.raises(ParaphraseError):
        await ex.on_candidate_message("Bonjour")
    [(_, usd, _)] = store.costs
    assert usd == pytest.approx(cost_usd(Usage(1000, 200)))


async def test_retries_with_a_fresh_seq_when_another_writer_took_it():
    ex, store, _ = make(FakeStore(existing_turns=2, conflicts=1))
    await ex.on_candidate_message("Bonjour")
    assert [t[1] for t in store.turns] == [3, 4]


async def test_ignores_blank_messages():
    ex, store, p = make()
    assert await ex.on_candidate_message("   ") is None
    assert store.turns == [] and p.calls == []


def test_session_id_comes_from_the_room_name():
    from fromage_agent.worker import session_id_from_room

    assert session_id_from_room("session-123") == "123"
    with pytest.raises(ValueError):
        session_id_from_room("other-room")
