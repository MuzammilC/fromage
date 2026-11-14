# DELF/DALF Speaking Coach: technical and domain research

*Research date: 2026-11-10. Prices, model names and product status change quickly, so re-check anything you plan to rely on.*

**How to read this document**

- Every factual claim has an inline link to its source.
- **[secondary]** marks a claim that rests only on a third-party source, a search-engine summary, or vendor marketing.
- **[recommendation]** marks my own judgement.
- **[unverified]** marks a claim I couldn't confirm. All of these are collected in [Verification notes](#verification-notes).
- **Method note:** france-education-international.fr (FEI) blocks automated HTTP fetchers (it returns `ERR-BOT-403`). I read the FEI pages and their official PDFs (sample papers, examiner documents, grids and descriptors) in a normal browser session on 2026-11-10 and extracted the text from there. Every FEI link below is the official URL. The PDFs are served as downloads.

---

## TL;DR

1. **The rubric is public, and it is band-based, not continuous.** Every FEI speaking grid has the same layout:
   - Task criteria, one per exam part ("réalisation de la tâche").
   - Three linguistic criteria: lexique, morphosyntaxe, maîtrise du système phonologique.
   - Each criterion is scored by ticking one of **four bands**: 0 / 1 / 2.5 / 4, or 0 / 1 / 3 / 5 for the 5-point criteria.
   - The bands mean: not answered or insufficient / below target level / at target level (e.g. A1) / above it (A1+).
   - Every grid totals 25 points ([A1 grid](https://www.france-education-international.fr/document/grille-po-a1), [A2 grid](https://www.france-education-international.fr/document/grille-po-a2)).
   - The judge should therefore be built as a **per-criterion ordinal classifier with evidence**, not a free 0–25 score.
2. **Phase 1 is very tractable.**
   - **A1:** three parts in 5–7 minutes, with 10 minutes of preparation ([FEI A1](https://www.france-education-international.fr/diplome/delf-tout-public/niveau-a1)).
   - **A2:** three parts in 6–8 minutes, with 10 minutes of preparation ([FEI A2](https://www.france-education-international.fr/diplome/delf-tout-public/niveau-a2)).
   - The examiner's behaviour is scripted in FEI's examiner documents: speak slowly, reformulate when the candidate doesn't understand, play a shop assistant with a hidden price list ([A1 examiner doc](https://www.france-education-international.fr/document/delf-dalf-a1-tp-examinateur-sujet-demo0)).
3. **Don't copy official subjects into the app.**
   - FEI's candidate documents say reusing DELF/DALF subjects is forbidden and will lead to sanctions ([A1 candidate doc](https://www.france-education-international.fr/document/delf-dalf-a1-tp-candidat-ind-sujet-demo)).
   - FEI's legal notice says that everything except "official documents" is under copyright, and that reuse needs the author's permission ([mentions légales](https://www.france-education-international.fr/mentions-legales)).
   - **[recommendation]** Use official material only to derive the format and topic taxonomy, and write original prompts in the same style.
4. **Phase 1 voice stack [recommendation]:** a cascaded pipeline (STT → LLM → TTS) on **LiveKit Agents**. It beats speech-to-speech for this product for three reasons:
   - Grading needs a faithful transcript. OpenAI itself says the transcript of user audio in its Realtime API comes from a separate ASR model and is only a rough guide ([OpenAI docs, via search](https://developers.openai.com/api/docs/guides/realtime-conversations)).
   - Turn-taking has to be deliberately patient with hesitant learners.
   - The examiner has to follow a strict script and hold examiner-only data, which is easier with a text LLM.
5. **Learner pauses are the main voice-UX risk.** Use semantic or acoustic end-of-turn detection with long timeouts:
   - Deepgram Flux: `eot_timeout_ms` from 500 to 60,000, default 5,000 ([Flux docs](https://developers.deepgram.com/docs/flux/quickstart)).
   - LiveKit's audio turn detector, which covers French ([LiveKit](https://docs.livekit.io/agents/build/turns/turn-detector/)).
   - Pipecat Smart Turn v3.2, BSD-2, 23 languages including French ([GitHub](https://github.com/pipecat-ai/smart-turn)).
   - Add a "relance" policy that copies FEI examiner behaviour.
6. **Transcript-only grading can't measure the phonology criterion,** which carries 4–5 of the 25 points. It is also biased: ASR tends to drop hesitations and can silently repair learner errors ([LearnerVoice, arXiv 2407.04280](https://arxiv.org/abs/2407.04280); [arXiv 2506.04076](https://arxiv.org/html/2506.04076v1)). Supplement it with:
   - Azure Pronunciation Assessment, which supports **fr-FR and fr-CA**. Prosody scoring is en-US only ([Azure docs](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=pronunciation-assessment), [how-to](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/how-to-pronunciation-assessment)).
   - Or Speechace, which supports fr-fr and fr-ca pronunciation and fluency but gives no grammar or vocabulary scores for French ([Speechace](https://api-docs.speechace.com/solutions/speaking-practice-in-spanish-and-french)).
   - Timing-based fluency features (speech rate, pauses).
   - Optionally, an audio-native LLM judge.
7. **G-Eval in brief.** The model generates its own evaluation steps from the criteria, fills in a scoring form, and the final score is the probability-weighted sum Σ p(sᵢ)·sᵢ. Because GPT-4 exposed no probabilities, the authors estimated them by sampling 20 times ([arXiv 2303.16634](https://arxiv.org/html/2303.16634v3)).
   - **[recommendation]** Map this onto the DELF bands: one call per criterion, the band descriptors in the prompt, quoted evidence from the transcript, and n samples giving a band distribution. Then mimic FEI's mandatory *double évaluation* ([grids](https://www.france-education-international.fr/document/grille-po-a1)) with two independent judges plus a harmonisation step.
8. **The headline résumé artefact is an eval harness with measured agreement.** I found **no openly licensed, CEFR-labelled French spoken-learner corpus** (see C.5). FEI's CEFR-illustration videos may only be used for non-commercial examiner and teacher training ([FEI](https://www.france-education-international.fr/productions-orales-illustrant-les-6-niveaux-du-cecrl)). **[recommendation]** Build a consented gold set of about 100–200 double-rated mock exams and report per-criterion quadratic weighted kappa (QWK) with confidence intervals.
9. **Cost per 12-minute connected session** (arithmetic in B.8):
   - Cascaded voice: about $0.22–0.31.
   - Plus judging: about $0.15–0.65.
   - `gpt-realtime-2.1`: about $0.65 if prompt caching works, up to about $5 if it doesn't ([OpenAI pricing](https://developers.openai.com/api/docs/pricing), [token math](https://developers.openai.com/api/docs/guides/voice-latency-cost)).
   - Avatar add-on: from about $0.11 (Simli) to about $4 (Tavus).
10. **Market** ([FEI, 2026-03](https://www.france-education-international.fr/actualites/lettre-fei/2026-02/les-certifications-de-langue-francaise-de-france-education-international-en-forte-hausse)):
    - DELF-DALF had 513,435 candidates in 2025.
    - TCF had 310,473 (+21%), of which TCF Canada was 124,667.
    - Since 2026-01-01, France requires A2 for a first multi-year residence card and B1 for a first resident card ([service-public.fr](https://www.service-public.gouv.fr/particuliers/vosdroits/F34501?lang=fr)); naturalisation is reportedly B2 **[secondary]**.
    - TCF/TEF Canada speaking is the obvious expansion.

### Recommended Phase 1 architecture (summary) [recommendation]

```
Browser (Next.js, LiveKit JS SDK, WebRTC)
   │  mic audio ↑   examiner audio ↓   data channel: phase/timer/cards UI
LiveKit (Cloud first; self-host later)
   │
Agent worker (Python, LiveKit Agents)
   ├─ Exam state machine (level, part, timers, card draws, examiner-only data)
   ├─ STT: Deepgram Flux Multilingual (flux-general-multi, language_hint=fr)
   │        → turn events (EndOfTurn / EagerEndOfTurn / TurnResumed), word timestamps
   ├─ Examiner LLM: Claude Haiku 5.5 (claude-haiku-5-5), short replies, prompt-cached scenario
   │        (Sonnet 5.5 as fallback for open B1+ conversation)
   ├─ TTS: ElevenLabs Flash v2.5 or Cartesia Sonic-3.x French voice (A/B test)
   └─ Recorder: per-part learner audio (separate track) → object storage (EU)
Post-session grading job (queue)
   ├─ Re-transcription (batch, word timestamps, verbatim-leaning) + VAD pause map
   ├─ Fluency features (speech rate, articulation rate, pause stats, filled pauses)
   ├─ Pronunciation: Azure Pronunciation Assessment fr-FR (unscripted or transcript-as-reference)
   ├─ Judge: Claude Opus 5.5 (claude-opus-5-5), G-Eval-style per-criterion band classification,
   │         n-sample distribution, evidence quotes, structured JSON; 2nd judge from another family
   └─ Feedback generator: corrections, model answers, error taxonomy
Observability: Langfuse (traces of every LLM call + eval datasets); latency spans per turn
Data: Postgres (Supabase EU) + object storage with lifecycle deletion
```

---

## A. Exam domain

### A.1 Speaking test structure by level (DELF/DALF *tout public*)

Common rules for DELF A1–B2 and DALF C1 ([A1](https://www.france-education-international.fr/diplome/delf-tout-public/niveau-a1), [B2](https://www.france-education-international.fr/diplome/delf-tout-public/niveau-b2), [C1](https://www.france-education-international.fr/article/dalf-c1)):

- Each of the four épreuves is scored out of 25.
- The diploma needs at least 50/100 overall.
- A score below 5/25 in any épreuve is eliminatory.
- The speaking test is individual: the candidate is alone in front of **two examiners**.

DALF C2 is different ([C2](https://www.france-education-international.fr/article/dalf-c2)):

- It has two épreuves, each out of 50, with a minimum of 10/50 in each.
- The oral grid is still filled out of 25 and then multiplied by 2 ([C2 grid](https://www.france-education-international.fr/document/grille-copo-c2)).

| Level | Parts (in order) | Live duration | Prep | Source |
|---|---|---|---|---|
| **A1** | 1. Entretien dirigé (no prep, ~1 min)<br>2. Échange d'informations (~2 min)<br>3. Dialogue simulé / jeu de rôle (~2 min) | 5–7 min | 10 min, for parts 2 and 3 | [A1 page](https://www.france-education-international.fr/diplome/delf-tout-public/niveau-a1), [A1 grid](https://www.france-education-international.fr/document/grille-po-a1), [A1 candidate doc](https://www.france-education-international.fr/document/delf-dalf-a1-tp-candidat-ind-sujet-demo) |
| **A2** | 1. Entretien dirigé (no prep, ~1 min 30)<br>2. Monologue suivi (~2 min)<br>3. Exercice en interaction (3–4 min) | 6–8 min | 10 min, for parts 2 and 3 | [A2 page](https://www.france-education-international.fr/diplome/delf-tout-public/niveau-a2), [A2 grid](https://www.france-education-international.fr/document/grille-po-a2), [A2 examiner doc](https://www.france-education-international.fr/document/delf-a2-tp-examinateur-ind) |
| **B1** | 1. Entretien dirigé (no prep, 2–3 min)<br>2. Exercice en interaction (no prep, 3–4 min)<br>3. Expression d'un point de vue (with prep, 5–7 min) | 15 min on the level page; "10 à 15 minutes" in the sample examiner doc | 10 min, for part 3 | [B1 page](https://www.france-education-international.fr/diplome/delf-tout-public/niveau-b1), [B1 grid](https://www.france-education-international.fr/document/grille-po-b1), [B1 examiner doc](https://www.france-education-international.fr/document/delf-b1-tp-examinateur-ind) |
| **B2** | 1. Monologue suivi (present and defend a point of view from a short document, 5–7 min)<br>2. Exercice en interaction (debate with the examiner, 10–13 min) | 20 min | 30 min | [B2 page](https://www.france-education-international.fr/diplome/delf-tout-public/niveau-b2), [B2 grid](https://www.france-education-international.fr/document/grille-po-b2), [B2 examiner doc](https://www.france-education-international.fr/document/delf-b2-tp-examinateur-ind) |
| **C1** | 1. Exposé from a set of written documents on a theme (8–10 min)<br>2. Entretien / débat with the jury (15–20 min) | 30 min | 1 h | [C1 page](https://www.france-education-international.fr/article/dalf-c1), [C1 grid](https://www.france-education-international.fr/document/grille-po-c1), [C1 examiner doc](https://www.france-education-international.fr/document/dalf-c1sujet-demo-examinateur) |
| **C2** | 1. Compte rendu of an audio document, heard twice (5–10 min)<br>2. Développement personnel / point de vue argumenté (~10 min)<br>3. Débat with the jury (~10 min) | 30 min | 1 h | [C2 page](https://www.france-education-international.fr/article/dalf-c2), [C2 grid](https://www.france-education-international.fr/document/grille-copo-c2) |

### A.2 What the examiner does in each part (A1/A2 in detail)

From FEI's demo examiner documents. Paraphrased; the links go to the originals.

**A1** ([examiner doc](https://www.france-education-international.fr/document/delf-dalf-a1-tp-examinateur-sujet-demo0), [candidate doc](https://www.france-education-international.fr/document/delf-dalf-a1-tp-candidat-ind-sujet-demo)):

- **Before the test.** The candidate draws six word cards for part 2 and two role-play subjects for part 3, picks one subject, and gets 10 minutes to prepare. The parts then run back to back, and the examiner announces each transition.
- **Part 1, entretien dirigé.**
  - The examiner asks *very slowly* about the candidate's identity, family, likes and daily routine.
  - If the candidate doesn't understand, the examiner reformulates.
  - The doc includes a bank of example questions, e.g. name and spelling, nationality, job, typical day, weekend activities.
- **Part 2, échange d'informations.**
  - The candidate asks the examiner questions prompted by the keyword on each card (e.g. "date de naissance" → asking the examiner's age).
  - The examiner answers briefly and checks the candidate has understood.
  - Cards cover themes such as family, office, car, phone, apartment, nationality, computer, train, school, bank, library, park, swimming pool, restaurant.
- **Part 3, dialogue simulé.**
  - The candidate plays a customer who obtains goods or services: asks prices, states quantities, and pays with **fake banknotes and coins** handed over by the examiner.
  - The examiner plays the shop assistant or clerk and holds an **examiner-only document** with prices, schedules and so on.
  - The 10 demo scenarios: hotel booking, clothes shop, holiday club, market, theatre tickets, café, train station, office supplies, school enrolment, bookshop.
  - **[recommendation]** In the app: a virtual wallet, hidden scenario data that only the examiner LLM sees, and mandatory greeting/politeness moves.

**A2** ([examiner doc](https://www.france-education-international.fr/document/delf-a2-tp-examinateur-ind)):

- **Before the test.** The candidate draws two subjects for part 2 and two for part 3, chooses one of each, and gets 10 minutes to prepare.
- **Part 1, entretien dirigé (~1 min 30).** The candidate introduces themselves; the examiner asks follow-up questions about family, home, hobbies and friends.
- **Part 2, monologue suivi (~2 min).** The examiner lets the candidate speak continuously on the chosen subject, then may ask two or three follow-up questions. The 15 demo subjects are personal-sphere topics: housing, sea vs mountain, friends, sport, shops, cinema, plane, restaurant, workday, computer, workplace, books, studies, French, favourite teacher.
- **Part 3, exercice en interaction (3–4 min).**
  - The candidate resolves an everyday situation with the examiner and must greet and use basic politeness.
  - Demo situations: estate agency, mountain holiday (talking to a friend), buying a computer, adopting a dog, choosing a theatre show with a friend, restaurant, bus station, explaining a car accident to a police officer, job interview, and others.

**B1–C2, briefly:**

- **B1.** The interaction part has no prep and deliberately confronts the candidate with an *unusual situation or problem*, e.g. refused refund, hotel room mismatch. Part 3 asks the candidate to identify the theme of a short trigger text, then give an opinion in a ~3-minute exposé before questions ([B1 examiner doc](https://www.france-education-international.fr/document/delf-b1-tp-examinateur-ind)).
- **B2.** The candidate states the problem raised by a ~200–250-word press-style document, presents an argued opinion, then defends it in a debate with the examiner ([B2 examiner doc](https://www.france-education-international.fr/document/delf-b2-tp-examinateur-ind)).
- **C2.** A FEI C2 examiner document reportedly recommends that the debate be a genuine exchange: one examiner takes the opposing side while the other assesses ([FEI C2 examiner doc, via search snippet](https://www.france-education-international.fr/document/dalfc2-tp-espacepro-ex1-examinateur-sc)) **[secondary: search-engine snippet, PDF not opened]**.

### A.3 Official scoring grids (the judge rubric)

All grids come from the official sample-paper pages. Each criterion has four tick-box bands, defined as:

- **Band 0:** "Non répondu ou production insuffisante".
- **Band 1:** "En dessous du niveau ciblé".
- **Band 2:** "Au niveau ciblé" at level X.
- **Band 3:** "Au niveau ciblé" at level X+.

Every grid notes that double rating is mandatory and records an individual score plus a harmonised score (*note harmonisée*).

| Level | Task criteria (points at each band 0 / 1 / 2 / 3) | Linguistic criteria, across all parts (bands) | Total |
|---|---|---|---|
| A1 ([grid](https://www.france-education-international.fr/document/grille-po-a1)) | Entretien dirigé 0/1/2.5/4 · Échange d'informations 0/1/2.5/4 · Dialogue simulé 0/1/2.5/4 | Lexique 0/1/3/5 · Morphosyntaxe 0/1/2.5/4 · Phonologie 0/1/2.5/4 | 25 |
| A2 ([grid](https://www.france-education-international.fr/document/grille-po-a2)) | Entretien dirigé 0/1/2.5/4 · Monologue suivi 0/1/2.5/4 · Exercice en interaction 0/1/2.5/4 | Lexique 0/1/3/5 · Morphosyntaxe 0/1/2.5/4 · Phonologie 0/1/2.5/4 | 25 |
| B1 ([grid](https://www.france-education-international.fr/document/grille-po-b1)) | Entretien dirigé 0/1/2.5/4 · Exercice en interaction 0/1/2.5/4 · Expression d'un point de vue 0/1/2.5/4 | Lexique 0/1/3/5 · Morphosyntaxe 0/1/2.5/4 · Phonologie 0/1/2.5/4 | 25 |
| B2 ([grid](https://www.france-education-international.fr/document/grille-po-b2)) | Monologue suivi 0/1/3/5 · Exercice en interaction 0/1/3/5 | Lexique 0/1/3/5 · Morphosyntaxe 0/1/3/5 · Phonologie 0/1/3/5 | 25 |
| C1 ([grid](https://www.france-education-international.fr/document/grille-po-c1)) | Exposé 0/1/3/5 · Entretien 0/1/3/5 | Lexique 0/1/3/5 · Morphosyntaxe 0/1/3/5 · Phonologie 0/1/3/5 | 25 |
| C2 ([grid](https://www.france-education-international.fr/document/grille-copo-c2)) | Présentation du document 0/1/2.5/4 · Point de vue argumenté 0/1/2.5/4 · Débat 0/1/2.5/4 | Lexique 0/1/3/5 · Morphosyntaxe 0/1/2.5/4 · Phonologie 0/1/2.5/4 | 25 × 2 = 50 |

The grid groups the task criteria under *compétences pragmatique et sociolinguistique* and the linguistic criteria under *compétence linguistique*.

**Performance descriptors.** FEI publishes a separate descriptor sheet per level (e.g. [A1 descriptors](https://www.france-education-international.fr/document/descript-perf-po-a1), [A2 descriptors](https://www.france-education-international.fr/document/descript-perf-po-a2)). Each sheet gives one descriptor per criterion for the "below", "at level" and "level+" bands. Paraphrased A1 examples:

| Criterion | Below target (band 1) | At target, A1 (band 2) | A1+ (band 3) |
|---|---|---|---|
| Entretien dirigé | Answers very predictable personal questions, often with isolated words; examiner must repeat and guide | Introduces self; needs prompting to add simple details | Talks about daily life in juxtaposed simple ideas; adds details and examples spontaneously |
| Échange d'informations | Very simple questions, often decontextualised or repetitive | Simple, fairly varied questions linked to the cards | Varied questions that keep the interaction going |
| Dialogue simulé | Needs constant guidance; very brief social contact | Broadly completes the task with guidance; basic politeness | Completes the task with the right speech acts; manages a short social exchange |
| Phonology | Only partly intelligible; examiner must make an effort | Limited repertoire pronounced correctly; some repetition needed | Familiar words pronounced correctly; intelligible throughout |

At A2 the "level+" band adds some things on top: narrating past activities and plans with brief justifications, coherent production with connectors, taking initiative in interaction, appropriate register, and mostly correct pronunciation ([A2 descriptors](https://www.france-education-international.fr/document/descript-perf-po-a2)). The B2 descriptors reportedly ask the candidate to state a *problématique*, announce a plan, use varied connectors and handle concession ([FEI B2 sample page, via search](https://www.france-education-international.fr/diplome/delf-tout-public/niveau-b2/exemples-sujets)) **[secondary: search summary]**.

**Implications for the judge [recommendation]:**

- **Output one of four bands per criterion,** not a continuous score. The point value then follows from the grid. This matches the official form and makes agreement metrics such as QWK natural to compute.
- **Phonology needs signal from the audio.** It is worth 4/25 at A1–B1 and C2, and 5/25 at B2–C1.
- **Lexique, morphosyntaxe and phonology are judged across the whole test,** so the judge needs the full session.
- **Task-achievement criteria are judged per part** and depend on the examiner's behaviour. Phrases like "needs constant guidance from the examiner" mean the judge must see the *examiner turns* too, not only the learner's.

### A.4 Official materials and licensing: what you can reuse

**Available material.** For every level, FEI publishes "exemples de sujets":

- Candidate documents and examiner documents for the speaking test.
- Collective tests, with MP3s for listening comprehension.
- The grids and the descriptors.

([A1](https://www.france-education-international.fr/diplome/delf-tout-public/niveau-a1/exemples-sujets), [A2](https://www.france-education-international.fr/diplome/delf-tout-public/niveau-a2/exemples-sujets), [B1](https://www.france-education-international.fr/diplome/delf-tout-public/niveau-b1/exemples-sujets), [B2](https://www.france-education-international.fr/diplome/delf-tout-public/niveau-b2/exemples-sujets), [C1](https://www.france-education-international.fr/diplome/dalf/exemples-sujets), [C2](https://www.france-education-international.fr/diplome/dalf/dalf-c2-exemples-de-sujets).) I found **no official audio of candidates' speaking performances** on these pages.

**Copyright position.**

- The official candidate document says: "Photocopier, photographier ou réutiliser les sujets du DELF et du DALF est interdit" ([A1 candidate doc](https://www.france-education-international.fr/document/delf-dalf-a1-tp-candidat-ind-sujet-demo)).
- FEI's legal notice says that official documents (e.g. circulars, press releases) are freely reusable with attribution, but all other site content is protected, and reuse needs the author's agreement under art. L.122-4 of the French intellectual property code ([mentions légales](https://www.france-education-international.fr/mentions-legales)).
- The B1/B2/C1 demo subjects also quote **third-party press**: Lire-matin.fr, La Croix, lexpress.fr and 20minutes.fr are credited in the [B1](https://www.france-education-international.fr/document/delf-b1-tp-examinateur-ind) and [B2](https://www.france-education-international.fr/document/delf-b2-tp-examinateur-ind) examiner docs. Those texts carry their publishers' rights.
- FEI's CEFR-illustration videos of spoken French at all six levels may only be used to train examiners and teachers in non-commercial settings, and may not be reproduced ([FEI](https://www.france-education-international.fr/productions-orales-illustrant-les-6-niveaux-du-cecrl)).

**Safe approach [recommendation].**

- **Facts are fine to encode.** Format, durations, part names, point allocations and criteria names can go into the app with attribution and a link.
- **Paraphrase the descriptors** in the judge prompt rather than displaying FEI's text verbatim in the product UI. Link to the official grids.
- **Build a topic taxonomy** (e.g. A1 "obtenir des biens et des services": shop, market, hotel, station, café…) from the demo papers, then **generate original scenarios** in the same style and have them reviewed by a human (see F.2). Never ship FEI subjects or press extracts.
- **Get permission before going commercial at scale.** Email FEI's evaluation and certification department to ask about using the grids and naming "DELF" in marketing. "DELF/DALF" are FEI and French Ministry diplomas, so avoid implying endorsement. **[unverified: trademark status not checked]**

### A.5 Variants and format reforms

- **Junior / scolaire.** Same diplomas and the same value as *tout public*. The skills assessed are identical; only the topics are adapted to teenagers, and "scolaire" is organised through schools ([FEI DELF junior/scolaire](https://www.france-education-international.fr/diplome/delf-junior-scolaire)). The junior/scolaire B1 speaking test also has three parts, 15 minutes plus 10 minutes of prep ([FEI, via search](https://www.france-education-international.fr/en/article/delf-juniorscolaire-niveau-b1)) **[secondary: search summary]**.
- **DELF Pro.** FEI's page returned 403 in the browser, so I couldn't verify it **[unverified]**.
- **Reform history**, from FEI's "Évolution des épreuves du DELF et du DALF", updated 2024-06-24 ([kit évolutions](https://www.france-education-international.fr/document/kit-evolutions-dd)):
  - **Comprehension tests:** open questions removed in favour of MCQs, partly to prepare for possible computer-based delivery. Progressive rollout of the new format for A1–B2 was set for 2024–2025.
  - **Production tests:** new grids, rolled out from late 2021 or early 2022. The 4-band grids above are this new generation.
  - **DELF B1:** collective tests lengthened by 10 minutes from March 2020.
  - **DALF:** specialist domains (humanities vs sciences) removed from C1 production and C2 from March 2020.
- **Since 2024.** I found **no announced reform of the speaking test** taking effect in 2026 on FEI's DELF/DALF pages or in its news list (checked 2026-11-10). Claims of a "nouveau format 2026" came only from low-quality third-party sites **[secondary]**.
- **Related change:** TCF re-marking requests for the speaking and writing tests are suspended for about a year from the 2026-09-01 sessions ([FEI TCF Canada](https://www.france-education-international.fr/test/tcf-canada)).

### A.6 TCF and TEF Canada: the expansion case

| | TCF Canada (FEI) | TEF Canada (CCI Paris Île-de-France) |
|---|---|---|
| Speaking format | Face to face with one examiner, 3 tasks, **12 min including 2 min prep** ([FEI](https://www.france-education-international.fr/test/tcf-canada)) | 15 min: Section A (obtain information, ~5 min) and Section B (convince, ~10 min) ([le français des affaires, via search](https://www.lefrancaisdesaffaires.fr/en/prepare-yourself-for-the-oral-expression-test-of-the-tef/)) **[secondary: search summary of official site]** |
| Scoring | Scored on the NCLC/CLB scale for Immigration, Refugees and Citizenship Canada (IRCC) **[unverified]** | Same **[unverified]** |
| Volume | 124,667 TCF Canada candidates in 2025, the main driver of TCF's +21% ([FEI](https://www.france-education-international.fr/actualites/lettre-fei/2026-02/les-certifications-de-langue-francaise-de-france-education-international-en-forte-hausse)) | n/a |

**Other demand drivers.**

- **TCF IRN**, for French residency and naturalisation applications, has a 10-minute speaking test with 3 tasks ([FEI](https://www.france-education-international.fr/test/tcf-irn)).
- **New French requirements from 2026-01-01:**
  - A2 for a first multi-year residence card ([service-public.fr](https://www.service-public.gouv.fr/particuliers/vosdroits/F34501?lang=fr)).
  - B1 for a first resident card (same source).
  - B2 for naturalisation **[secondary]** ([digischool](https://www.digischool.fr/articles/fle/niveau-de-francais-naturalisation-2026/), [integrationfrance](https://www.integrationfrance.fr/articles/niveau-francais-a2-b1-b2-titre-sejour)).

**[recommendation]** Design the exam engine to be configured from data: parts, timings, roles, grid and prep time. TCF and TEF then become new "exam definitions", not new code. TCF and TEF are shorter, high-volume and immigration-motivated, which means a larger willingness to pay than DELF hobbyists.

---

## B. Real-time voice-to-voice architecture

### B.1 Requirements specific to a speaking exam [recommendation]

1. **Grading-grade transcript.** Word-level timestamps, a faithful record of learner errors, and hesitations kept, separately from whatever drives the live conversation.
2. **Patient turn-taking.** A1/A2 learners pause mid-sentence. An early cut-off ruins realism and depresses the task score. FEI's examiner guidance is literally to speak slowly and reformulate.
3. **A controlled examiner persona.** The examiner should:
   - Follow the part sequence and announce transitions.
   - Never teach or correct during a mock exam.
   - Keep replies short so the learner does the talking.
   - Hold hidden scenario data such as prices.
4. **Timers and phase UI.** Prep timer, card draws and part transitions are driven by a state machine, not by the LLM.
5. **Per-part audio segmentation** for the pronunciation and fluency analysis.
6. **Low latency where it matters.** Fast once the turn is truly over; a deliberate wait inside a turn.

### B.2 Approach 1: cascaded STT → LLM → TTS

**Streaming STT with good French support:**

| Service | French streaming | Turn signals | Price (streaming) | Notes |
|---|---|---|---|---|
| Deepgram **Flux Multilingual** (`flux-general-multi`) | Yes. 10 languages including French, with `language_hint` (GA 2026-04-29) ([Deepgram docs](https://developers.deepgram.com/docs/flux/quickstart), [SiliconANGLE](https://siliconangle.com/2026/04/29/deepgram-expands-flux-10-languages-mid-call-switching-voice-agents/)) | Model-based end of turn (`eot_threshold` default 0.7, `eot_timeout_ms` 500–60,000, default 5,000; `EagerEndOfTurn`/`TurnResumed`); vendor claims ~260 ms end-of-turn ([docs](https://developers.deepgram.com/docs/flux/quickstart)) | $0.0078/min pay-as-you-go ([pricing](https://deepgram.com/pricing)) | Word timestamps. Filler-word tagging is **English only** on Nova models ([docs](https://developers.deepgram.com/docs/filler-words)) |
| Deepgram Nova-3 Multilingual | Yes **[unverified for French accuracy]** | VAD / endpointing | $0.0092/min streaming; $0.0052/min pre-recorded ([pricing](https://deepgram.com/pricing)) | Good candidate for batch re-transcription |
| AssemblyAI Universal-3.6 Pro Realtime | French appears in its language table ([pricing](https://www.assemblyai.com/pricing)) | Built-in turn detection (LiveKit "stt" mode supports AssemblyAI) ([LiveKit](https://docs.livekit.io/agents/build/turns/)) | $0.45/hr base, billed per session hour ([pricing](https://www.assemblyai.com/pricing)) | The vendor itself advises against its $0.15/hr models for voice agents |
| ElevenLabs Scribe v3 Live | 90+ languages ([models](https://elevenlabs.io/docs/overview/models)) | n/a | $0.22/hr; batch Scribe v3 $0.20/hr ([pricing](https://elevenlabs.io/pricing/api)) | Scribe v2 Realtime: ~150 ms median to committed transcript (vendor) |
| OpenAI `gpt-live-transcribe` / `gpt-transcribe` | Multilingual **[unverified for French accuracy]** | n/a | $0.017/min live; $0.0045/min batch ([pricing](https://developers.openai.com/api/docs/pricing)) | |
| Speechmatics | "55+ languages"; French not explicitly listed on the pricing page **[unverified]** | n/a | $0.45–0.80/hr ([pricing](https://www.speechmatics.com/pricing)) | |
| Self-hosted Whisper / faster-whisper | Multilingual | DIY | GPU cost | Known to normalise disfluencies (see C.3) |

**[recommendation]** No source I found gives an independent French word-error-rate (WER) on *learner* (accented, disfluent) speech. Run your own bake-off on 30–50 recorded learner answers; it doubles as a résumé artefact.

**Examiner LLM.** Anthropic models, verified on [Anthropic models overview](https://platform.claude.com/docs/en/about-claude/models/overview.md) and [pricing](https://platform.claude.com/docs/en/about-claude/pricing.md):

| Model ID | Input / output per MTok | Cache read per MTok | Latency class | Notes |
|---|---|---|---|---|
| `claude-haiku-5-5` | $0.10 / $0.50 (prompts ≤100k tokens) | $0.01 | "Fastest" | Default effort `medium`, adaptive thinking |
| `claude-sonnet-5-5` | $2 / $10 | $0.10 | "Fast" | Default effort `high` |
| `claude-opus-5-5` | $4 / $20 | $0.20 | "Moderate" | Default effort `medium`; thinking always on |

All three have 1M context and 128K max output. Claude models take **text and image input only, no audio** ([overview](https://platform.claude.com/docs/en/about-claude/models/overview.md)), so Claude works as the examiner brain or the transcript judge, never as an audio judge.

Alternatives ([OpenAI pricing](https://developers.openai.com/api/docs/pricing), [Gemini pricing](https://aistudio.google.com/docs/pricing)):

- **OpenAI** small models: `gpt-6-luna` at $0.10/$0.50, `gpt-5.6-luna` at $0.20/$1.20.
- **Google:** `gemini-3.8-flash` at $0.75/$3.75 through 2026-12-31, rising to $1.50/$7.50 from 2027-01-01.

**[recommendation]**

- Use Haiku 5.5 for the A1/A2 examiner: short, scripted replies, and the latency matters most.
- Keep Sonnet 5.5 behind a feature flag for B1+ open interaction.
- Put the static scenario and system prompt first so it caches. The minimum cacheable prefix is 286 tokens for these models ([pricing](https://platform.claude.com/docs/en/about-claude/pricing.md)).

**TTS with good French support:**

| Service | French | Latency (stated) | Price |
|---|---|---|---|
| ElevenLabs Flash v2.5 | Yes, 32 languages | ~100 ms median (vendor, excludes network) ([models](https://elevenlabs.io/docs/overview/models)); independent measurements 119–288 ms **[secondary]** ([gradium](https://gradium.ai/content/best-low-latency-tts-apis-2026)) | $0.04 per 1K chars, ≈ $0.04/min ([pricing](https://elevenlabs.io/pricing/api)) |
| ElevenLabs v4 Turbo / v3 Conversational | Yes, 90+ / 70+ languages | ~100 ms / ~165 ms median (vendor) | $0.04 per 1K chars |
| Cartesia Sonic-3.6 | French **[unverified on official page]** | Vendor ~90 ms model; independent ~166 ms first audio **[secondary]** ([futureagi](https://futureagi.com/blog/elevenlabs-vs-cartesia-tts-2026/)) | 1 credit per character, ~750–800 credits/min; $299/mo for 8M credits ≈ $0.0000374/credit ([pricing](https://cartesia.ai/pricing)) |
| Deepgram Aura-2 | **[unverified French]** | n/a | $0.030 per 1K chars ([pricing](https://deepgram.com/pricing)) |
| OpenAI `gpt-4o-mini-tts` | Multilingual | n/a | $0.60/MTok text in, $12/MTok audio out ([pricing](https://developers.openai.com/api/docs/pricing)) |
| Azure Neural / HD voices | fr-FR and fr-CA HD and neural voices; **visemes and blend shapes for fr-FR** ([Azure language support](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=pronunciation-assessment)) | n/a | Pricing page showed no figures **[unverified]** |

### B.3 Approach 2: speech-to-speech realtime models

| Model | Price | Strengths | Concerns for this product |
|---|---|---|---|
| OpenAI `gpt-realtime-2.1` (and `-mini`) | Audio $32 in / $64 out per MTok; cached audio input $0.40; mini $10 / $20 ([pricing](https://developers.openai.com/api/docs/pricing)). User audio = 1 token per 100 ms; assistant audio = 1 token per 50 ms; each response re-sends the whole conversation ([OpenAI cost guide](https://developers.openai.com/api/docs/guides/voice-latency-cost)) | Reasoning and tool use; better silence, noise and interruption handling than v2; 128k context ([model page](https://developers.openai.com/api/docs/models/gpt-realtime-2.1)); `semantic_vad` with `eagerness: low` "lets the user take their time" ([VAD guide](https://developers.openai.com/api/docs/guides/realtime-vad)); 60-min max session ([conversations guide](https://developers.openai.com/api/docs/guides/realtime-conversations)) | Input transcription comes from a **separate ASR** and should be treated as a rough guide ([OpenAI docs, via search](https://developers.openai.com/api/docs/guides/realtime-conversations)); cost depends on best-effort caching; less deterministic script adherence **[recommendation]** |
| OpenAI **GPT-Live** (`gpt-live-1`) | $0.05/min voice layer, billed per second, plus a separately billed backend model ([pricing](https://developers.openai.com/api/docs/pricing), [cost guide](https://developers.openai.com/api/docs/guides/voice-latency-cost)) | Full-duplex front-end voice layer that hands reasoning to a backend model; native ASR transcripts; turn detection ([OpenAI announcement, via search](https://openai.com/index/introducing-gpt-live-1-in-the-api/)), API launched 2026-09-10 **[secondary on date]** | New; billed for all connected time including silence, which matters during learner pauses |
| Google `gemini-3.8-live` | Audio in $3/MTok (≈ $0.005/min); audio out $12/MTok (≈ $0.018/min) ([Gemini pricing](https://aistudio.google.com/docs/pricing)) | Cheapest per minute; input and output transcription with custom vocabulary; French supported; configurable VAD (`silence_duration_ms`, server default ~800 ms) ([capabilities](https://aistudio.google.com/docs/live-api/capabilities)) | Audio-only session capped at **15 min** without context compression; connections last ~10 min, so session resumption is needed ([session docs](https://aistudio.google.com/docs/live-api/session-management)); proactive audio can't be turned off on 3.8 Live ([capabilities](https://aistudio.google.com/docs/live-api/capabilities)) |
| ElevenLabs Agents (Realtime v1 Mini/Max) | $0.08/min plus LLM ([pricing](https://elevenlabs.io/pricing/api)) | Managed stack | Less control |
| Others supported in Pipecat | AWS Nova Sonic, Azure Voice Live, Grok Voice Agent, Ultravox, Inworld Realtime ([Pipecat services](https://docs.pipecat.ai/server/services/supported-services)) | n/a | Not evaluated for French |

**Pros of speech-to-speech for an exam:**

- Prosody-aware turn-taking.
- Lower latency potential.
- A more natural voice.
- Can "hear" pronunciation.

**Cons:**

- Transcript fidelity for grading.
- The persona can drift from the script.
- Harder to swap the LLM.
- Cost from re-reading audio context.
- Hidden state is harder to audit.

**[recommendation]** Use speech-to-speech as an experiment arm, not the backbone.

### B.4 Approach 3: hybrid [recommendation]

Run the conversation on a realtime model (OpenAI or Gemini) for naturalness, and in parallel tee the learner's mic track to a high-accuracy STT and recorder for grading. LiveKit makes this easy because the raw audio track is available to the agent. You get speech-to-speech UX plus grading-grade transcripts. The costs are double STT spend and two vendors.

### B.5 Orchestration frameworks and transport

- **LiveKit Agents** ([GitHub](https://github.com/livekit/agents)):
  - Apache-2.0 framework on top of LiveKit's WebRTC media server, with telephony support.
  - Turn handling modes ([LiveKit turns](https://docs.livekit.io/agents/build/turns/)):
    - turn-detector model (default);
    - `realtime_llm`;
    - `vad`;
    - `stt`, which uses the STT provider's own turn detection, e.g. Deepgram Flux or AssemblyAI;
    - `manual`, for push-to-talk.
  - Interruption controls:
    - `min_duration` and `min_words`;
    - an "adaptive" mode that tells backchannels ("mm-hm") apart from real interruptions;
    - `resume_false_interruption`;
    - `allow_interruptions=False` per utterance.
  - Avatar plugins exist for 16 vendors (see D) ([LiveKit avatars](https://docs.livekit.io/agents/models/avatar/)).
- **Pipecat** (Daily):
  - Python framework, BSD-2 ([pypi](https://pypi.org/project/pipecat-ai/), [docs](https://docs.pipecat.ai/overview/introduction)) **[secondary on licence wording]**.
  - Transports: Daily, LiveKit, SmallWebRTC, WebSocket.
  - Very broad provider list, including Anthropic, Gemini Live, OpenAI Realtime and OpenAI GPT-Live.
  - Avatar services: Anam, bitHuman, HeyGen, Protoface, Simli, Tavus ([supported services](https://docs.pipecat.ai/server/services/supported-services)).
- **WebRTC vs WebSocket [recommendation].**
  - Use WebRTC (LiveKit or Daily) from the browser for jitter buffering, echo cancellation and NAT traversal.
  - Use WebSocket only server-to-vendor, e.g. agent to Deepgram.
  - OpenAI Realtime offers both WebRTC and WebSocket ([search summary](https://community.openai.com/t/new-realtime-models-on-the-api-gpt-realtime-2-1-and-gpt-realtime-2-1-mini/1385896)) **[secondary]**.
- **[recommendation]** LiveKit Agents for Phase 1. It has first-class audio turn detection in French, avatar plugins for Phase 2, Flux in `stt` turn mode, and a Cloud-to-self-host path. Pipecat is an equally valid choice.

### B.6 Turn detection, barge-in and long learner pauses

**Building blocks:**

- **Silero VAD.** MIT, about 2 MB, under 1 ms per 30 ms+ chunk on one CPU thread, 8/16 kHz ([GitHub](https://github.com/snakers4/silero-vad)).
- **LiveKit audio turn detector** ([LiveKit](https://docs.livekit.io/agents/build/turns/turn-detector/)):
  - `v1` runs in the cloud and `v1-mini` on local CPU.
  - Uses acoustic cues (intonation, pitch, rhythm) plus content, without a transcript; 14 languages including French.
  - Endpointing defaults with the audio detector are `min_delay` 0.3 s and `max_delay` 2.5 s.
  - The older text-based detector is deprecated.
- **Pipecat Smart Turn v3.2.** Audio-native, Whisper-Tiny backbone, about 8 MB int8, under 100 ms on most CPUs, 23 languages including French, BSD-2 ([GitHub](https://github.com/pipecat-ai/smart-turn)).
- **Deepgram Flux.** Model-based end of turn, tunable `eot_threshold`, and `eot_timeout_ms` of up to 60 s ([docs](https://developers.deepgram.com/docs/flux/quickstart)).
- **OpenAI `semantic_vad`** (`eagerness: low`) and **Gemini** `silence_duration_ms` / `end_of_speech_sensitivity` ([OpenAI](https://developers.openai.com/api/docs/guides/realtime-vad), [Gemini](https://aistudio.google.com/docs/live-api/capabilities)).

**Patience policy for hesitant learners [recommendation]:**

| Situation | Behaviour |
|---|---|
| Learner pauses mid-sentence (e.g. "Je… euh… j'habite à…") | Use the semantic/acoustic detector. Raise `eot_threshold` (Flux 0.8–0.9) or LiveKit's `unlikely_threshold`. For A1/A2 set `max_delay` to 3–4 s. |
| 5–8 s of silence after an examiner question | Examiner *relance*: repeat the question more slowly, then reformulate it, exactly as the FEI examiner docs instruct. |
| More than ~12–15 s of silence | Move on ("Passons à la question suivante"). Log the event as evidence for the task criterion. |
| Learner talks over the examiner (barge-in) | Allow it, stop TTS quickly, and use LiveKit adaptive mode so backchannels don't cut the examiner off. |
| Monologue parts (A2 part 2, B2 part 1, C1 exposé) | **Disable end-of-turn responses**: the examiner only listens until the learner says they're done or the part's timer ends. Use the `manual` turn mode or `commit_user_turn()` ([LiveKit](https://docs.livekit.io/agents/build/turns/)). |
| Practice mode | Optional "Je réfléchis" button (push-to-hold) and a visual "examiner is listening" indicator. |

**[recommendation]** Make patience a per-level setting and tune it on recorded learner sessions. Report the false cut-off rate (examiner spoke while the learner wasn't done) as a key metric.

### B.7 Model choice summary [recommendation]

| Role | Primary | Alternative | Why |
|---|---|---|---|
| Examiner (A1/A2) | `claude-haiku-5-5`, low effort, prompt-cached scenario | `gpt-6-luna` / `gemini-3.8-flash` | Short scripted turns; latency first; cheap |
| Examiner (B1+) | `claude-sonnet-5-5` | `claude-opus-5-5` for C1/C2 debate | Argumentation quality |
| Judge (transcript + features) | `claude-opus-5-5` | `claude-sonnet-5-5`; GPT-6.x | Rubric reasoning; structured output |
| Second judge (double évaluation) | Different family, e.g. `gemini-3.8-flash` with **audio input** | `gpt-audio-1.5` | Family diversity reduces correlated errors; audio access for phonology |
| Feedback writer | `claude-sonnet-5-5` | n/a | Long, pedagogical French |

### B.8 Per-session cost estimates (arithmetic)

**Assumed session [recommendation]:** an A2 mock exam with 10 minutes of prep (session paused, nothing streaming) and a **12-minute connected live session**:

- 6 min of learner speech, 4 min of examiner speech, 2 min of silence.
- 25 examiner turns.
- Live talk is 6–8 min officially; the extra time is the introduction and transitions.

**Option A: cascaded (Flux + Haiku 5.5 + ElevenLabs Flash)**

| Item | Calculation | Cost |
|---|---|---|
| Streaming STT (Flux Multilingual, pay-as-you-go) | 12 min × $0.0078 | $0.094 |
| Examiner LLM (Haiku 5.5) | 25 turns × ~3,000 input tokens = 75k, with ~90% cache reads: 7.5k uncached × $0.10/M + 7.5k cache-write × $0.125/M + 67.5k cache-read × $0.01/M + output 25 × 60 = 1.5k × $0.50/M | ≈ $0.003 |
| (Examiner LLM if Sonnet 5.5) | 7.5k × $2 + 7.5k × $2.5 + 67.5k × $0.10 + 1.5k × $10, all per M (excluding thinking tokens) | ≈ $0.056 |
| TTS (ElevenLabs Flash) | 4 min ≈ 4,000 chars × $0.04/1K | $0.16 |
| (TTS if Cartesia, Scale plan) | 4 min × ~800 credits × $0.0000374 | ≈ $0.12 |
| **Live conversation subtotal** | | **≈ $0.22–0.31** |

**Grading (applies to every option)**

| Item | Calculation | Cost |
|---|---|---|
| Batch re-transcription | 6 min × $0.0045 (`gpt-transcribe`) or × $0.0052 (Nova-3 Multi) | ≈ $0.03 |
| Judge, lean (`claude-opus-5-5`) | 3 calls (all 6 criteria per call, 3 samples) × (8k input, ~2k output incl. thinking): input 24k × $4/M ≈ $0.10 (less with caching), output 6k × $20/M = $0.12 | ≈ $0.15–0.22 |
| Judge, thorough | 6 criteria × 3 samples = 18 calls × (6.5k input mostly cached, ~1.5k output): cache write 6k × $5/M = $0.03; reads 17 × 6k × $0.20/M = $0.02; uncached 9k × $4/M = $0.036; output 27k × $20/M = $0.54 | ≈ $0.63 |
| Pronunciation (Azure) | Billed like STT on ~6 min ([Azure docs](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/how-to-pronunciation-assessment)); rate not visible on the pricing page | **[unverified]** |

Notes on grading:

- The Batch API halves Claude prices if grading can be asynchronous, but batch completion time is unbounded, so it suits only "results by email".
- **Option A total:** about **$0.40–0.95 per session**. So 1,000 mock exams a month cost roughly $400–950 in API spend, excluding LiveKit and hosting.

**Option B: speech-to-speech (`gpt-realtime-2.1`)**

| Item | Calculation | Cost |
|---|---|---|
| Audio tokens | Learner 6 min × 600 = 3,600 tokens; examiner 4 min × 1,200 = 4,800 tokens | n/a |
| Context replay | Each of 25 responses re-sends the history. Average history ≈ (3,600 + 4,800)/2 + 2,000 text ≈ 6,200 tokens, so ≈ 155k input tokens | n/a |
| Best case (good caching) | Uncached audio 8.4k × $32/M = $0.27; text 2k × $4/M = $0.008; cached 145k × $0.40/M = $0.058; output audio 4.8k × $64/M = $0.31 | ≈ **$0.65** |
| Worst case (no cache hits) | ~153k audio input × $32/M ≈ $4.90 + $0.31 | ≈ **$5.2** |
| `gpt-realtime-2.1-mini` best case | ≈ 1/3.2 of the above | ≈ $0.20 |
| GPT-Live | 12 min × $0.05 + backend LLM | ≈ $0.60 + backend |
| Gemini 3.8 Live | 12 min × $0.005 + 4 min × $0.018 | ≈ $0.13, **[unverified]** whether context re-reads add cost |
| Plus grading (same as Option A) | | +$0.18–0.66 |

**Option C: résumé-max (cascaded + avatar + pronunciation).** Option A plus the avatar minutes (prices in D, 12 min each):

| Avatar | Cost per session |
|---|---|
| Simli | ≈ $0.11–0.12 |
| bitHuman cloud | ≈ $0.48 |
| LiveAvatar LITE | ≈ $1.56 **[secondary]** |
| Anam | ≈ $1.3–1.9 |
| Tavus | ≈ $3.1–4.2 |

### B.9 Latency budget

Measure **response latency** from the learner's last voiced frame to the first examiner audio frame at the client. Report the *deliberate patience wait* separately from the *system latency*.

| Stage (cascaded) | Target p50 | Target p95 | Basis |
|---|---|---|---|
| End-of-turn decision after the learner stops (patience, A1/A2) | 0.8–1.5 s (deliberate) | ≤ 3 s | Design choice; Flux claims ~260 ms end-of-turn ([docs](https://developers.deepgram.com/docs/flux/quickstart)); LiveKit `max_delay` default 2.5 s ([docs](https://docs.livekit.io/agents/build/turns/turn-detector/)) |
| Final transcript available | Included in the above (Flux) | n/a | Vendor claim |
| LLM time to first token (Haiku 5.5, cached prefix, low effort) | 300–600 ms | < 1 s | **[unverified: measure]** Anthropic only gives relative latency ("Fastest") |
| First sentence → TTS first audio | 100–200 ms | 350 ms | ElevenLabs ~100 ms median (vendor); Cartesia ~166 ms (independent) **[secondary]** |
| WebRTC transport and jitter buffer | 50–150 ms | 250 ms | **[unverified estimate]** |
| **System latency, excluding the deliberate wait** | **≈ 0.6–1.0 s** | **≤ 1.6 s** | [recommendation] |
| Phase 2 avatar render | +100–300 ms | +500 ms | **[unverified]**; LiveKit exposes `AvatarMetrics` playback latency ([docs](https://docs.livekit.io/agents/models/avatar/)) |

**Tricks to hit the budget [recommendation]:**

- Stream LLM output to TTS sentence by sentence.
- Use Flux `EagerEndOfTurn` to start drafting replies early. This costs 50–70% more LLM calls ([docs](https://developers.deepgram.com/docs/flux/quickstart)), which is negligible with Haiku.
- Pre-synthesise fixed examiner lines (greetings, part transitions, relances).
- Keep the scenario prefix cached.

---

## C. Assessment: LLM-as-judge

### C.1 How G-Eval works

From [Liu et al., 2023, arXiv 2303.16634](https://arxiv.org/html/2303.16634v3):

1. **Auto-CoT.** Give the LLM the task introduction and criteria only; it writes detailed evaluation steps, which are then reused in the scoring prompt.
2. **Form-filling.** Prompt = instructions + generated steps + source + target. The model fills a form with a score per aspect, rather than scoring by output likelihood as GPTScore does.
3. **Probability-weighted score.** score = Σᵢ p(sᵢ)·sᵢ over the allowed scores. With GPT-4 there were no logprobs, so the authors **sampled 20 times** (temperature 1) to estimate p.
4. **Reported results:**
   - Spearman 0.514 with humans on summarisation.
   - Topical-Chat dialogue averages r = 0.575 and ρ = 0.588.
   - Possible **bias toward LLM-written text**.
   - Without probabilities, many ties.

**Libraries.**

- **DeepEval `GEval`.**
  - Parameters: `criteria` or `evaluation_steps`, `evaluation_params`, `rubric` (non-overlapping score ranges on 0–10), `threshold`, `strict_mode`, custom `model`.
  - Uses logprob weighting when the model exposes token probabilities; otherwise falls back to the raw score.
  - Offers `DAGMetric` for deterministic decision trees ([DeepEval docs](https://deepeval.com/docs/metrics-llm-evals)).
- **Langfuse** has built-in LLM-as-judge evaluators, datasets and experiments; MIT core, self-hostable, built on OpenTelemetry ([GitHub](https://github.com/langfuse/langfuse)).

### C.2 Adapting G-Eval to the DELF grids [recommendation]

- **Unit of judgement:** one (criterion, part) pair. Task criteria are scored per part; lexique, morphosyntaxe and phonology use the whole session.
- **Prompt contents:**
  - The level's paraphrased descriptors for bands 1–3, plus the band-0 definition.
  - Fixed evaluation steps, generated once with Auto-CoT, then **frozen and version-controlled**.
  - The transcript with **speaker labels and timestamps**.
  - Examiner turns, so "needed guidance" is visible.
  - Scenario metadata.
  - Computed fluency and pronunciation features as text.
- **Output via structured output** (Claude: `output_config.format`, per Anthropic API reference):
  - `{band: 0|1|2|3, evidence: [quotes with timestamps], missing: [...], confidence}`.
  - Evidence quotes must be exact substrings of the transcript, validated in code.
- **Band distribution:**
  - **Claude's Messages API does not expose token logprobs [unverified negative]**, and the 2026-10-21 API version rejects `temperature` ([Anthropic API reference, cached 2026-11-03](https://platform.claude.com/docs/en/about-claude/models/overview.md)). So estimate p(band) G-Eval-style by **n independent samples** (n = 3–5 in production, n = 10–20 in offline evals).
  - Report the expected points E[pts] = Σ p(band)·pts(band) **and** the modal band.
  - Show the learner the modal band. Use the spread as an uncertainty signal; if it's wide, say "borderline A2 / A2+".
- **Double évaluation:** judge A (Claude Opus 5.5 on transcript + features) and judge B (an audio-capable model from another family). If they differ by ≥ 2 bands, run a third adjudication pass with both rationales. This mirrors FEI's *note harmonisée*.
- **Scoring math:** sum the band points (0/1/2.5/4 or 0/1/3/5) to /25. Never let the LLM add up points itself.
- **Guardrails:**
  - Practice and mock outputs must state they're *estimates*, not official DELF results.
  - Penalise only what the grid penalises. Don't let the judge reward length per se; test for length bias in C.5.

### C.3 Limits of transcript-only grading

- **Phonology is invisible in text,** and fluency is only partly visible.
- **ASR also distorts the learner signal:**
  - LearnerVoice reports that L2 spontaneous speech has far more disfluencies and ungrammatical forms than native speech, and that these cause many ASR errors: 54.2% of vanilla Whisper's errors came from L2 features ([arXiv 2407.04280](https://arxiv.org/abs/2407.04280)).
  - Other work notes that standard ASR tends to drop hesitations, and that ASR output can introduce spurious grammar edits ([arXiv 2506.04076](https://arxiv.org/html/2506.04076v1), via search summary) **[secondary]**.
- **Mitigations [recommendation]:**
  - Choose verbatim-leaning ASR settings and benchmark error-preservation on learner French.
  - Keep word-level confidence; tell the judge to treat low-confidence words as uncertain rather than as errors.
  - Use two ASR engines and flag disagreements.
  - Optionally let an audio model listen to flagged segments.

### C.4 Pronunciation and fluency signals

| Option | French support | What you get | Caveats |
|---|---|---|---|
| **Azure AI Speech Pronunciation Assessment** | **fr-FR and fr-CA** among 33 locales ([language support](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=pronunciation-assessment)) | Accuracy, fluency, completeness, `PronScore`; phoneme-level results in IPA; scripted (reference text) and unscripted modes ([how-to](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/how-to-pronunciation-assessment)) | **Prosody is en-US only**; syllable-level is en-US only; content assessment is retired. Microsoft recommends running STT first, then a *scripted* assessment with the transcript as reference, for accuracy. Audio over 30 s needs continuous mode. Billed like STT |
| **Speechace** | fr-fr and fr-ca ([supported languages](https://api-docs.speechace.com/getting-started/supported-languages)) | Word and sentence pronunciation, read-aloud fluency, unscripted `score/speech` and `score/task` ([French solution page](https://api-docs.speechace.com/solutions/speaking-practice-in-spanish-and-french)) | No grammar, vocabulary or coherence for French; no stress or intonation (English only); pricing **[unverified]** |
| **Forced alignment** (Montreal Forced Aligner) | French MFA acoustic models v2.0.0, v2.0.0a, v3.0.0, CC BY 4.0 ([MFA models](https://mfa-models.readthedocs.io/en/latest/acoustic/French/index.html)) | Phone and word boundaries for computing timing and pause features, and goodness-of-pronunciation (GOP) scores | DIY; needs a pronunciation dictionary |
| **Phoneme recognition** (`facebook/wav2vec2-xlsr-53-espeak-cv-ft`) | Multilingual phonemes, Apache-2.0 ([HF](https://huggingface.co/facebook/wav2vec2-xlsr-53-espeak-cv-ft)) | Recognised phone string to compare with the expected phonemisation of the transcript (e.g. from espeak) | Research-grade; needs calibration on learner data |
| **Timing-derived fluency features** [recommendation] | Any ASR with word timestamps (Flux, Nova-3, Scribe) | Speech rate (words/min), articulation rate (excluding pauses), mean length of run, count and mean duration of silent pauses (> 250 ms) **within** vs **between** clauses, filled-pause count ("euh", "bah", "ben"), self-repairs, examiner-to-learner talk ratio | French filled pauses need explicit handling (Deepgram filler tagging is English only, [docs](https://developers.deepgram.com/docs/filler-words)) |
| **Audio-native LLM judge** | `gpt-audio-1.5` ($32 / $64 per MTok audio, [pricing](https://developers.openai.com/api/docs/pricing)); Gemini 3.8 models (audio input **[unverified pricing line]**) | Holistic "intelligibility / accent impact" band with quoted timestamps | Unvalidated for DELF; research shows multimodal LLM speaking assessment improving: holistic PCC 0.783 → 0.846, delivery the hardest aspect ([arXiv 2508.12591](https://arxiv.org/abs/2508.12591)) |

**[recommendation]** Map these to the phonology band as follows:

1. Compute Azure `AccuracyScore` and `FluencyScore`, intelligibility proxies (proportion of low-confidence ASR words, examiner repeat requests) and audio-LLM judgements.
2. Give all of them to the judge as features.
3. Fit a small **ordinal regression** from features to human phonology bands once the gold set exists. This is safer than trusting any one vendor score.
4. The CEFR Companion Volume (2020) phonology scale (overall, sound articulation, prosody) foregrounds **intelligibility over native-likeness**, which supports this mapping ([CoE CV 2020](https://rm.coe.int/cefr-companion-volume-with-new-descriptors-2020/16809ea0d4)).

### C.5 Calibration and validation: the eval harness [recommendation]

**Gold set.**

- 100–200 consented mock sessions: A1/A2 first, varied first languages, devices and noise conditions.
- Each one **independently double-rated** by two trained raters, ideally DELF-habilitated examiner-correctors, on the official grid. Disagreements of 2 or more bands go to adjudication.
- Store the band per criterion, rater IDs, and the timestamped evidence each rater cites.

**Metrics:**

- Per-criterion **QWK** (`sklearn.metrics.cohen_kappa_score(..., weights="quadratic")`, [docs](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.cohen_kappa_score.html)).
- Exact-band and adjacent-band (±1) agreement.
- MAE on the /25 total.
- Agreement on the "≥ 12.5/25" proxy and on the 5/25 elimination threshold ([FEI rules](https://www.france-education-international.fr/diplome/delf-tout-public/niveau-a1)).
- Bootstrapped 95% confidence intervals.
- **Human–human QWK as the ceiling.** The target is judge–human ≈ human–human.

**Ablations to report:**

- Transcript-only vs + timing features vs + Azure pronunciation assessment vs + audio-LLM.
- Single judge vs self-consistency n = 5 vs two-family double évaluation.
- Haiku vs Sonnet vs Opus judges.
- ASR engine A vs B.

**Bias and robustness tests:**

- First-language and accent groups; gender.
- Audio quality (add noise, phone codec).
- Answer length.
- Order of parts.
- Paraphrase-invariance of the prompts.
- Self-preference: score TTS-synthesised "model answers" vs human answers of equal human-rated quality. G-Eval itself flags an LLM-text bias ([arXiv 2303.16634](https://arxiv.org/html/2303.16634v3)).

**Regression CI:** every prompt, model or ASR change re-runs the gold set; versions and results are stored in Langfuse datasets ([Langfuse](https://github.com/langfuse/langfuse)).

**Existing corpora.** I found none that is openly licensed, CEFR-labelled *and* spoken French learner speech:

| Corpus | What it is | CEFR labels? | Licence / access |
|---|---|---|---|
| FEI/CIEP "Productions orales illustrant les 6 niveaux du CECRL" | Teenagers 13–18, French among 5 languages, levels assigned at a 2008 expert seminar, with commentary PDFs | Yes (illustrative) | **Non-commercial examiner and teacher training only; no reproduction** ([FEI](https://www.france-education-international.fr/productions-orales-illustrant-les-6-niveaux-du-cecrl)) |
| LANGSNAP (SLABank / TalkBank) | Oral interviews and narratives of UK learners of French, with anonymised audio and CHAT transcripts ([TalkBank](https://slabank.talkbank.org/access/French/LANGSNAP6.html)) | Not CEFR **[unverified]** | Citation required; TalkBank ground rules; exact licence **[unverified]** |
| FLLOC (Southampton) | French learner oral corpora, school and university ([archive](https://web-archive.southampton.ac.uk/www.flloc.soton.ac.uk/list.html)) | **[unverified]** | **[unverified]** |
| IPFC | International interphonology corpus of FLE learners ([project](https://cblle.tufs.ac.jp/ipfc/index9.html)) | **[unverified]** | Contact the project team **[secondary]** |
| Japanese learners of French, CEFR-rated by 3 teachers (IRIT, Interspeech 2022) | Phonetic and linguistic features with A1–C2 ratings ([search result](https://gitlab.irit.fr/samova/linguistic_features)) | Yes | **[unverified]** |
| Speak & Improve 2025 | ~315 h of L2 **English** with holistic scores; a methodological template ([arXiv 2412.11985](https://arxiv.org/abs/2412.11985)) | Holistic scores | English only |

### C.6 Feedback generation [recommendation]

- **Per part:** what you did well, mapped to "at level" descriptor language, and the top 2 things that would move you up one band, with concrete examples.
- **Error taxonomy** (French-specific, A1–B1):
  - Agreement (gender and number).
  - Verb conjugation and tense (passé composé auxiliary *être/avoir*, past-participle agreement).
  - Articles and partitives.
  - Prepositions with places.
  - Question formation.
  - Negation placement.
  - Register (tu/vous).
  - Politeness formulas.
  - Lexical gaps, anglicisms and code-switching.
  - Pronunciation targets: nasal vowels, /y/ vs /u/, final consonants, liaison.
- **Corrections:** only for errors evidenced in the transcript with high ASR confidence. Show the original, a minimal correction and the rule. Cap at about 5 per part to avoid overload.
- **Model answer:** a rewritten "A2+" version of the learner's own answer that keeps their content. A separate TTS clip lets them hear it, and they can practise by shadowing.
- **Drill generation:** spaced-repetition items from the recurring errors, which feeds adaptive practice in later sessions.
- **Rubric transparency:** show the band per criterion and the cited evidence. Never present it as an official result.

---

## D. Phase 2: talking examiner avatar

| Option | Pricing (verified page) | Integration | French / lip-sync | Notes |
|---|---|---|---|---|
| **Simli** | Hobby $10 for 1,000 min ($0.01/min); Pro $49 for 5,500 min; Scale $249 for 27,500 min ($0.009); enterprise from $0.005 ([pricing](https://www.simli.com/pricing)) | LiveKit and Pipecat plugins ([LiveKit](https://docs.livekit.io/agents/models/avatar/), [Pipecat](https://docs.pipecat.ai/server/services/supported-services)) | Driven by audio; language support not stated on the pricing page **[unverified]** | Cheapest real-time option |
| **bitHuman** | 2 credits/min self-hosted (~$0.02), 4/min cloud (~$0.04), 10/min managed (~$0.10); $1 per 100 credits ([pricing](https://www.bithuman.ai/pricing)) | LiveKit and Pipecat plugins | **[unverified]** | Renders on-device (iOS, Android, Mac, Linux, WebGPU), so it can scale cheaply |
| **Anam** | $49/mo for 250 min, overage $0.14/min; Growth $299 for 2,000 min, $0.12/min; enterprise from $0.04/min; billed per second ([pricing](https://anam.ai/pricing)) | LiveKit (Python/Node) and Pipecat | "70+ languages" ([pricing](https://anam.ai/pricing)) | Photoreal |
| **LiveAvatar (HeyGen)** | LITE 1 credit/min, FULL 2 credits/min ([docs](https://docs.liveavatar.com/docs/lite-mode/overview)); about $0.13/min LITE on the Starter plan **[secondary]** ([HeyGen help, via search](https://help.heygen.com/en/articles/10035615-how-to-get-started-with-liveavatar)) | LITE mode takes your own STT/LLM/TTS audio; LiveKit and Pipecat plugins | **[unverified]** | HeyGen's Streaming API is deprecated in favour of LiveAvatar, and the sunset messaging conflicts **[secondary]** ([HeyGen docs](https://docs.heygen.com/docs/streaming-api-deprecated)) |
| **Tavus CVI** | Builder $59 for 175 min (overage ~$0.35/min); Growth $397 for 1,300 min (~$0.31/min); 30 s minimum per conversation ([pricing](https://www.tavus.io/pricing)) | LiveKit and Pipecat plugins | 30+ or 42+ languages (inconsistent on the page) | Phoenix-4.5 rendering, Sparrow-2 turn-taking; priciest |
| **D-ID** | API pricing page not readable **[unverified]** | LiveKit plugin ([LiveKit](https://docs.livekit.io/agents/models/avatar/)) | **[unverified]** | V4 Expressive avatars |
| **Pre-rendered clips** | One-off generation cost | Play clips for fixed lines (greeting, instructions, transitions, relances) and an idle loop; use a "listening" loop while the learner talks | Exact, since the lines are scripted | **[recommendation]** Best realism-per-dollar for a mock exam: most examiner lines in A1/A2 are formulaic, and the dynamic replies can be audio over a "talking" loop |
| **3D/2D in browser** | Free (MIT) | **TalkingHead** (three.js): visemes from TTS word timestamps; **has a French lip-sync module**; works with ElevenLabs WebSocket timestamps or Azure visemes ([GitHub](https://github.com/met4citizen/TalkingHead)). Azure provides viseme IDs and blend shapes for fr-FR ([Azure](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=pronunciation-assessment)) | Good | **Ready Player Me shut down its public services in January 2026** after Netflix acquired it **[secondary]** ([TechCrunch](https://techcrunch.com/2025/12/19/netflix-acquires-gaming-avatar-maker-ready-player-me/), [FrameVR](https://learn.framevr.io/blog/rpm-closure)), so use Avaturn, Avatar SDK MetaPerson, VRoid or MPFB models instead. Rive and Live2D are 2D alternatives **[not researched in depth]** |

**[recommendation] Phase 2 plan:**

1. Start with **pre-rendered clips + TalkingHead or Simli** behind a feature flag.
2. Measure added latency through LiveKit `AvatarMetrics` and learner-rated realism.
3. Only then consider Anam or Tavus for a premium tier.
4. Use `wait_for_join()` so video is live before the first examiner line ([LiveKit](https://docs.livekit.io/agents/models/avatar/)).
5. Avoid photoreal likenesses of real people. Disclose that the examiner is AI; also expected under the EU AI Act transparency rules **[unverified applicability]**.

---

## E. Phase 3: B1 to C2

**What changes technically:**

1. **Longer monologues.** 5–7 min at B1 part 3 and B2 part 1; 8–10 min for the C1 exposé ([grids](https://www.france-education-international.fr/document/grille-po-c1)).
   - Switch to listen-only mode with no end-of-turn replies.
   - Show a visible timer.
   - Have the examiner time-box the part politely.
   - Record and transcribe in chunks.
2. **Argument evaluation.** B2 descriptors ask for a problem statement, an announced plan, connectors and concession (see A.3, [secondary]). The examiner must defend a contrary view. **[recommendation]** Do structured argument extraction first: thesis, plan, arguments, examples, counter-arguments, concessions, conclusion. Then judge task achievement against that structure, and plan debate moves that target weak premises.
3. **Document-based preparation.**
   - B1: a short trigger text.
   - B2: a ~250-word article.
   - C1: a dossier of several written documents.
   - C2: an **audio document** heard twice ([C2](https://www.france-education-international.fr/article/dalf-c2)).
   - **[recommendation]** Generate original press-style documents with an LLM, fact-check them, and get human review; for C2, render them as multi-voice audio with TTS. Don't scrape press articles: the FEI samples' press extracts are third-party copyrighted (A.4). Also consider openly licensed or public-sector sources whose licences you verify one by one **[unverified per source]**.
4. **Examiner roles.** C1/C2 juries have two examiners; at C2 one may play the opposing side ([secondary, A.2]). **[recommendation]** Use two voices or avatars, with the "contradictor" agent having its own persona and goals.
5. **Harder rubric judgements.** Distinguishing C1 from C1+ on lexis and morphosyntax needs judges at high effort with calibrated exemplars. Agreement will be lower, so report it honestly per level.
6. **Prep phase UX.** 30–60 minutes with notes allowed. Offer note-taking in the UI, but hide the notes during the exposé, as in the real exam **[unverified rule; check the candidate manual]**.

---

## F. Product, scaling and the résumé angle

### F.1 Suggested stack [recommendation]

| Layer | Choice | Why |
|---|---|---|
| Frontend | Next.js + LiveKit React components | Fast UI; React hooks for agent tracks ([LiveKit](https://docs.livekit.io/agents/models/avatar/)) |
| Realtime | LiveKit Cloud, then self-host | WebRTC, agent dispatch, recording |
| Agent | Python LiveKit Agents worker | Plugins, turn detection |
| Backend API | FastAPI or Next.js route handlers | Session creation, tokens, grading jobs |
| Auth / DB / storage | Supabase in an EU region: Postgres + RLS + Storage, or Postgres + S3-compatible storage | Simple; EU residency |
| Jobs | Postgres queue (pgmq) or Celery/Arq | Asynchronous grading pipeline |
| Observability | Langfuse (LLM traces, evals), OpenTelemetry spans for voice latency | ([Langfuse](https://github.com/langfuse/langfuse)) |
| Payments (later) | Stripe | Subscriptions and session packs |

### F.2 Content pipeline and question-bank schema [recommendation]

```ts
type ExamDefinition = {               // data-driven: DELF A1..C2, TCF, TEF
  id: "delf-a1-tp" | "delf-a2-tp" | ...;
  parts: { key: "entretien_dirige" | "echange_informations" | "dialogue_simule" | ...;
           prepMinutes: number; targetMinutes: [number, number];
           turnMode: "interactive" | "monologue_listen_only";
           criteria: CriterionRef[] }[];
  grid: { criterion: string; bandPoints: [0, number, number, number]; scope: "part" | "global" }[];
  provenance: { source: "FEI grille", url: string, retrievedAt: string };
};

type TaskItem = {
  id: string; examId: string; partKey: string; level: "A1" | "A2" | ...;
  variant: "tout_public" | "junior_scolaire";
  objective: string;                  // paraphrase of FEI objective, e.g. "obtenir des biens et services"
  themeTaxonomy: string[];            // e.g. ["achats", "hôtel"], derived from demo papers
  candidatePromptFr: string;          // ORIGINAL text, never copied
  examinerRole?: string;              // "réceptionniste de l'hôtel"
  examinerOnlyData?: Record<string, unknown>;  // price list, timetable…
  expectedSpeechActs: string[];       // saluer, demander le prix, payer, remercier
  lexicalField: string[]; difficulty: number;  // IRT-style parameter after data collection
  cards?: string[];                   // A1 échange d'informations keywords
  status: "draft" | "reviewed" | "retired"; reviewer?: string; version: number;
  generation: { model: string; promptVersion: string; createdAt: string };
};
```

**Pipeline:**

1. Derive the taxonomy from FEI demo papers.
2. LLM-generate candidate items per taxonomy cell.
3. Run automatic checks: level-appropriate vocabulary against a CEFR inventory, no overlap with FEI text (n-gram similarity), and complete examiner-only data.
4. Human FLE-teacher review.
5. Publish.
6. Collect performance data, then estimate difficulty and use it for adaptive selection.

FEI publishes an "Inventaire linguistique des contenus clés des niveaux du CECRL" that can guide level-appropriate lexis ([link on the A1 page](https://www.france-education-international.fr/diplome/delf-tout-public/niveau-a1)). Check its licence before ingesting it **[unverified]**.

### F.3 Privacy, compliance and audio retention

- **GDPR.** Voice recordings are personal data. Per the EDPB, processing voice to **identify** a user is biometric processing under art. 4(14) and needs an art. 9 exemption, realistically explicit consent ([EDPB Guidelines 02/2021](https://www.edpb.europa.eu/system/files/2021-07/edpb_guidelines_202102_on_vva_v2.0_adopted_en.pdf)). **[recommendation]**
  - Never build voiceprints or speaker identification.
  - Process audio only for assessment and feedback, on a contract or consent basis.
  - Get separate opt-in consent before using recordings to improve models or to build the gold set.
- **Retention [recommendation].**
  - Keep raw audio for 30 days by default, for replay and re-grading, then delete it automatically through storage lifecycle rules.
  - Keep transcripts, features and scores until the account is deleted.
  - Let users delete individual sessions.
  - Use EU-region storage.
  - Sign data processing agreements (DPAs) with vendors; enable zero-retention options where they exist (e.g. Anam and Simli enterprise tiers mention zero data retention: [Anam](https://anam.ai/pricing), [Simli](https://www.simli.com/pricing)).
  - Check each vendor's data residency (Deepgram offers EU endpoints for Flux per [SiliconANGLE](https://siliconangle.com/2026/04/29/deepgram-expands-flux-10-languages-mid-call-switching-voice-agents/) **[secondary]**).
- **Minors.** DELF junior/scolaire targets teenagers. **[recommendation]** Launch adults-only; consent rules for children (e.g. France's age 15 for information-society services) need legal review **[unverified]**.
- **EU AI Act.**
  - Annex III point 3(b) lists AI systems used to "evaluate learning outcomes" in education and vocational training *institutions* as high-risk ([AI Act Annex III](https://artificialintelligenceact.eu/annex/3/)).
  - The Digital Omnibus reportedly moved Annex III obligations from 2026-08-02 to **2027-12-02** **[secondary]** ([Gibson Dunn](https://www.gibsondunn.com/eu-ai-act-omnibus-agreement-postponed-high-risk-deadlines-and-other-key-changes/), [Lewis Silkin](https://www.lewissilkin.com/insights/2026/07/27/the-digital-omnibus-on-ai-enters-into-force-today-102nedo)).
  - A self-study consumer app may fall outside "institutions", but **B2B sales to language schools could pull it in**. This is an open legal question.
- **Canada (TCF expansion).** Get a PIPEDA and Québec Law 25 review before launch **[not researched]**.

### F.4 What makes it technically impressive [recommendation]

1. **A judge validated against humans.** Publish a model card: gold-set size, per-criterion QWK with confidence intervals versus the human–human ceiling, ablations (C.5), and bias tests.
2. **A measured latency budget.** p50/p95 response latency and false cut-off rate per level, broken down by stage, on a live Grafana or Langfuse dashboard.
3. **An ASR bake-off on learner French.** WER *and* "error-preservation rate" (how many learner grammar errors survive transcription).
4. **Pronunciation and fluency modelling.** Timing features plus Azure PA plus an ordinal regression calibrated to human phonology bands.
5. **A data-driven exam engine.** Adding TCF Canada should be a config file, not new code.
6. **Adaptive practice.** Item difficulty estimates and learner ability from the score history; target items near the ability level.
7. **Experiments.** Cascaded vs speech-to-speech arm, measured on realism ratings, latency, cost and grading agreement.
8. **Engineering hygiene.** Prompt and version registry, eval CI gate, cost per session tracked, traceable evidence for every score.

### F.5 Competitive landscape

All claims here are vendor self-descriptions **[secondary]**.

| Product | Focus | Link |
|---|---|---|
| DELF & TCF: OralPrep (iOS) | AI tutor that listens, scores and suggests improvements for DELF/TCF speaking | [App Store](https://apps.apple.com/ae/app/id6772313115) |
| TCF Exam Hero (iOS) | TCF speaking tasks 1–3 with an estimated CLB range | [listing](https://mwm.ai/apps/tcf-exam-hero/6757088210) |
| TCF-Canada Speaking Test Coach | AI examiner simulation of the 3 TCF oral parts | [listing](https://mwm.ai/apps/tcf-canada-speaking-test-coach/6753697803) |
| Talkparty | General French speaking app; rubric-based DELF feedback claimed | [site](https://www.talkparty.app/improve-french) |
| Praktika | General AI tutor; publishes DELF prep content | [blog](https://praktika.ai/blog/delf-b2-preparation-honest-faq) |
| Penvo, PrepMyFrench, Univext | TEF/TCF prep with AI correction; general AI tutor | [Penvo](https://penvo.pages.dev/), [PrepMyFrench](https://www.producthunt.com/products/prepmyfrench), [Univext](https://univext.com/en/blog/274/how-to-pass-delf-dalf-exam-with-ai-2026) |

**Differentiation [recommendation]:**

- Faithful exam *procedure*: prep timer, card draws, examiner-only data, patient examiner, transitions.
- Official grid bands with cited evidence.
- **Published agreement metrics,** which none of the listed competitors appear to publish.
- Pronunciation measured, not guessed.
- A realistic visible examiner.
- Practice mode separate from mock mode.

---

## G. Recommendation

### G.1 Three end-to-end options

| | **1. Lean MVP** | **2. Realtime-native** | **3. Résumé-max** (recommended target by end of Phase 2) |
|---|---|---|---|
| Conversation | Cascaded: Flux Multilingual → Haiku 5.5 → ElevenLabs Flash / Cartesia, on LiveKit Agents | `gpt-realtime-2.1` (or Gemini 3.8 Live) via LiveKit, with a parallel STT tee for grading | Option 1 plus a speech-to-speech experiment arm |
| Turn-taking | Flux end-of-turn plus patience policy | Semantic VAD, `eagerness: low` | Flux + LiveKit audio turn detector; tuned per level; false cut-off metric |
| Grading | Opus 5.5 G-Eval-style, n = 3, transcript + timing features | Same, on the teed STT | Two-family double évaluation + Azure PA fr-FR + calibrated phonology model + eval harness |
| Avatar | None (static examiner photo + speaking indicator) | None | Pre-rendered clips + Simli / TalkingHead; Anam premium experiment |
| Cost per 12-min session | ≈ $0.40–0.95 | ≈ $0.85–5.8 (cache-dependent) | ≈ $0.55–1.2 (Simli) |
| Complexity | Low–medium | Medium (vendor quirks, session limits) | High |
| Résumé value | Medium | Medium | **High** |

### G.2 Recommended path [recommendation]

**Phase 1:** build **Option 1**, structured so that Option 3's pieces slot in:

- Data-driven exam engine.
- Langfuse from day one.
- Separate recorded learner track.
- Judge interface designed for multiple judges.

**Milestones:**

| # | Milestone | Exit criteria |
|---|---|---|
| M0 (1 wk) | Domain encoding | `ExamDefinition` for A1 and A2 with grids; 20 original A1 role-plays and 20 A2 monologue/interaction items reviewed by an FLE teacher |
| M1 (2–3 wk) | Voice loop | A1 mock end to end in the browser: prep timer, card draw, three parts, transitions, relance policy; p50 system latency ≤ 1.0 s; false cut-off rate measured on 20 internal sessions |
| M2 (2 wk) | Grading v1 | Batch transcript + timing features + Opus judge (n = 3) + feedback report; evidence quotes validated |
| M3 (3–4 wk, overlaps) | Gold set v0 and eval harness | 50 consented sessions double-rated; QWK dashboard; ASR bake-off (2–3 engines) |
| M4 | Pronunciation | Azure PA fr-FR integrated; phonology ordinal model; ablation report |
| M5 | Practice vs mock modes, A2 complete, beta with 20–50 learners | Retention and rating feedback; cost per session ≤ $1 |
| Phase 2 | Avatar | Clips + Simli/TalkingHead A/B; added latency ≤ 300 ms p50; realism rating uplift |
| Phase 3 | B1 → B2 → C1 → C2 | Monologue mode, document generation pipeline, argument extraction, two-examiner C2 debate; per-level agreement reports |
| Expansion | TCF Canada / TEF Canada | New `ExamDefinition`s; NCLC mapping (official tables needed) |

### G.3 Latency budget (target)

See B.9. Headline: **system latency p50 ≤ 1.0 s and p95 ≤ 1.6 s, excluding the deliberate patience wait**, which is tuned per level, starting at 0.8–1.5 s for A1/A2. Plus ≤ 300 ms p50 for the avatar in Phase 2.

### G.4 Cost table (per 12-min connected session; see B.8 for the arithmetic)

| Component | Lean | Realtime-native | Résumé-max |
|---|---|---|---|
| STT (streaming) | $0.09 | $0.03 (batch tee only) | $0.09 |
| Conversation LLM / S2S | $0.003–0.06 | $0.65 best case to $5.2 worst | $0.003–0.06 |
| TTS | $0.12–0.16 | Included | $0.12–0.16 |
| Judge(s) | $0.15–0.63 | $0.15–0.63 | $0.30–0.80 (two families) |
| Pronunciation | — | — | Azure STT-priced **[unverified]** |
| Avatar | — | — | $0.11 (Simli) to $1.9 (Anam) |
| **Total** | **≈ $0.40–0.95** | **≈ $0.85–5.8** | **≈ $0.65–3.0** |

### G.5 Risks

1. **Learners may treat estimates as official scores.** Mitigate with clear disclaimers, published agreement data and uncertainty bands.
2. **ASR on accented learner French** may hide or invent errors. Mitigate with the bake-off, dual ASR and confidence-aware judging.
3. **Turn-taking:** cutting learners off feels hostile, and waiting too long feels laggy. Mitigate with per-level tuning and the false cut-off metric.
4. **IP:** accidental reuse of FEI subjects or press texts. Mitigate with an n-gram overlap check and a review gate.
5. **Vendor churn:** HeyGen's Streaming API was deprecated and Ready Player Me shut down ([secondary]). Mitigate by keeping vendor-agnostic interfaces; LiveKit and Pipecat plugins make swaps cheap.
6. **Regulation:** GDPR voice data and the EU AI Act high-risk scope if sold to institutions. Get legal review before B2B.
7. **Cost spikes on speech-to-speech** if prompt caching misses. Use the cascaded default and track cost per session in telemetry.
8. **Judge bias:** length, accent, self-preference. Run the bias suite in CI.

### G.6 Open questions

1. Can you recruit 2+ DELF-habilitated examiner-correctors to rate the gold set, and on what terms?
2. Will FEI agree to explicit use of the grids or descriptors in a commercial product, or to the "DELF" name in marketing?
3. Target market first: EU hobbyists and students, or immigration-driven candidates (France residency, Canada)? This changes the TCF priority.
4. Should mock mode allow pausing? The real exam doesn't.
5. Should the judge be allowed to hear audio (audio-LLM), given the privacy and cost implications?
6. How much examiner variability is desired? Real examiners differ, so randomised examiner "styles" within FEI guidance might add realism.
7. Which TTS voice best fits "neutral French examiner", and should a fr-CA voice be offered for the TCF Canada audience?

---

## Verification notes

Claims I could not verify from a primary source, or which rest on secondary sources:

1. **TEF Canada speaking format** (15 min; Section A ~5 min, Section B ~10 min): from a search summary of lefrancaisdesaffaires.fr pages; the official page was not opened.
2. **French naturalisation requires B2 from 2026-01-01:** secondary sites only. service-public F2213 says only "connaissance suffisante" and gives no level.
3. **DELF junior/scolaire B1 speaking format** (3 parts, 15 min + 10 min prep): search snippet of the FEI page.
4. **DELF Pro speaking format:** FEI page returned 403.
5. **C2 debate with one examiner playing the opposing side:** search snippet of an FEI C2 examiner PDF.
6. **B2 descriptor content** (problématique, plan, connectors, concession): search summary; the B2 descriptor PDF was not opened.
7. **"DELF/DALF" trademark status and FEI licensing terms** for commercial use of the grids: not checked.
8. **TCF Canada and TEF scoring on the NCLC/CLB scale:** not checked on IRCC or FEI.
9. **French STT accuracy (WER) for Nova-3, OpenAI transcribe, Speechmatics and AssemblyAI on learner speech:** no independent data found. Speechmatics' French support is not listed on its pricing page.
10. **Cartesia Sonic-3.6 French support and Deepgram Aura-2 French voices:** not confirmed on official pages.
11. **TTS latency:** vendor claims (ElevenLabs ~100 ms, Cartesia ~90 ms) are verified as claims only. Independent numbers (119–288 ms; ~166 ms) are from secondary benchmark blogs.
12. **LLM time to first token for Claude, OpenAI and Gemini:** no published millisecond figures; must be measured.
13. **Azure Speech prices** (STT, pronunciation assessment, neural TTS, avatar): the pricing page rendered without numbers.
14. **Speechace pricing** (a $40/month tier mentioned by a third party): unverified.
15. **D-ID API pricing:** page unreadable.
16. **LiveAvatar dollar pricing** (~$0.13/min LITE on Starter; credit pack prices): from HeyGen help and community pages via search, not the pricing page. Interactive Avatar sunset status is conflicting.
17. **Simli, bitHuman and LiveAvatar French lip-sync quality and language support:** not stated on the pages I read.
18. **Ready Player Me shutdown (January 2026):** secondary sources (TechCrunch on the acquisition; competitor blogs on the shutdown date).
19. **GPT-Live API launch date (2026-09-10), benchmark claims, and the gpt-realtime-2.1 release date (2026-07-06):** secondary or news coverage. The model page and pricing were verified.
20. **Gemini Live billing for context re-reads** and the audio-input price line for Gemini text models: not specified on the pricing page I read.
21. **Claude Messages API lacks token logprobs:** stated from my knowledge and Anthropic API reference material; not confirmed against a docs page that explicitly says so. The `temperature` rejection on API version 2026-10-21 comes from Anthropic's API skill reference (cached 2026-11-03).
22. **Pipecat licence (BSD-2):** from official docs via a search summary; the LICENSE file was not opened.
23. **ASR silently "fixing" grammar and dropping hesitations** (arXiv 2506.04076): search summary. The LearnerVoice abstract (2407.04280) was verified for disfluency and error rates.
24. **EU AI Act Digital Omnibus delay to 2027-12-02** and Regulation number 2026/1744: law-firm commentary; the Official Journal was not checked.
25. **Corpora** (LANGSNAP, FLLOC, IPFC, the IRIT Japanese-learners corpus): licences and CEFR labelling unverified.
26. **Speak & Improve corpus licence and CEFR labelling:** not stated on the arXiv abstract.
27. **Deepgram EU endpoints for Flux:** press coverage.
28. **Rive and Live2D** as 2D avatar options: not researched in depth.
29. **Copyright status of the CEFR "Inventaire linguistique"** (FEI): not checked.
30. **Age of digital consent for minors in France (15):** not verified in this research.

---

## Sources

**France Éducation international (primary)**

- DELF tout public levels: [A1](https://www.france-education-international.fr/diplome/delf-tout-public/niveau-a1) · [A2](https://www.france-education-international.fr/diplome/delf-tout-public/niveau-a2) · [B1](https://www.france-education-international.fr/diplome/delf-tout-public/niveau-b1) · [B2](https://www.france-education-international.fr/diplome/delf-tout-public/niveau-b2)
- DALF: [C1](https://www.france-education-international.fr/article/dalf-c1) · [C2](https://www.france-education-international.fr/article/dalf-c2)
- Sample papers: [A1](https://www.france-education-international.fr/diplome/delf-tout-public/niveau-a1/exemples-sujets) · [A2](https://www.france-education-international.fr/diplome/delf-tout-public/niveau-a2/exemples-sujets) · [B1](https://www.france-education-international.fr/diplome/delf-tout-public/niveau-b1/exemples-sujets) · [B2](https://www.france-education-international.fr/diplome/delf-tout-public/niveau-b2/exemples-sujets) · [C1](https://www.france-education-international.fr/diplome/dalf/exemples-sujets) · [C2](https://www.france-education-international.fr/diplome/dalf/dalf-c2-exemples-de-sujets)
- Speaking grids: [A1](https://www.france-education-international.fr/document/grille-po-a1) · [A2](https://www.france-education-international.fr/document/grille-po-a2) · [B1](https://www.france-education-international.fr/document/grille-po-b1) · [B2](https://www.france-education-international.fr/document/grille-po-b2) · [C1](https://www.france-education-international.fr/document/grille-po-c1) · [C2](https://www.france-education-international.fr/document/grille-copo-c2)
- Speaking descriptors: [A1](https://www.france-education-international.fr/document/descript-perf-po-a1) · [A2](https://www.france-education-international.fr/document/descript-perf-po-a2)
- Examiner and candidate docs: [A1 examiner](https://www.france-education-international.fr/document/delf-dalf-a1-tp-examinateur-sujet-demo0) · [A1 candidate](https://www.france-education-international.fr/document/delf-dalf-a1-tp-candidat-ind-sujet-demo) · [A2 examiner](https://www.france-education-international.fr/document/delf-a2-tp-examinateur-ind) · [B1 examiner](https://www.france-education-international.fr/document/delf-b1-tp-examinateur-ind) · [B2 examiner](https://www.france-education-international.fr/document/delf-b2-tp-examinateur-ind) · [C1 examiner](https://www.france-education-international.fr/document/dalf-c1sujet-demo-examinateur)
- [Évolution des épreuves (kit, updated 2024-06-24)](https://www.france-education-international.fr/document/kit-evolutions-dd)
- [Mentions légales](https://www.france-education-international.fr/mentions-legales)
- [2025 certification figures](https://www.france-education-international.fr/actualites/lettre-fei/2026-02/les-certifications-de-langue-francaise-de-france-education-international-en-forte-hausse)
- [DELF junior/scolaire](https://www.france-education-international.fr/diplome/delf-junior-scolaire)
- [TCF Canada](https://www.france-education-international.fr/test/tcf-canada) · [TCF IRN](https://www.france-education-international.fr/test/tcf-irn)
- [Productions orales illustrant les 6 niveaux du CECRL](https://www.france-education-international.fr/productions-orales-illustrant-les-6-niveaux-du-cecrl)

**Government and regulation**

- [service-public.fr F34501](https://www.service-public.gouv.fr/particuliers/vosdroits/F34501?lang=fr) · [F2213](https://www.service-public.gouv.fr/particuliers/vosdroits/F2213)
- [EDPB Guidelines 02/2021 on virtual voice assistants](https://www.edpb.europa.eu/system/files/2021-07/edpb_guidelines_202102_on_vva_v2.0_adopted_en.pdf)
- [AI Act Annex III](https://artificialintelligenceact.eu/annex/3/) · [Gibson Dunn on the Omnibus](https://www.gibsondunn.com/eu-ai-act-omnibus-agreement-postponed-high-risk-deadlines-and-other-key-changes/) · [Lewis Silkin](https://www.lewissilkin.com/insights/2026/07/27/the-digital-omnibus-on-ai-enters-into-force-today-102nedo)
- [CEFR Companion Volume 2020](https://rm.coe.int/cefr-companion-volume-with-new-descriptors-2020/16809ea0d4)

**Models and APIs**

- Anthropic: [models overview](https://platform.claude.com/docs/en/about-claude/models/overview.md) · [pricing](https://platform.claude.com/docs/en/about-claude/pricing.md)
- OpenAI: [pricing](https://developers.openai.com/api/docs/pricing) · [gpt-realtime-2.1](https://developers.openai.com/api/docs/models/gpt-realtime-2.1) · [voice latency & cost](https://developers.openai.com/api/docs/guides/voice-latency-cost) · [realtime VAD](https://developers.openai.com/api/docs/guides/realtime-vad) · [realtime conversations](https://developers.openai.com/api/docs/guides/realtime-conversations) · [GPT-Live announcement](https://openai.com/index/introducing-gpt-live-1-in-the-api/)
- Google: [Gemini pricing](https://aistudio.google.com/docs/pricing) · [Live API session management](https://aistudio.google.com/docs/live-api/session-management) · [Live API capabilities](https://aistudio.google.com/docs/live-api/capabilities)
- Deepgram: [pricing](https://deepgram.com/pricing) · [Flux quickstart](https://developers.deepgram.com/docs/flux/quickstart) · [filler words](https://developers.deepgram.com/docs/filler-words)
- Other STT/TTS vendors: [AssemblyAI pricing](https://www.assemblyai.com/pricing) · [Speechmatics pricing](https://www.speechmatics.com/pricing) · [ElevenLabs API pricing](https://elevenlabs.io/pricing/api) · [ElevenLabs models](https://elevenlabs.io/docs/overview/models) · [Cartesia pricing](https://cartesia.ai/pricing)
- Microsoft Azure: [language support](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=pronunciation-assessment) · [pronunciation assessment how-to](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/how-to-pronunciation-assessment) · [pricing](https://azure.microsoft.com/en-us/pricing/details/speech/)
- Speechace: [supported languages](https://api-docs.speechace.com/getting-started/supported-languages) · [French/Spanish solution](https://api-docs.speechace.com/solutions/speaking-practice-in-spanish-and-french)

**Frameworks and tools**

- LiveKit: [Agents (GitHub)](https://github.com/livekit/agents) · [turn detector](https://docs.livekit.io/agents/build/turns/turn-detector/) · [turns](https://docs.livekit.io/agents/build/turns/) · [avatars](https://docs.livekit.io/agents/models/avatar/)
- Pipecat: [supported services](https://docs.pipecat.ai/server/services/supported-services) · [Smart Turn](https://github.com/pipecat-ai/smart-turn) · [pypi](https://pypi.org/project/pipecat-ai/)
- Other tools: [Silero VAD](https://github.com/snakers4/silero-vad) · [Langfuse](https://github.com/langfuse/langfuse) · [DeepEval G-Eval](https://deepeval.com/docs/metrics-llm-evals) · [scikit-learn cohen_kappa_score](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.cohen_kappa_score.html) · [MFA French models](https://mfa-models.readthedocs.io/en/latest/acoustic/French/index.html) · [wav2vec2 XLSR-53 espeak](https://huggingface.co/facebook/wav2vec2-xlsr-53-espeak-cv-ft) · [TalkingHead](https://github.com/met4citizen/TalkingHead)

**Avatars**

- [Simli pricing](https://www.simli.com/pricing) · [Anam pricing](https://anam.ai/pricing) · [Tavus pricing](https://www.tavus.io/pricing) · [bitHuman pricing](https://www.bithuman.ai/pricing)
- [LiveAvatar LITE mode](https://docs.liveavatar.com/docs/lite-mode/overview) · [HeyGen Streaming API deprecated](https://docs.heygen.com/docs/streaming-api-deprecated)
- [TechCrunch on Ready Player Me](https://techcrunch.com/2025/12/19/netflix-acquires-gaming-avatar-maker-ready-player-me/)

**Papers**

- [G-Eval (arXiv 2303.16634)](https://arxiv.org/html/2303.16634v3)
- [LearnerVoice (arXiv 2407.04280)](https://arxiv.org/abs/2407.04280)
- [Verbatim L2 ASR (arXiv 2506.04076)](https://arxiv.org/html/2506.04076v1)
- [Unified MLLM ASA (arXiv 2508.12591)](https://arxiv.org/abs/2508.12591)
- [Speak & Improve 2025 (arXiv 2412.11985)](https://arxiv.org/abs/2412.11985)

**Corpora**

- [LANGSNAP on TalkBank](https://slabank.talkbank.org/access/French/LANGSNAP6.html) · [FLLOC](https://web-archive.southampton.ac.uk/www.flloc.soton.ac.uk/list.html) · [IPFC](https://cblle.tufs.ac.jp/ipfc/index9.html)

**Secondary / market**

- [digischool](https://www.digischool.fr/articles/fle/niveau-de-francais-naturalisation-2026/) · [integrationfrance](https://www.integrationfrance.fr/articles/niveau-francais-a2-b1-b2-titre-sejour) · [gradium TTS latency](https://gradium.ai/content/best-low-latency-tts-apis-2026) · [futureagi](https://futureagi.com/blog/elevenlabs-vs-cartesia-tts-2026/) · [SiliconANGLE on Flux](https://siliconangle.com/2026/04/29/deepgram-expands-flux-10-languages-mid-call-switching-voice-agents/)
- Competitors: [OralPrep](https://apps.apple.com/ae/app/id6772313115) · [TCF Exam Hero](https://mwm.ai/apps/tcf-exam-hero/6757088210) · [TCF Canada Speaking Coach](https://mwm.ai/apps/tcf-canada-speaking-test-coach/6753697803) · [Talkparty](https://www.talkparty.app/improve-french) · [Praktika](https://praktika.ai/blog/delf-b2-preparation-honest-faq) · [Penvo](https://penvo.pages.dev/) · [PrepMyFrench](https://www.producthunt.com/products/prepmyfrench) · [Univext](https://univext.com/en/blog/274/how-to-pass-delf-dalf-exam-with-ai-2026)
