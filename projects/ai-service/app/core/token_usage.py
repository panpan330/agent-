from dataclasses import dataclass
from math import ceil


@dataclass(frozen=True)
class TokenBudget:
    estimated_input_tokens: int
    max_output_tokens: int

    @property
    def total_reserved_tokens(self) -> int:
        return self.estimated_input_tokens + self.max_output_tokens


def estimate_text_tokens_roughly(text: str) -> int:
    stripped_text = text.strip()
    if not stripped_text:
        return 0

    ascii_count = sum(1 for character in stripped_text if character.isascii())
    non_ascii_count = len(stripped_text) - ascii_count

    return max(1, ceil(ascii_count / 4) + non_ascii_count)


def build_token_budget(text: str, max_output_tokens: int) -> TokenBudget:
    if max_output_tokens <= 0:
        raise ValueError("max_output_tokens must be greater than 0")

    return TokenBudget(
        estimated_input_tokens=estimate_text_tokens_roughly(text),
        max_output_tokens=max_output_tokens,
    )
