import tiktoken


class TokenAnalyzer:
    def __init__(self):
        self.encoder = tiktoken.get_encoding("cl100k_base")

    def estimate(self, text: str) -> int:
        return len(self.encoder.encode(text))
