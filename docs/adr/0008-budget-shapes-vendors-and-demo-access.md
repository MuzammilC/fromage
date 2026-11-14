# A budget of about 50 CAD/month shapes vendor choices and demo access

All API and vendor spending during Phase 1 is capped at about 50 CAD a month. This constraint explains choices that would otherwise look odd:

- **Vendors:** free tiers first. LiveKit Cloud Build hosts the agent, a $200 Deepgram credit covers speech-to-text, Azure F0 covers French voices and pronunciation scoring, and Supabase, Langfuse and Vercel Hobby are on their free plans.
- **TTS:** Azure neural voices instead of ElevenLabs or Cartesia, whose free tiers are too small and non-commercial.
- **Judge model:** Sonnet 5.5 by default. Opus 5.5 is used only in eval comparison runs, through the Batch API.
- **Demo access:** a login with email verification, one voice Session per User per day, and a global voice-spend kill switch, backed by a hard spend limit in the Anthropic console.

Free tiers have hard caps: LiveKit stops at 1,000 agent minutes, and free Supabase projects pause after a week of inactivity. Free-tier usage is therefore tracked, and a keep-alive ping keeps Supabase awake.
