class RateLimitError(Exception):
    """Exception raised when an LLM provider rate limit is hit."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)
