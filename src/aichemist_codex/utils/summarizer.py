import re


def summarize_for_gpt(text, max_sentences=5, max_length=1000):
    """Condenses text to extract key details for GPT-based summaries."""
    if not text:
        return "No summary available."

    sentences = re.split(r"(?<=\.)\s", text)  # Split at sentence boundaries
    summary = ". ".join(sentences[:max_sentences])

    return summary[:max_length].strip() + "..."
