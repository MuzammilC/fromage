# Cascaded STT → LLM → TTS voice pipeline on LiveKit Agents

The Examiner runs as a cascaded pipeline: speech-to-text, then a text LLM, then text-to-speech, on LiveKit Agents in Python. Phase 1 uses Deepgram Flux, Claude Haiku 5.5 and Azure fr-FR neural voices. Speech-to-speech models such as `gpt-realtime-2.1` and Gemini Live sound more natural, but they were rejected for three reasons:

- Grading needs a faithful word-level Transcript, and their transcripts come from a separate, rough ASR.
- The Examiner has to follow a strict procedure and hold Examiner-only Data, which a text LLM does more predictably.
- Their per-session cost depends on prompt-cache hits, from about $0.65 up to about $5.

Speech-to-speech can come back later as an experiment arm. See `docs/research/delf-speaking-coach.md` §B.
