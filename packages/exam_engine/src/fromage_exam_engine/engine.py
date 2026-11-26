"""The Session state machine (ADR-0003). Pure: no I/O, no LLM, no wall clock.

The caller builds an `ExamEngine`, calls `start`, then feeds it events with `handle`. Every call
returns the effects to carry out. The caller sends a `Tick` whenever `next_deadline` is reached,
but it may also send a late one: the engine then replays the deadlines it missed, in order, each
at its own time, so a late Tick never shifts a timer.

The order of a Session is: Draws, then Prep Time (one period after another), then the Parts in the
order of the Exam Definition.
"""

from __future__ import annotations

import copy
import random
from dataclasses import dataclass
from enum import Enum, IntEnum

from fromage_exam_definition import ExamDefinition, Item

from . import lines
from .effects import (
    AskExaminer,
    AskReason,
    DrawCard,
    Effect,
    ExaminerItem,
    Phase,
    PhaseChanged,
    SayFixedLine,
    SessionEnded,
    ShowDraw,
    WrapUpAllowed,
)
from .events import (
    CandidateActivity,
    CandidateDone,
    CandidateTurn,
    ChoseItem,
    Event,
    Ready,
    Tick,
)


class EngineError(ValueError):
    """The engine was set up, or called, in a way it cannot honour."""


@dataclass(frozen=True)
class EngineConfig:
    max_follow_ups: int = 3
    """Follow-up questions after a monologue (research doc §A.2: two or three)."""
    listening_share: float = 0.75
    """The share of a listen-only Part's maximum time given to the Candidate's monologue.
    The rest is left for the follow-up questions."""

    def __post_init__(self) -> None:
        if self.max_follow_ups < 0:
            raise EngineError(f"max_follow_ups must be 0 or more, got {self.max_follow_ups}")
        if not 0 < self.listening_share < 1:
            raise EngineError(
                f"listening_share must be between 0 and 1, got {self.listening_share}"
            )


class _Stage(Enum):
    INTERACTIVE = "interactive"
    LISTENING = "listening"
    FOLLOW_UP = "follow_up"


class _Deadline(IntEnum):
    # The value is the order in which deadlines due at the same time are fired.
    PREP_END = 0
    WRAP_UP = 1
    LISTENING_END = 2
    PART_END = 3


class ExamEngine:
    def __init__(
        self,
        definition: ExamDefinition,
        items: list[Item],
        seed: int | str,
        config: EngineConfig | None = None,
    ) -> None:
        self._definition = definition
        self._config = config or EngineConfig()
        self._parts = list(definition.parts)
        self._preps = list(definition.prep_periods or [])
        self._items: dict[str, Item] = {}
        self._draws: dict[str, tuple[str, ...]] = {}
        self._chosen: dict[str, str] = {}
        self._pick_items(items, seed)

        self._phase = Phase.DRAW
        self._now = 0.0
        self._started = False
        self._last_activity_at: float | None = None

        self._prep_index = 0
        self._prep_started_at = 0.0
        self._part_index = -1
        self._part_started_at = 0.0
        self._stage = _Stage.INTERACTIVE
        self._wrap_up_allowed = False
        self._follow_ups_asked = 0

    # --- reading the state ---

    @property
    def phase(self) -> Phase:
        return self._phase

    @property
    def current_part(self) -> str | None:
        return self._parts[self._part_index].key if self._phase is Phase.PART else None

    @property
    def draws(self) -> dict[str, tuple[str, ...]]:
        """The Item ids offered for each Part that has a Draw."""
        return dict(self._draws)

    @property
    def chosen(self) -> dict[str, str]:
        """The Item id the Session uses for each Part so far."""
        return dict(self._chosen)

    @property
    def last_candidate_activity_at(self) -> float | None:
        """When the Candidate last typed or sent a turn. Relance measures silence from this."""
        return self._last_activity_at

    @property
    def next_deadline(self) -> float | None:
        """When the engine next needs a Tick, or None if nothing is waiting on time."""
        deadline = self._earliest_deadline()
        return deadline[0] if deadline else None

    # --- driving the engine ---

    def start(self, at: float) -> list[Effect]:
        if self._started:
            raise EngineError("The engine is already started")
        self._started = True
        self._now = at
        if self._draws:
            self._phase = Phase.DRAW
            effects: list[Effect] = [
                PhaseChanged(Phase.DRAW, None, at, None),
                SayFixedLine(lines.DRAW_INTRO),
            ]
            effects += [ShowDraw(part, self._cards(ids)) for part, ids in self._draws.items()]
            return effects
        return self._begin_prep_or_parts()

    def handle(self, event: Event) -> list[Effect]:
        if not self._started:
            raise EngineError("Call start() before handling events")
        effects = self._advance(event.at)
        if self._phase is Phase.ENDED:
            return effects

        match event:
            case ChoseItem():
                effects += self._on_chose_item(event)
            case Ready():
                if self._phase is Phase.PREP:
                    effects += self._end_prep()
            case CandidateActivity():
                self._last_activity_at = event.at
            case CandidateDone():
                if self._phase is Phase.PART and self._stage is _Stage.LISTENING:
                    effects += self._begin_follow_ups()
            case CandidateTurn():
                self._last_activity_at = event.at
                effects += self._on_candidate_turn(event)
            case Tick():
                pass
        return effects

    # --- setting up the Items ---

    def _pick_items(self, items: list[Item], seed: int | str) -> None:
        ref = f"{self._definition.id}@{self._definition.version}"
        for part in self._parts:
            if part.item_type is None:
                if part.draw_count is not None:
                    raise EngineError(f"Part {part.key!r} has a draw_count but no item_type")
                continue
            candidates = sorted(
                (
                    item
                    for item in items
                    if item.root.status.value == "reviewed"
                    and item.root.exam_definition.root == ref
                    and item.root.part_key.root == part.key
                    and item.root.type == part.item_type.value
                ),
                key=lambda item: item.root.id.root,
            )
            needed = part.draw_count or 1
            if len(candidates) < needed:
                raise EngineError(
                    f"Part {part.key!r} needs {needed} reviewed Item(s) of type "
                    f"{part.item_type.value!r}, found {len(candidates)}"
                )
            # One generator per Part, so adding a Part never changes the Draws of the others.
            rng = random.Random(f"{type(seed).__name__}:{seed}:{part.key}")
            if part.draw_count is None:
                picked = rng.choice(candidates)
                self._items[picked.root.id.root] = picked
                self._chosen[part.key] = picked.root.id.root
                continue
            if part.item_type.value == "question_bank":
                raise EngineError(f"Part {part.key!r}: a question bank cannot be offered as a Draw")
            offered = rng.sample(candidates, part.draw_count)
            for item in offered:
                self._items[item.root.id.root] = item
            self._draws[part.key] = tuple(item.root.id.root for item in offered)

    def _cards(self, item_ids: tuple[str, ...]) -> tuple[DrawCard, ...]:
        # Candidate-facing fields only: the brief, never Examiner-only Data.
        return tuple(
            DrawCard(item_id, self._items[item_id].root.candidate_brief)  # type: ignore[union-attr]
            for item_id in item_ids
        )

    # --- time ---

    def _earliest_deadline(self) -> tuple[float, _Deadline] | None:
        if self._phase is Phase.PREP:
            return (
                self._prep_started_at + self._preps[self._prep_index].time_seconds,
                _Deadline.PREP_END,
            )
        if self._phase is not Phase.PART:
            return None
        part = self._parts[self._part_index]
        due: list[tuple[float, _Deadline]] = [
            (self._part_started_at + part.target_duration_seconds.max, _Deadline.PART_END)
        ]
        if not self._wrap_up_allowed:
            due.append(
                (self._part_started_at + part.target_duration_seconds.min, _Deadline.WRAP_UP)
            )
        if self._stage is _Stage.LISTENING:
            listening = round(part.target_duration_seconds.max * self._config.listening_share)
            due.append((self._part_started_at + listening, _Deadline.LISTENING_END))
        return min(due)

    def _advance(self, at: float) -> list[Effect]:
        if at < self._now:
            raise EngineError(f"Time went backwards: {at} is before {self._now}")
        effects: list[Effect] = []
        while (deadline := self._earliest_deadline()) is not None and deadline[0] <= at:
            self._now = deadline[0]
            effects += self._fire(deadline[1])
        self._now = at
        # A late Tick replays Parts that are already over: the Examiner must not speak for them.
        current = self.current_part
        return [e for e in effects if not (isinstance(e, AskExaminer) and e.part != current)]

    def _fire(self, deadline: _Deadline) -> list[Effect]:
        match deadline:
            case _Deadline.PREP_END:
                return self._end_prep()
            case _Deadline.WRAP_UP:
                self._wrap_up_allowed = True
                return [WrapUpAllowed(self._parts[self._part_index].key)]
            case _Deadline.LISTENING_END:
                return self._begin_follow_ups()
            case _Deadline.PART_END:
                return self._end_part()

    # --- Draws and Prep Time ---

    def _on_chose_item(self, event: ChoseItem) -> list[Effect]:
        if self._phase is not Phase.DRAW:
            return []
        offered = self._draws.get(event.part)
        if offered is None:
            raise EngineError(f"Part {event.part!r} has no Draw")
        if event.item_id not in offered:
            raise EngineError(f"Item {event.item_id!r} is not in the Draw for {event.part!r}")
        self._chosen[event.part] = event.item_id
        if all(part in self._chosen for part in self._draws):
            return self._begin_prep_or_parts()
        return []

    def _begin_prep_or_parts(self) -> list[Effect]:
        if self._prep_index < len(self._preps):
            return self._begin_prep()
        return self._begin_part(0)

    def _begin_prep(self) -> list[Effect]:
        self._phase = Phase.PREP
        self._prep_started_at = self._now
        seconds = self._preps[self._prep_index].time_seconds
        return [
            PhaseChanged(Phase.PREP, None, self._now, self._now + seconds),
            SayFixedLine(lines.prep_started(seconds)),
        ]

    def _end_prep(self) -> list[Effect]:
        self._prep_index += 1
        if self._prep_index < len(self._preps):
            return self._begin_prep()
        return [SayFixedLine(lines.PREP_ENDED), *self._begin_part(0)]

    # --- Parts ---

    def _begin_part(self, index: int) -> list[Effect]:
        self._part_index = index
        part = self._parts[index]
        self._phase = Phase.PART
        self._part_started_at = self._now
        self._wrap_up_allowed = False
        self._follow_ups_asked = 0
        self._stage = (
            _Stage.LISTENING if part.turn_mode.value == "listen_only" else _Stage.INTERACTIVE
        )
        effects: list[Effect] = [
            PhaseChanged(
                Phase.PART, part.key, self._now, self._now + part.target_duration_seconds.max
            ),
            SayFixedLine(lines.part_announcement(part)),
        ]
        if self._stage is _Stage.INTERACTIVE:
            effects.append(self._ask("opening"))
        return effects

    def _end_part(self) -> list[Effect]:
        if self._part_index + 1 < len(self._parts):
            return self._begin_part(self._part_index + 1)
        self._phase = Phase.ENDED
        return [
            SayFixedLine(lines.SESSION_ENDED),
            PhaseChanged(Phase.ENDED, None, self._now, None),
            SessionEnded("completed"),
        ]

    def _on_candidate_turn(self, event: CandidateTurn) -> list[Effect]:
        if self._phase is not Phase.PART or not event.text.strip():
            return []
        match self._stage:
            case _Stage.INTERACTIVE:
                return [self._ask("candidate_turn", event.text)]
            case _Stage.LISTENING:
                # The Examiner only listens during a monologue.
                return []
            case _Stage.FOLLOW_UP:
                if self._follow_ups_asked >= self._config.max_follow_ups:
                    return self._end_part()
                return self._ask_follow_up()

    def _begin_follow_ups(self) -> list[Effect]:
        self._stage = _Stage.FOLLOW_UP
        if self._config.max_follow_ups < 1:
            return self._end_part()
        return self._ask_follow_up()

    def _ask_follow_up(self) -> list[Effect]:
        self._follow_ups_asked += 1
        return [self._ask("follow_up", follow_up_number=self._follow_ups_asked)]

    # --- the Examiner's context ---

    def _ask(
        self,
        reason: AskReason,
        candidate_text: str | None = None,
        follow_up_number: int | None = None,
    ) -> AskExaminer:
        part = self._parts[self._part_index]
        item_id = self._chosen.get(part.key)
        return AskExaminer(
            part=part.key,
            reason=reason,
            item=self._examiner_item(self._items[item_id]) if item_id else None,
            candidate_text=candidate_text,
            may_wrap_up=self._wrap_up_allowed,
            follow_up_number=follow_up_number,
        )

    @staticmethod
    def _examiner_item(item: Item) -> ExaminerItem:
        variant = item.root
        match variant.type:
            case "question_bank":
                return ExaminerItem(
                    variant.id.root,
                    variant.type,
                    questions=tuple(q.root for q in variant.questions),
                )
            case "monologue_subject":
                return ExaminerItem(
                    variant.id.root,
                    variant.type,
                    candidate_brief=variant.candidate_brief,
                    suggested_angles=tuple(a.root for a in variant.suggested_angles),
                )
            case _:
                return ExaminerItem(
                    variant.id.root,
                    variant.type,
                    candidate_brief=variant.candidate_brief,
                    examiner_role=variant.examiner_role,
                    examiner_only_data=copy.deepcopy(variant.examiner_only_data),
                    expected_speech_acts=tuple(s.root for s in variant.expected_speech_acts),
                    register=variant.register_.value,
                )
