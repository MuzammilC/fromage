"""Claude Haiku adapter for the echo Examiner, traced in Langfuse."""

from anthropic import AsyncAnthropic
from langfuse import Langfuse

from fromage_agent.echo import MODEL, Paraphrase, Usage, cost_usd

SYSTEM_PROMPT = (
    "Tu es un examinateur de français. Le candidat écrit une phrase. "
    "Reformule-la en français très simple (niveau A2), en une seule phrase courte. "
    "Réponds uniquement avec la reformulation, sans commentaire."
)
MAX_TOKENS = 512


class HaikuParaphraser:
    def __init__(self, client: AsyncAnthropic, langfuse: Langfuse) -> None:
        self._client = client
        self._langfuse = langfuse

    async def paraphrase(self, session_id: str, text: str) -> Paraphrase:
        with self._langfuse.start_as_current_observation(
            name="paraphrase",
            as_type="generation",
            model=MODEL,
            input=text,
            metadata={"session_id": session_id},
        ) as generation:
            response = await self._client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=SYSTEM_PROMPT,
                output_config={"effort": "low"},
                messages=[{"role": "user", "content": text}],
            )
            reply = "".join(b.text for b in response.content if b.type == "text").strip()
            usage = Usage(response.usage.input_tokens, response.usage.output_tokens)
            generation.update(
                output=reply,
                usage_details={"input": usage.input_tokens, "output": usage.output_tokens},
                cost_details={"total": cost_usd(usage)},
            )
        if not reply:
            raise RuntimeError(f"Empty reply (stop_reason={response.stop_reason})")
        return Paraphrase(text=reply, usage=usage)
