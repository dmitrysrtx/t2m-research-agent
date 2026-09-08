import math
from typing import Dict, Any, Optional
from dataclasses import dataclass
from academic_ranking_engine.models import PaperMetadata
from academic_ranking_engine.venue_classifier import classify_venue


@dataclass
class ScoringConfig:
    """Configurable weights and bonuses for hybrid paper scoring."""
    influential_cit_multiplier: float = 2.5
    bonus_code: float = 15.0
    bonus_open_access: float = 3.0
    sota_velocity_weight: float = 2.0
    foundation_sqrt_weight: float = 3.0
    foundation_velocity_weight: float = 0.8
    author_h_index_threshold: int = 25
    author_prestige_bonus: float = 6.0


def calculate_paper_score(
    paper: PaperMetadata,
    force_bucket: Optional[str] = None,
    config: Optional[ScoringConfig] = None
) -> float:
    """
    Computes hybrid composite score based on age, velocity, venue, and code artifacts.
    Assigns venue tier, weight, bucket, and stores breakdown details inside paper.
    """
    cfg = config or ScoringConfig()

    # 1. Classify venue tier & multiplier
    tier, w_venue, canonical_venue = classify_venue(paper.venue)
    paper.venue_tier = tier
    paper.venue_weight = w_venue

    # 2. Compute temporal delta_t & citation velocity
    dt = paper.delta_t
    raw_v_cit = (paper.citation_count + cfg.influential_cit_multiplier * paper.influential_citation_count) / dt
    v_cit = round(raw_v_cit, 2)

    # 3. Artifact bonuses
    b_code = cfg.bonus_code if paper.has_code else 0.0
    b_oa = cfg.bonus_open_access if paper.is_open_access else 0.0

    # 4. Author prestige boost for preprints/recent works
    b_author = 0.0
    if any((a.h_index or 0) >= cfg.author_h_index_threshold for a in paper.authors):
        b_author = cfg.author_prestige_bonus

    # 5. Determine bucket: SOTA (<= 2.0 years) vs Foundation (> 2.0 years)
    bucket = force_bucket or ("sota" if dt <= 2.0 else "foundation")
    paper.ranking_bucket = bucket

    if bucket == "sota":
        # Score_SOTA = (V_cit * 2.0 + B_code + B_oa + ln(1 + cit) + B_author) * W_venue
        log_cit = math.log1p(paper.citation_count)
        base_score = (v_cit * cfg.sota_velocity_weight) + b_code + b_oa + log_cit + b_author
        final_score = base_score * w_venue
    else:
        # Score_Foundation = (sqrt(cit) * 3.0 + V_cit * 0.8 + B_code + B_author) * W_venue
        sqrt_cit = math.sqrt(paper.citation_count)
        base_score = (sqrt_cit * cfg.foundation_sqrt_weight) + (v_cit * cfg.foundation_velocity_weight) + b_code + b_author
        final_score = base_score * w_venue

    final_score = round(final_score, 2)
    paper.score = final_score

    paper.score_breakdown = {
        "bucket": bucket,
        "delta_t": dt,
        "v_cit": v_cit,
        "w_venue": w_venue,
        "venue_tier": tier,
        "canonical_venue": canonical_venue,
        "b_code": b_code,
        "b_oa": b_oa,
        "b_author": b_author,
        "final_score": final_score
    }

    return final_score


if __name__ == "__main__":
    from datetime import date
    from academic_ranking_engine.models import Author

    recent_sota = PaperMetadata(
        paper_id="sota-1",
        title="PhysDiff: Physics-Guided Human Motion Diffusion Model",
        year=2024,
        publication_date=date(2024, 6, 1),
        venue="CVPR 2024",
        citation_count=35,
        influential_citation_count=8,
        is_open_access=True,
        code_url="https://github.com/syguan96/PhysDiff",
        authors=[Author(name="S. Guan", h_index=15)]
    )

    foundational = PaperMetadata(
        paper_id="found-1",
        title="SMPL: A Skinned Multi-Person Linear Model",
        year=2015,
        publication_date=date(2015, 10, 1),
        venue="ACM Transactions on Graphics (SIGGRAPH Asia)",
        citation_count=3400,
        influential_citation_count=420,
        is_open_access=True,
        code_url="https://github.com/vchoutas/smplx",
        authors=[Author(name="M. Loper", h_index=45)]
    )

    s_sota = calculate_paper_score(recent_sota)
    s_found = calculate_paper_score(foundational)

    print("==================================================")
    print("⚖️ Hybrid Scorer Diagnostic")
    print("==================================================")
    print(f"[*] SOTA Paper: '{recent_sota.title}'")
    print(f"    - Score: {s_sota} | Bucket: {recent_sota.ranking_bucket} | V_cit: {recent_sota.citation_velocity}")
    print(f"    - Breakdown: {recent_sota.score_breakdown}")
    print(f"[*] Foundational Paper: '{foundational.title}'")
    print(f"    - Score: {s_found} | Bucket: {foundational.ranking_bucket} | V_cit: {foundational.citation_velocity}")
    print(f"    - Breakdown: {foundational.score_breakdown}")
    print("==================================================")
