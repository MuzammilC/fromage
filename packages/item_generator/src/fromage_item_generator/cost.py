# USD per million tokens (input, output). Assumed prices: check the Anthropic pricing page.
PRICES_PER_MTOK: dict[str, tuple[float, float]] = {
    "claude-sonnet-5-5": (3.0, 15.0),
}


def cost_usd(model: str, input_tokens: int, output_tokens: int) -> float | None:
    """The cost of one call, or None when the model has no known price."""
    price = PRICES_PER_MTOK.get(model)
    if price is None:
        return None
    return (input_tokens * price[0] + output_tokens * price[1]) / 1_000_000
