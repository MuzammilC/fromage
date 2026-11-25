import anthropic
from langfuse import get_client

from .generator import LLMResult

DEFAULT_MODEL = "claude-sonnet-5-5"
MAX_TOKENS = 4000


class AnthropicLLM:
    """Calls Claude and records each call as a Langfuse generation (a no-op without Langfuse keys)."""

    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model
        self._client = anthropic.Anthropic()
        self._langfuse = get_client()

    def complete(self, system: str, user: str, metadata: dict[str, str] | None = None) -> LLMResult:
        with self._langfuse.start_as_current_observation(
            as_type="generation",
            name="gen-items",
            model=self.model,
            input={"system": system, "user": user},
            metadata=metadata,
        ) as generation:
            message = self._client.messages.create(
                model=self.model,
                max_tokens=MAX_TOKENS,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            text = "".join(block.text for block in message.content if block.type == "text")
            usage = {
                "input": message.usage.input_tokens,
                "output": message.usage.output_tokens,
            }
            generation.update(output=text, usage_details=usage)
        return LLMResult(
            text, usage["input"], usage["output"], truncated=message.stop_reason == "max_tokens"
        )

    def flush(self) -> None:
        self._langfuse.flush()
