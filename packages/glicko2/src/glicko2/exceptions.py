class Glicko2Error(Exception):
    """Base exception for all glicko2 errors."""


class ConvergenceError(Glicko2Error):
    """Raised when the iterative σ update fails to converge."""


class UnknownPlayerError(Glicko2Error):
    """Raised when a player ID is not found in the pool or storage."""


class InvalidMatchError(Glicko2Error):
    """Raised when a match references the same player twice or has an invalid score."""


class StorageError(Glicko2Error):
    """Raised on persistence failures."""
