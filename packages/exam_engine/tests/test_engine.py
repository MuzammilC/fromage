import pytest
from fromage_exam_engine import (
    AskExaminer,
    CandidateActivity,
    CandidateDone,
    CandidateTurn,
    ChoseItem,
    EngineConfig,
    EngineError,
    ExamEngine,
    Phase,
    PhaseChanged,
    Ready,
    SayFixedLine,
    SessionEnded,
    ShowDraw,
    Tick,
    WrapUpAllowed,
)

P1, P2, P3 = "entretien_dirige", "monologue_suivi", "exercice_en_interaction"


def engine_for(a2, items, seed=1, config=None):
    return ExamEngine(a2, items, seed=seed, config=config)


def of_type(effects, kind):
    return [e for e in effects if isinstance(e, kind)]


def choose_all(engine, at=0.0):
    effects = []
    for part, ids in engine.draws.items():
        effects += engine.handle(ChoseItem(at, part, ids[0]))
    return effects


def at_part(a2, items, part, seed=1):
    """An engine at the start of `part`, with the Candidate having chosen the first card of each Draw."""
    engine = engine_for(a2, items, seed)
    engine.start(0.0)
    choose_all(engine)
    engine.handle(Tick(600.0))  # Prep Time ends: Part 1 starts at 600
    if part == P1:
        return engine, 600.0
    engine.handle(Tick(690.0))  # Part 1 ends at 600 + 90
    if part == P2:
        return engine, 690.0
    engine.handle(Tick(810.0))  # Part 2 ends at 690 + 120
    return engine, 810.0


# --- Draws ---


def test_start_shows_a_draw_of_two_items_for_parts_2_and_3_only(a2, items):
    engine = engine_for(a2, items)
    effects = engine.start(0.0)
    assert effects[0] == PhaseChanged(Phase.DRAW, None, 0.0, None)
    draws = of_type(effects, ShowDraw)
    assert [d.part for d in draws] == [P2, P3]
    assert all(len(d.cards) == 2 for d in draws)


def test_part_1_gets_one_question_bank_chosen_by_the_engine(a2, items):
    engine = engine_for(a2, items)
    engine.start(0.0)
    assert P1 not in engine.draws
    assert engine.chosen[P1].startswith("a2-entretien-dirige-")


def test_the_same_seed_always_gives_the_same_draws(a2, items):
    first = engine_for(a2, items, seed=42)
    again = engine_for(a2, items, seed=42)
    assert first.draws == again.draws
    assert first.chosen == again.chosen


def test_different_seeds_give_different_draws(a2, items):
    draws = {tuple(sorted(engine_for(a2, items, seed=s).draws.items())) for s in range(10)}
    assert len(draws) > 1


@pytest.mark.parametrize("seed", range(25))
def test_a_draw_never_offers_the_same_item_twice(a2, items, seed):
    for part, ids in engine_for(a2, items, seed).draws.items():
        assert len(set(ids)) == len(ids) == 2, part


def test_draws_hold_reviewed_items_of_the_right_part_only(a2, items):
    by_id = {i.root.id.root: i.root for i in items}
    engine = engine_for(a2, items, seed=3)
    for part, ids in engine.draws.items():
        for item_id in ids:
            assert by_id[item_id].part_key.root == part
            assert by_id[item_id].status.value == "reviewed"


def test_draft_items_are_never_drawn(a2, items):
    drafts = []
    for item in items:
        copy = item.model_copy(deep=True)
        if copy.root.part_key.root == P2:
            copy.root.status = type(copy.root.status)("draft")
        drafts.append(copy)
    with pytest.raises(EngineError, match=r"monologue_suivi.*needs 2"):
        engine_for(a2, drafts)


def test_not_enough_items_for_a_part_is_an_error(a2, items):
    first_interaction = next(i for i in items if i.root.part_key.root == P3)
    only_one_interaction = [i for i in items if i.root.part_key.root != P3] + [first_interaction]
    with pytest.raises(EngineError, match=r"exercice_en_interaction.*needs 2"):
        engine_for(a2, only_one_interaction)


def test_choosing_an_item_outside_the_draw_is_an_error(a2, items):
    engine = engine_for(a2, items)
    engine.start(0.0)
    with pytest.raises(EngineError, match="not in the Draw"):
        engine.handle(ChoseItem(1.0, P2, "not-an-item"))
    with pytest.raises(EngineError, match="has no Draw"):
        engine.handle(ChoseItem(1.0, P1, engine.chosen[P1]))


def test_prep_time_waits_until_every_draw_is_chosen(a2, items):
    engine = engine_for(a2, items)
    engine.start(0.0)
    effects = engine.handle(ChoseItem(5.0, P2, engine.draws[P2][1]))
    assert effects == []
    assert engine.phase is Phase.DRAW
    effects = engine.handle(ChoseItem(8.0, P3, engine.draws[P3][0]))
    assert PhaseChanged(Phase.PREP, None, 8.0, 608.0) in effects
    assert engine.chosen[P2] == engine.draws[P2][1]
    assert engine.chosen[P3] == engine.draws[P3][0]


def test_the_candidate_can_change_a_choice_before_the_last_draw_is_chosen(a2, items):
    engine = engine_for(a2, items)
    engine.start(0.0)
    engine.handle(ChoseItem(1.0, P2, engine.draws[P2][0]))
    engine.handle(ChoseItem(2.0, P2, engine.draws[P2][1]))
    assert engine.chosen[P2] == engine.draws[P2][1]


# --- Prep Time ---


def test_prep_time_lasts_600_seconds_and_ends_on_its_timer(a2, items):
    engine = engine_for(a2, items)
    engine.start(0.0)
    choose_all(engine, at=10.0)
    assert engine.phase is Phase.PREP
    assert engine.next_deadline == 610.0
    assert engine.handle(Tick(609.9)) == []
    effects = engine.handle(Tick(610.0))
    assert engine.phase is Phase.PART
    assert engine.current_part == P1
    assert PhaseChanged(Phase.PART, P1, 610.0, 700.0) in effects


def test_ready_ends_prep_time_early(a2, items):
    engine = engine_for(a2, items)
    engine.start(0.0)
    choose_all(engine, at=10.0)
    effects = engine.handle(Ready(100.0))
    assert engine.current_part == P1
    assert PhaseChanged(Phase.PART, P1, 100.0, 190.0) in effects


def test_ready_outside_prep_time_does_nothing(a2, items):
    engine = engine_for(a2, items)
    engine.start(0.0)
    assert engine.handle(Ready(1.0)) == []
    assert engine.phase is Phase.DRAW


def test_turns_during_prep_time_are_ignored(a2, items):
    engine = engine_for(a2, items)
    engine.start(0.0)
    choose_all(engine, at=1.0)
    assert engine.handle(CandidateTurn(5.0, "Bonjour")) == []
    assert engine.phase is Phase.PREP


# --- Parts, transitions and timers ---


def test_each_part_is_announced_with_a_fixed_french_line(a2, items):
    engine = engine_for(a2, items)
    engine.start(0.0)
    choose_all(engine)
    said = {}
    for tick in (600.0, 690.0, 810.0):
        said[tick] = [e.text for e in of_type(engine.handle(Tick(tick)), SayFixedLine)]
    assert any("entretien dirigé" in text for text in said[600.0])
    assert any("monologue suivi" in text for text in said[690.0])
    assert any("exercice en interaction" in text for text in said[810.0])


def test_part_1_opens_with_the_examiner_and_answers_every_candidate_turn(a2, items):
    engine, t = at_part(a2, items, P1)
    effects = engine.handle(CandidateTurn(t + 10, "Je m'appelle Sam."))
    [ask] = of_type(effects, AskExaminer)
    assert (ask.part, ask.reason, ask.candidate_text) == (P1, "candidate_turn", "Je m'appelle Sam.")
    assert ask.item is not None and ask.item.questions


def test_part_1_ends_at_its_max_duration_and_part_2_starts(a2, items):
    engine, t = at_part(a2, items, P1)
    assert engine.next_deadline == t + 90
    assert engine.handle(Tick(t + 89.9)) == []
    effects = engine.handle(Tick(t + 90))
    assert PhaseChanged(Phase.PART, P2, t + 90, t + 210) in effects
    assert engine.current_part == P2


def test_the_wrap_up_signal_comes_at_the_part_minimum(a2, items):
    engine, t = at_part(a2, items, P3)  # Part 3 runs 180 to 240 seconds
    assert engine.next_deadline == t + 180
    effects = engine.handle(Tick(t + 180))
    assert effects == [WrapUpAllowed(P3)]
    [ask] = of_type(engine.handle(CandidateTurn(t + 185, "Merci")), AskExaminer)
    assert ask.may_wrap_up is True
    assert engine.next_deadline == t + 240


def test_may_wrap_up_is_false_before_the_minimum(a2, items):
    engine, t = at_part(a2, items, P3)
    [ask] = of_type(engine.handle(CandidateTurn(t + 5, "Bonjour")), AskExaminer)
    assert ask.may_wrap_up is False


def test_part_3_opens_with_the_examiner(a2, items):
    engine, t = at_part(a2, items, P2)
    effects = engine.handle(Tick(t + 120))
    openings = [a for a in of_type(effects, AskExaminer) if a.reason == "opening"]
    assert [a.part for a in openings] == [P3]


def test_the_last_part_ending_ends_the_session(a2, items):
    engine, t = at_part(a2, items, P3)
    effects = engine.handle(Tick(t + 240))
    assert effects[-1] == SessionEnded("completed")
    assert PhaseChanged(Phase.ENDED, None, t + 240, None) in effects
    assert engine.phase is Phase.ENDED
    assert engine.next_deadline is None
    assert engine.handle(CandidateTurn(t + 250, "Allô ?")) == []


def test_a_late_tick_replays_every_missed_deadline_at_its_own_time(a2, items):
    engine = engine_for(a2, items)
    engine.start(0.0)
    choose_all(engine)
    effects = engine.handle(Tick(2000.0))
    changes = [(e.phase, e.part, e.started_at) for e in of_type(effects, PhaseChanged)]
    assert changes == [
        (Phase.PART, P1, 600.0),
        (Phase.PART, P2, 690.0),
        (Phase.PART, P3, 810.0),
        (Phase.ENDED, None, 1050.0),
    ]
    assert of_type(effects, WrapUpAllowed)


def test_time_going_backwards_is_an_error(a2, items):
    engine, t = at_part(a2, items, P1)
    with pytest.raises(EngineError, match="backwards"):
        engine.handle(Tick(t - 1))


def test_events_before_start_are_an_error(a2, items):
    with pytest.raises(EngineError, match="start"):
        engine_for(a2, items).handle(Tick(0.0))


def test_the_engine_cannot_be_started_twice(a2, items):
    engine = engine_for(a2, items)
    engine.start(0.0)
    with pytest.raises(EngineError, match="already started"):
        engine.start(1.0)


# --- Turn Modes: the monologue ---


def test_the_examiner_only_listens_during_the_monologue(a2, items):
    engine, t = at_part(a2, items, P2)
    assert of_type(engine.handle(Tick(t)), AskExaminer) == []
    for i in range(5):
        assert engine.handle(CandidateTurn(t + 5 + i, "Alors, j'habite dans un appartement.")) == []
    assert engine.handle(CandidateActivity(t + 20)) == []


def test_the_monologue_ends_when_the_candidate_says_they_are_done(a2, items):
    engine, t = at_part(a2, items, P2)
    effects = engine.handle(CandidateDone(t + 40))
    [ask] = of_type(effects, AskExaminer)
    assert (ask.part, ask.reason, ask.follow_up_number) == (P2, "follow_up", 1)


def test_the_monologue_ends_when_the_listening_time_runs_out(a2, items):
    engine, t = at_part(a2, items, P2)
    assert engine.next_deadline == t + 90  # three quarters of 120 seconds
    effects = engine.handle(Tick(t + 90))
    [ask] = of_type(effects, AskExaminer)
    assert (ask.reason, ask.follow_up_number) == ("follow_up", 1)


def test_the_listening_share_is_configurable(a2, items):
    engine = engine_for(a2, items, config=EngineConfig(listening_share=0.5))
    engine.start(0.0)
    choose_all(engine)
    engine.handle(Tick(690.0))
    assert engine.next_deadline == 750.0  # Part 2 starts at 690, listens for 60


def test_up_to_three_follow_up_questions_then_the_next_part(a2, items):
    engine, t = at_part(a2, items, P2)
    asks = of_type(engine.handle(CandidateDone(t + 30)), AskExaminer)
    for i in range(1, 3):
        asks += of_type(engine.handle(CandidateTurn(t + 30 + i, f"Réponse {i}")), AskExaminer)
    assert [a.follow_up_number for a in asks] == [1, 2, 3]
    effects = engine.handle(CandidateTurn(t + 40, "Réponse 3"))
    assert of_type(effects, AskExaminer)[0].part == P3
    assert engine.current_part == P3


def test_follow_ups_carry_the_subject_and_never_examiner_only_data(a2, items):
    engine, t = at_part(a2, items, P2)
    [ask] = of_type(engine.handle(CandidateDone(t + 30)), AskExaminer)
    assert ask.item.item_id == engine.chosen[P2]
    assert ask.item.suggested_angles
    assert ask.item.examiner_only_data is None


def test_the_part_timer_still_ends_the_monologue_part_during_follow_ups(a2, items):
    engine, t = at_part(a2, items, P2)
    engine.handle(CandidateDone(t + 100))
    effects = engine.handle(Tick(t + 120))
    assert engine.current_part == P3
    assert PhaseChanged(Phase.PART, P3, t + 120, t + 360) in effects


def test_zero_follow_ups_ends_the_part_when_the_monologue_ends(a2, items):
    engine = engine_for(a2, items, config=EngineConfig(max_follow_ups=0))
    engine.start(0.0)
    choose_all(engine)
    engine.handle(Tick(690.0))
    effects = engine.handle(CandidateDone(700.0))
    assert engine.current_part == P3
    assert not [a for a in of_type(effects, AskExaminer) if a.reason == "follow_up"]


def test_candidate_done_is_ignored_outside_the_monologue(a2, items):
    engine, t = at_part(a2, items, P1)
    assert engine.handle(CandidateDone(t + 5)) == []


# --- Candidate activity ---


def test_typing_and_turns_are_tracked_for_relance(a2, items):
    engine, t = at_part(a2, items, P1)
    assert engine.last_candidate_activity_at is None
    engine.handle(CandidateActivity(t + 3))
    assert engine.last_candidate_activity_at == t + 3
    engine.handle(CandidateTurn(t + 7, "Oui"))
    assert engine.last_candidate_activity_at == t + 7


def test_a_blank_turn_is_not_sent_to_the_examiner(a2, items):
    engine, t = at_part(a2, items, P1)
    assert engine.handle(CandidateTurn(t + 2, "   ")) == []


# --- Examiner-only Data ---


def leaf_strings(value):
    if isinstance(value, dict):
        for v in value.values():
            yield from leaf_strings(v)
    elif isinstance(value, str):
        yield value


def play_a_whole_mock(a2, items, seed):
    """Plays a Mock and returns every effect, in order."""
    engine = engine_for(a2, items, seed)
    effects = engine.start(0.0)
    effects += choose_all(engine, at=20.0)
    effects += engine.handle(Ready(120.0))
    t = 120.0
    effects += engine.handle(CandidateTurn(t + 5, "Bonjour, je m'appelle Sam."))
    effects += engine.handle(Tick(t + 90))
    t += 90
    effects += engine.handle(CandidateTurn(t + 5, "J'habite dans une grande ville."))
    effects += engine.handle(CandidateDone(t + 40))
    for i in range(3):
        effects += engine.handle(CandidateTurn(t + 45 + i, f"Réponse {i}"))
    t += 120
    effects += engine.handle(Tick(t))
    effects += engine.handle(CandidateTurn(t + 5, "Bonjour madame."))
    effects += engine.handle(Tick(t + 240))
    return engine, effects


def test_a_whole_a2_mock_plays_through_from_the_draws_to_session_ended(a2, items):
    engine, effects = play_a_whole_mock(a2, items, seed=7)
    phases = [(e.phase, e.part) for e in of_type(effects, PhaseChanged)]
    assert phases == [
        (Phase.DRAW, None),
        (Phase.PREP, None),
        (Phase.PART, P1),
        (Phase.PART, P2),
        (Phase.PART, P3),
        (Phase.ENDED, None),
    ]
    assert effects[-1] == SessionEnded("completed")
    assert engine.phase is Phase.ENDED


@pytest.mark.parametrize("seed", range(10))
def test_no_candidate_facing_effect_contains_examiner_only_data(a2, items, seed):
    engine, effects = play_a_whole_mock(a2, items, seed)
    # Only the Items this Session offered. A fact the Candidate's own brief already states
    # (a restaurant's name) is not a secret.
    by_id = {i.root.id.root: i.root for i in items}
    secrets = {
        text
        for item_id in engine.draws[P3]
        for text in leaf_strings(by_id[item_id].examiner_only_data)
        if len(text) > 8 and text not in by_id[item_id].candidate_brief
    }
    assert secrets
    for effect in effects:
        if isinstance(effect, AskExaminer):
            continue
        assert not any(secret in repr(effect) for secret in secrets), effect


def test_the_examiner_only_sees_the_current_parts_chosen_item(a2, items):
    by_id = {i.root.id.root: i.root for i in items}
    engine, effects = play_a_whole_mock(a2, items, seed=11)
    asks = of_type(effects, AskExaminer)
    for ask in asks:
        assert ask.item.item_id == engine.chosen[ask.part]
        if ask.part != P3:
            assert ask.item.examiner_only_data is None
    part_3 = [a for a in asks if a.part == P3]
    assert part_3
    chosen = by_id[engine.chosen[P3]]
    rejected = by_id[next(i for i in engine.draws[P3] if i != engine.chosen[P3])]
    for ask in part_3:
        assert ask.item.examiner_only_data == chosen.examiner_only_data
        assert ask.item.examiner_only_data != rejected.examiner_only_data


def test_examiner_only_data_is_a_copy_the_caller_cannot_use_to_change_the_item(a2, items):
    engine, t = at_part(a2, items, P3)
    [ask] = of_type(engine.handle(CandidateTurn(t + 1, "Bonjour")), AskExaminer)
    ask.item.examiner_only_data.clear()
    [again] = of_type(engine.handle(CandidateTurn(t + 2, "Bonjour")), AskExaminer)
    assert again.item.examiner_only_data


def test_draw_cards_hold_the_brief_only(a2, items):
    by_id = {i.root.id.root: i.root for i in items}
    engine = engine_for(a2, items)
    for draw in of_type(engine.start(0.0), ShowDraw):
        for card in draw.cards:
            assert set(vars(card)) == {"item_id", "candidate_brief"}
            assert card.candidate_brief == by_id[card.item_id].candidate_brief


# --- Late Ticks, config and seeds ---


def test_a_late_tick_does_not_make_the_examiner_speak_for_parts_that_are_over(a2, items):
    engine = engine_for(a2, items)
    engine.start(0.0)
    choose_all(engine)
    effects = engine.handle(Tick(2000.0))
    assert of_type(effects, AskExaminer) == []
    engine, t = at_part(a2, items, P2)
    asks = of_type(engine.handle(Tick(t + 200)), AskExaminer)
    assert [(a.part, a.reason) for a in asks] == [(P3, "opening")]


@pytest.mark.parametrize(
    "config", [{"listening_share": 0}, {"listening_share": 1.5}, {"max_follow_ups": -1}]
)
def test_a_nonsense_config_is_rejected(config):
    with pytest.raises(EngineError):
        EngineConfig(**config)


def test_an_int_seed_and_the_same_text_seed_are_different_seeds(a2, items):
    ints = {tuple(engine_for(a2, items, seed=s).draws.items()) for s in range(10)}
    texts = {tuple(engine_for(a2, items, seed=str(s)).draws.items()) for s in range(10)}
    assert ints != texts
