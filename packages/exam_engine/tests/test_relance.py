import pytest
from fromage_exam_engine import (
    AskExaminer,
    CandidateActivity,
    CandidateTurn,
    EngineConfig,
    EngineError,
    ExaminerDone,
    Medium,
    PhaseChanged,
    QuestionUnanswered,
    RelanceThresholds,
    RepeatQuestion,
    SayFixedLine,
    SimplifyQuestion,
    Tick,
    WrapUpAllowed,
)
from test_engine import P1, P2, P3, at_part, choose_all, engine_for, of_type


def live(a2, items, part, config=None):
    """An engine at the start of `part` with the default Relance thresholds."""
    engine, t = at_part(a2, items, part, config=config, relance=None)
    engine.handle(ExaminerDone(t))  # the Examiner has said its opening line
    return engine, t


# Part 1 starts at 600 and lasts 90 s. Default thresholds: 6, 9, 12, 15 s of silence.


def kinds(effects):
    return [type(e).__name__ for e in effects]


def test_step_1_repeats_the_question_after_the_first_threshold(a2, items):
    engine, t = live(a2, items, P1)
    assert engine.handle(Tick(t + 5.9)) == []
    assert engine.next_deadline == t + 6
    assert engine.handle(Tick(t + 6)) == [RepeatQuestion(P1)]


def test_each_step_is_its_own_effect_in_order(a2, items):
    engine, t = live(a2, items, P1)
    assert engine.handle(Tick(t + 9)) == [RepeatQuestion(P1), SimplifyQuestion(P1)]
    step3 = engine.handle(Tick(t + 12))
    assert kinds(step3) == ["AskExaminer"]
    assert step3[0].reason == "reformulate"
    assert step3[0].item is not None and step3[0].candidate_text is None


def test_step_4_moves_on_and_records_the_question_as_unanswered(a2, items):
    engine, t = live(a2, items, P1)
    effects = engine.handle(Tick(t + 15))[3:]
    assert effects[:2] == [SayFixedLine("Passons à la question suivante."), QuestionUnanswered(P1)]
    assert isinstance(effects[2], AskExaminer) and effects[2].reason == "next_question"


def test_a_late_tick_replays_every_step_in_order(a2, items):
    engine, t = live(a2, items, P1)
    assert kinds(engine.handle(Tick(t + 20))) == [
        "RepeatQuestion",
        "SimplifyQuestion",
        "AskExaminer",
        "SayFixedLine",
        "QuestionUnanswered",
        "AskExaminer",
    ]


def test_after_moving_on_the_silence_starts_again_for_the_next_question(a2, items):
    engine, t = live(a2, items, P1)
    engine.handle(Tick(t + 15))
    engine.handle(ExaminerDone(t + 15))
    assert engine.next_deadline == t + 15 + 6
    assert engine.handle(Tick(t + 21)) == [RepeatQuestion(P1)]


def test_typing_resets_the_silence_timer(a2, items):
    engine, t = live(a2, items, P1)
    engine.handle(CandidateActivity(t + 5))
    assert engine.handle(Tick(t + 10)) == []
    assert engine.handle(Tick(t + 11)) == [RepeatQuestion(P1)]


def test_typing_does_not_undo_a_step_already_taken(a2, items):
    engine, t = live(a2, items, P1)
    engine.handle(Tick(t + 6))
    engine.handle(CandidateActivity(t + 7))
    # The next step is "simpler", counted from the typing.
    assert engine.next_deadline == t + 7 + 9
    assert engine.handle(Tick(t + 16)) == [SimplifyQuestion(P1)]


def test_a_candidate_turn_starts_a_new_question_from_the_first_step(a2, items):
    engine, t = live(a2, items, P1)
    engine.handle(Tick(t + 9))
    asked = engine.handle(CandidateTurn(t + 10, "Je m'appelle Ana."))
    assert asked[0].reason == "candidate_turn"
    engine.handle(ExaminerDone(t + 10))
    assert engine.handle(Tick(t + 15)) == []
    assert engine.handle(Tick(t + 16)) == [RepeatQuestion(P1)]


def test_silence_is_not_counted_while_the_examiner_is_still_asking(a2, items):
    engine, t = live(a2, items, P1)
    engine, t = live(a2, items, P1)
    engine.handle(CandidateTurn(t + 10, "Je m'appelle Ana."))
    assert engine.next_deadline == t + 90  # nothing but the Part end: the Examiner is replying
    assert engine.handle(Tick(t + 40)) == []
    engine.handle(ExaminerDone(t + 40))
    assert engine.next_deadline == t + 46


def test_a_blank_message_does_not_reset_the_silence_timer(a2, items):
    engine, t = live(a2, items, P1)
    engine.handle(CandidateTurn(t + 5, "   "))
    assert engine.handle(Tick(t + 6)) == [RepeatQuestion(P1)]


def test_default_relance_does_not_disturb_the_wrap_up_or_the_part_changes(a2, items):
    engine, t = live(a2, items, P1)
    effects, now = [], t
    while now + 4 < t + 90:
        now += 4  # the Candidate answers every 4 s, so there is never enough silence
        effects += engine.handle(CandidateTurn(now, "Oui."))
        engine.handle(ExaminerDone(now))
    effects += engine.handle(Tick(t + 90))
    assert not [e for e in effects if isinstance(e, (RepeatQuestion, QuestionUnanswered))]
    assert len([e for e in effects if isinstance(e, WrapUpAllowed)]) == 1
    assert [e.part for e in effects if isinstance(e, PhaseChanged)] == [P2]


def test_no_relance_during_the_listen_only_stretch(a2, items):
    engine, t = live(a2, items, P2)
    assert engine.handle(Tick(t + 29)) == []
    assert engine.handle(CandidateActivity(t + 29)) == []


def test_long_silence_ends_the_listening_stretch_and_asks_follow_ups(a2, items):
    engine, t = live(a2, items, P2)
    effects = engine.handle(Tick(t + 30))
    assert [e.reason for e in of_type(effects, AskExaminer)] == ["follow_up"]
    assert not [e for e in effects if isinstance(e, RepeatQuestion)]


def test_typing_delays_the_end_of_the_listening_stretch(a2, items):
    engine, t = live(a2, items, P2)
    engine.handle(CandidateActivity(t + 20))
    assert engine.handle(Tick(t + 49)) == []
    assert of_type(engine.handle(Tick(t + 50)), AskExaminer)


def test_relance_applies_to_the_follow_up_questions(a2, items):
    engine, t = live(a2, items, P2)
    engine.handle(Tick(t + 30))  # follow-up 1 asked at t + 30
    engine.handle(ExaminerDone(t + 30))
    assert engine.handle(Tick(t + 36)) == [RepeatQuestion(P2)]


def test_moving_on_in_the_last_follow_up_ends_the_part(a2, items):
    engine, t = live(a2, items, P2, config=EngineConfig(max_follow_ups=1))
    engine.handle(Tick(t + 30))  # follow-up 1, the last one
    engine.handle(ExaminerDone(t + 30))
    effects = engine.handle(Tick(t + 45))
    assert QuestionUnanswered(P2) in effects
    assert [e.part for e in effects if isinstance(e, PhaseChanged)] == [P3]


def test_a_part_that_ends_does_not_get_relance_steps_for_the_next_part(a2, items):
    engine, t = live(a2, items, P1)
    engine.handle(CandidateActivity(t + 85))
    effects = engine.handle(Tick(t + 90))  # Part 1 ends; Part 2 starts and is listen-only
    assert not [e for e in effects if isinstance(e, (RepeatQuestion, QuestionUnanswered))]
    assert engine.next_deadline == t + 90 + 30  # the listening silence, counted from Part 2's start


def test_a_relance_due_at_the_part_end_is_dropped(a2, items):
    engine, t = live(a2, items, P1)
    engine.handle(CandidateActivity(t + 84))
    effects = engine.handle(Tick(t + 90))  # step 1 would be due at t + 90, exactly the end
    assert not [e for e in effects if isinstance(e, RepeatQuestion)]


def test_no_relance_in_prep_time(a2, items):
    engine = engine_for(a2, items, relance=None)
    engine.start(0.0)
    choose_all(engine)
    assert engine.handle(Tick(300.0)) == []


def test_thresholds_are_set_per_medium_without_touching_the_engine(a2, items):
    config = EngineConfig(
        medium=Medium.VOICE,
        relance={
            Medium.TEXT: RelanceThresholds(),
            Medium.VOICE: RelanceThresholds(3, 5, 7, 9, listening_end_after=12),
        },
    )
    engine, t = live(a2, items, P1, config=config)
    assert engine.handle(Tick(t + 3)) == [RepeatQuestion(P1)]
    assert engine.handle(Tick(t + 9))[-1].reason == "next_question"


def test_thresholds_must_be_increasing():
    with pytest.raises(ValueError):
        RelanceThresholds(repeat_after=10, simplify_after=5)


def test_the_config_needs_thresholds_for_its_medium():
    with pytest.raises(EngineError):
        EngineConfig(medium=Medium.VOICE, relance={Medium.TEXT: RelanceThresholds()})
