"""glicko2 — pure Glicko-2 rating system library.

Quick start::

    from glicko2 import RatingEngine, MatchResult, RatingPeriod

    engine = RatingEngine(tau=0.5)
    engine.pool.get_or_create("alice")
    engine.pool.get_or_create("bob")

    period = RatingPeriod(id="round-1")
    period.add_match(MatchResult("alice", "bob", 1.0))  # one entry per game
    engine.process_period(period)  # engine derives bob's perspective automatically
"""

from glicko2.engine.rating_engine import RatingEngine
from glicko2.models.match_result import MatchResult
from glicko2.models.player import Player
from glicko2.models.rating_period import RatingPeriod

__version__ = "0.1.0"
__all__ = ["RatingEngine", "Player", "MatchResult", "RatingPeriod"]
