"""Effects the engine asks the caller to carry out.

Only `AskExaminer` carries Examiner-only Data. Every other effect is safe to show the Candidate.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal


class Phase(Enum):
    DRAW = "draw"
    PREP = "prep"
    PART = "part"
    ENDED = "ended"


@dataclass(frozen=True)
class DrawCard:
    """What the Candidate sees of one Item in a Draw: Candidate-facing fields only."""

    item_id: str
    candidate_brief: str


@dataclass(frozen=True)
class PhaseChanged:
    phase: Phase
    part: str | None
    started_at: float
    deadline: float | None


@dataclass(frozen=True)
class ShowDraw:
    part: str
    cards: tuple[DrawCard, ...]


@dataclass(frozen=True)
class SayFixedLine:
    """A scripted French line. It is spoken as written, never rewritten by the LLM."""

    text: str


@dataclass(frozen=True)
class WrapUpAllowed:
    """The Part has reached its minimum time, so the Examiner may wrap up."""

    part: str


@dataclass(frozen=True)
class ExaminerItem:
    """The current Part's Item as the Examiner sees it, Examiner-only Data included."""

    item_id: str
    type: str
    questions: tuple[str, ...] = ()
    candidate_brief: str | None = None
    suggested_angles: tuple[str, ...] = ()
    examiner_role: str | None = None
    examiner_only_data: dict[str, Any] | None = None
    expected_speech_acts: tuple[str, ...] = ()
    register: str | None = None


AskReason = Literal["opening", "candidate_turn", "follow_up"]


@dataclass(frozen=True)
class AskExaminer:
    """Ask the Examiner for a reply, with the only context it may see."""

    part: str
    reason: AskReason
    item: ExaminerItem | None
    candidate_text: str | None
    may_wrap_up: bool
    follow_up_number: int | None = None


@dataclass(frozen=True)
class SessionEnded:
    reason: Literal["completed"]


Effect = PhaseChanged | ShowDraw | SayFixedLine | WrapUpAllowed | AskExaminer | SessionEnded
