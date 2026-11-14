# The exam engine is pure, and the Medium is an adapter

The engine handles the Session state machine (Prep Time, Draws, Parts, transitions, Relance policy, Turn Modes). It is a pure Python package with no I/O, so it can be unit-tested without LiveKit or an LLM.

The first slices run it inside the LiveKit agent with text-only I/O. The voice slice then changes only the I/O adapter, not the engine, and text and voice share one runtime and one deployment.

A separate FastAPI server for text Sessions was rejected, because it would mean two runtime paths that would drift apart.
