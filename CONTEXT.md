# Fromage

Fromage (French Language Assessment Prep) runs original, exam-format French speaking mock exams with an AI examiner and gives an estimated, evidence-backed score against the official grid for that format. Phase 1 covers DELF A1 and A2.

## Exam formats

**Exam Definition**:
The versioned description of one exam format: its Level, its Parts in order, the timings and the Grid.
_Avoid_: exam config, test template, exam (on its own)

**Level**:
The CEFR level an Exam Definition targets (A1–C2).
_Avoid_: grade, difficulty

**Part**:
One timed section of a speaking exam, such as the guided interview, the monologue or the role-play.
_Avoid_: section, task, épreuve (the épreuve is the whole speaking test)

**Turn Mode**:
Whether the Examiner replies to each Candidate turn in a Part (interactive) or only listens until the Part ends (listen-only).
_Avoid_: conversation type

**Prep Time**:
The timed period before the live Parts in which the Candidate prepares their chosen Items.
_Avoid_: preparation phase, warm-up

## Content

**Item**:
One original prompt a Candidate can be given for a Part, such as a monologue subject, an interaction situation or a set of Cards.
_Avoid_: question, subject, sujet, prompt

**Draw**:
The Items offered to the Candidate for a Part, from which they choose one (for example, two subjects, keep one).
_Avoid_: shuffle, pick

**Examiner-only Data**:
Facts belonging to an Item that only the Examiner knows, such as a price list or a timetable.
_Avoid_: hidden context, secret data

**Card**:
A keyword the A1 Candidate uses to ask the Examiner a question in the information-exchange Part.
_Avoid_: flashcard, keyword card

**Wallet**:
The simulated money an A1 Candidate pays with in the role-play Part.
_Avoid_: balance, banknotes

**Topic Taxonomy**:
The themes for each Level and Part, taken from the official format, that original Items are written against.
_Avoid_: categories, tags

## Sessions

**Candidate**:
The person taking a Session.
_Avoid_: learner, student, test-taker, user (User means the account)

**User**:
The account a Candidate signs in with.
_Avoid_: member, profile

**Examiner**:
The AI persona that runs a Session, following the exam's procedure.
_Avoid_: tutor, bot, agent, teacher

**Session**:
One sitting of one Exam Definition by one Candidate, in one Mode and one Medium.
_Avoid_: attempt, test, exam, run

**Mode**:
The rules a Session runs under: Mock or Practice.
_Avoid_: type, setting

**Mock**:
The Mode that reproduces exam conditions: no pausing, no correction during the Session, graded at the end.
_Avoid_: simulation, real exam

**Practice**:
The Mode with relaxed rules: pausing, retrying a Part, asking for thinking time, and feedback after each Part.
_Avoid_: training, drill

**Medium**:
How a Session is carried out: typed text or voice.
_Avoid_: text mode, voice mode (Mode means Mock or Practice)

**Relance**:
The Examiner's follow-up after Candidate silence, as the official examiner guidance describes: repeat the question, then say it more slowly, then reformulate it.
_Avoid_: retry, nudge, re-prompt

**Transcript**:
The record of a Session, with a speaker label and a timestamp on every turn.
_Avoid_: log, history, conversation

**False Cut-off**:
A moment when the Examiner starts speaking before the Candidate has finished their turn.
_Avoid_: interruption (a Candidate talking over the Examiner is a barge-in)

## Assessment

**Grid**:
The official scoring grid for a Level's speaking test: a fixed set of Criteria that adds up to 25 points.
_Avoid_: rubric, scale, marking scheme

**Criterion**:
One row of the Grid. It is scoped either to a single Part (task achievement) or to the whole Session (lexique, morphosyntaxe, phonologie).
_Avoid_: dimension, metric, category

**Band**:
One of the four ordinal levels a Criterion is rated on: 0 not answered or insufficient, 1 below the target Level, 2 at the target Level, 3 above it (for example A2+).
_Avoid_: score, grade, mark

**Band Points**:
What a Band is worth for a given Criterion, for example 0 / 1 / 2.5 / 4 or 0 / 1 / 3 / 5.
_Avoid_: weight

**Judge**:
The component that assigns a Band to a Criterion from a Session.
_Avoid_: grader (the Grader is the whole grading job), scorer, evaluator

**Judgement**:
One Judge's Band for one Criterion in one Session, with its Evidence.
_Avoid_: rating, verdict

**Evidence**:
An exact quote from the Transcript, with its timestamp, that a Judgement relies on.
_Avoid_: justification, reasoning

**Band Distribution**:
How often each Band came up across repeated Judgements of the same Criterion. It gives the Modal Band and the Expected Points.
_Avoid_: confidence, probability

**Estimated Score**:
The sum of the Band Points across all Criteria, out of 25. It is always an estimate, never an official result.
_Avoid_: result, official score, grade, mark

**Report**:
What the Candidate sees after grading: the Bands with their Evidence, the Estimated Score, Corrections and a Model Answer.
_Avoid_: results page, feedback (on its own)

**Correction**:
A Candidate error taken from the Transcript, shown with a minimal fix and the rule behind it.
_Avoid_: fix, suggestion

**Model Answer**:
A rewrite of the Candidate's own answer, keeping their content, at one Band higher.
_Avoid_: ideal answer, sample answer

## Evaluation

**Calibration Set**:
Answers built to have a known Intended Band (scripted answers plus Degradations), used to measure whether the Judge orders Bands correctly, gives consistent Judgements and is unbiased.
_Avoid_: gold set (a Gold Set is rated by humans), test data

**Intended Band**:
The Band a Calibration Set answer was built to deserve.
_Avoid_: label, ground truth

**Degradation**:
A controlled change to a Calibration Set answer meant to lower its Intended Band, such as injecting agreement errors, shortening it or adding heavy hesitation.
_Avoid_: corruption, perturbation

**Gold Set**:
Sessions rated independently by qualified humans on the Grid. There is none yet. The evaluation accepts one once it exists.
_Avoid_: calibration set, benchmark
