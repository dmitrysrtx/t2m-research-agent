"""
Academic Paper Discovery & Hybrid Ranking Engine
=================================================
A production-ready Python framework mitigating citation-lag bias and cross-domain noise:
1. Strict Domain Locking (Computer Science & Engineering).
2. Dual-Bucket Retrieval (Foundational vs. Frontier/SOTA).
3. Non-linear Composite Scoring (Citation Velocity, Influential Citations, Venue Tiers, Code Artifacts).
"""

from academic_ranking_engine.models import Author, PaperMetadata
from academic_ranking_engine.venue_classifier import classify_venue, normalize_venue_name
from academic_ranking_engine.scorer import calculate_paper_score, ScoringConfig
from academic_ranking_engine.client import AcademicSearchClient
from academic_ranking_engine.discovery_engine import DiscoveryEngine

__all__ = [
    "Author",
    "PaperMetadata",
    "classify_venue",
    "normalize_venue_name",
    "calculate_paper_score",
    "ScoringConfig",
    "AcademicSearchClient",
    "DiscoveryEngine",
]
