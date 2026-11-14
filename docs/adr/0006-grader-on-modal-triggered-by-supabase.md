# The Grader runs on Modal, triggered by a Supabase webhook

Grading is a 1–4 minute Python job that only makes HTTP calls: batch ASR, pronunciation assessment and the Judge.

A `grading_jobs` table in Supabase is the source of truth. Finishing a Session inserts a job, and a database webhook calls a Modal endpoint that `.spawn()`s the job and returns at once. A Modal cron job retries jobs stuck in `pending`.

Modal was chosen because:
- It costs about $1/month at Phase 1 volume, covered by the $30 monthly credit.
- It runs Python natively, with timeouts up to 24 h.
- It scales out automatically.
- GPUs for later phoneme models need a one-line change.

The alternatives were rejected:
- **Fly.io:** about $2–4/month for a machine that is idle almost all the time, plus a polling loop to write.
- **Cloud Run:** a billing account and more setup work. It remains the fallback.
- **Vercel Python functions:** a hard 300 s limit.
- **Grading inside the LiveKit agent:** short shutdown hooks, and it would compete with live Sessions.

The grading logic is a plain package, and the Modal code is a thin wrapper, so moving to Cloud Run means adding a Dockerfile and a FastAPI wrapper.
