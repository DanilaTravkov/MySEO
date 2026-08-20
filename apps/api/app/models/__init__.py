"""Persistent domain models.

Importing this package registers every model with SQLAlchemy metadata for Alembic.
"""

from app.models.auth import User, UserSession
from app.models.discovery import DiscoveryRun, Seed, Workspace
from app.models.keyword import Keyword, KeywordAnalysis, KeywordObservation, MonthlySearchVolume
from app.models.opportunity import Cluster, ClusterKeyword, Opportunity, ProductHypothesis

__all__ = [
    "Cluster",
    "ClusterKeyword",
    "DiscoveryRun",
    "Keyword",
    "KeywordAnalysis",
    "KeywordObservation",
    "MonthlySearchVolume",
    "Opportunity",
    "ProductHypothesis",
    "Seed",
    "User",
    "UserSession",
    "Workspace",
]
