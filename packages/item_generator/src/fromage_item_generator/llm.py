import anthropic
from langfuse import get_client

from .generator import LLMResult

DEFAULT_MODEL = "claude-sonnet-5-5"


class AnthropicLLM:
    """Calls Claude and records each call as a Langfuse generation (a no-op without Langfuse keys)."""

    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model
        self._client = anthropic.Anthropic()
        self._langfuse = get_client()

    def complete(self, system: str, user: str) -> LLMResult:
        with self._langfuse.start_as_current_observation(
            as_type="generation",
            name="gen-items",
            model=self.model,
            input={"system": system, "user": user},
        ) as generation:
            message = self._client.messages.create(
                model=self.model,
                max_tokens=2000,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            text = "".join(block.text for block in message.content if block.type == "text")
            usage = {
                "input": message.usage.input_tokens,
                "output": message.usage.output_tokens,
            }
            generation.update(output=text, usage_details=usage)
        return LLMResult(text, usage["input"], usage["output"])

    def flush(self) -> None:
        self._langfuse.flush()
