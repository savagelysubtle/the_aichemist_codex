"""Summarization utilities for AI-based processing."""


def summarize_for_gpt(text, max_sentences=10, max_length=1000):
    """Condenses text to extract key details."""
    if len(text) <= max_length:
        return text

    sentences = text.split(". ")
    summary = ". ".join(sentences[:max_sentences]) + "."
    return summary[:max_length].strip()
