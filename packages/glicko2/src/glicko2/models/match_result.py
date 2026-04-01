from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class MatchResult:
    """The outcome of a single match between two players.

    Score is any float in [0, 1] representing the outcome from `player_id`'s
    perspective. The classic Glicko values (1.0 win / 0.5 draw / 0.0 loss)
    are valid, but continuous scores are also supported — e.g. a judge that
    scores agent A at 0.82 and agent B at 0.61 on the same task would produce
    a score of 0.82 / (0.82 + 0.61) ≈ 0.57 for A and 0.43 for B.

    Attributes:
        player_id (str): The player whose rating will be updated.
        opponent_id (str): The opponent in this match.
        score (float): Outcome for `player_id` — any float in [0, 1].
        timestamp (datetime): When the match was played.
        metadata (dict[str, object]): Arbitrary key-value store for caller use.
    """

    player_id: str
    opponent_id: str
    score: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.player_id == self.opponent_id:
            from glicko2.exceptions import InvalidMatchError
            raise InvalidMatchError(
                f"player_id and opponent_id must differ, got {self.player_id!r}"
            )
        if not 0.0 <= self.score <= 1.0:
            from glicko2.exceptions import InvalidMatchError
            raise InvalidMatchError(
                f"score must be in [0, 1], got {self.score}"
            )

    def mirror(self) -> "MatchResult":
        """Return the match from the opponent's perspective.

        Returns:
            MatchResult: A new instance with player_id and opponent_id swapped
                and score inverted (1.0 - score).
        """
        return MatchResult(
            player_id=self.opponent_id,
            opponent_id=self.player_id,
            score=1.0 - self.score,
            timestamp=self.timestamp,
            metadata=self.metadata,
        )
