"""Custom exceptions for Instagram scraping."""


class ScraperError(Exception):
    """Base exception for all scraper errors."""
    pass


class AuthenticationExpiredError(ScraperError):
    """Raised when the session cookie has expired or is invalid."""

    def __init__(self, message: str = "Session cookie has expired or is invalid"):
        self.message = message
        super().__init__(self.message)


class RateLimitError(ScraperError):
    """Raised when Instagram rate limits or blocks the request."""

    def __init__(self, message: str = "Rate limited by Instagram", retry_after: int = 60):
        self.message = message
        self.retry_after = retry_after
        super().__init__(self.message)


class ProfileNotFoundError(ScraperError):
    """Raised when the requested profile does not exist."""

    def __init__(self, username: str):
        self.username = username
        self.message = f"Profile '{username}' not found"
        super().__init__(self.message)


class ProfilePrivateError(ScraperError):
    """Raised when the profile is private and not accessible."""

    def __init__(self, username: str):
        self.username = username
        self.message = f"Profile '{username}' is private"
        super().__init__(self.message)


class AgeRestrictionError(ScraperError):
    """Raised when profile requires age verification (21+)."""

    def __init__(self, username: str, min_age: int = 21):
        self.username = username
        self.min_age = min_age
        self.message = f"Profile '{username}' requires {min_age}+ age verification"
        super().__init__(self.message)


class NetworkError(ScraperError):
    """Raised for network-related errors (timeout, connection refused, etc.)."""

    def __init__(self, message: str = "Network error occurred", original_error: Exception = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


class BrowserError(ScraperError):
    """Raised when browser/Playwright encounters an error."""

    def __init__(self, message: str = "Browser error occurred", original_error: Exception = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)
