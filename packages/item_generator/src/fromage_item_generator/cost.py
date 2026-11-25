# USD per million tokens (input, output). Update when pricing changes; check the Anthropic pricing page.
PRICES_PER_MTOK: dict[str, tuple[float, float]] = {
    "claude-sonnet-5-5": (3.0, 15.0),
}
DEFAULT_PRICE = PRICES_PER_MTOK["claude-sonnet-5-5"]


def cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    price_in, price_out = PRICES_PER_MTOK.get(model, DEFAULT_PRICE)
    return (input_tokens * price_in + output_tokens * price_out) / 1_000_000
