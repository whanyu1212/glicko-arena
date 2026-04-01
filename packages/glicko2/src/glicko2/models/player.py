from dataclasses import dataclass, field


@dataclass
class Player:
    """A rated player in Glicko-2 scale (μ, φ, σ).

    All values are in Glicko-2 internal scale.
    Use glicko2.math.conversions to convert to/from display rating (r, RD).

    Attributes:
        id (str): Unique identifier for the player.
        mu (float): Rating on the Glicko-2 scale. Corresponds to display
            rating r via: r = 173.7178 * μ + 1500.
        phi (float): Rating deviation on the Glicko-2 scale. Corresponds to
            display RD via: RD = 173.7178 * φ.
        sigma (float): Volatility — measures consistency of performance.
        num_periods (int): Number of rating periods the player has participated in.
        metadata (dict[str, object]): Arbitrary key-value store for caller use.
    """

    id: str
    mu: float = 0.0          # maps to display rating 1500
    phi: float = 2.014761    # maps to RD 350 (initial default)
    sigma: float = 0.06
    num_periods: int = 0
    metadata: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.phi <= 0:
            raise ValueError(f"phi must be positive, got {self.phi}")
        if self.sigma <= 0:
            raise ValueError(f"sigma must be positive, got {self.sigma}")
