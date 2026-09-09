"""
Deterministic Venue & Academic Impact Ranker for AI, CV, Graphics, Robotics & Machine Learning.

Maps academic venues (conferences, journals, preprints) from Semantic Scholar, CrossRef,
and ArXiv metadata to recognized international rankings (CORE Ranking, JCR Impact Factor, H5-Index).
"""

import re
from typing import Dict, Any, Tuple


# ==============================================================================
# Canonical Venue Database (CORE Ranking, JCR Impact Factor, H5-Index, Tier)
# ==============================================================================
VENUE_DATABASE = [
    # --------------------------------------------------------------------------
    # Tier 1 Flagship Conferences (CORE A* / Top Tier AI, CV, Graphics, Robotics)
    # --------------------------------------------------------------------------
    {
        "patterns": [r"\bcvpr\b", r"computer vision and pattern recognition"],
        "name": "CVPR",
        "rank_display": "CORE A* (Tier 1, H5: 389)",
        "tier": 1,
        "tier_weight": 2.0,
        "is_peer_reviewed": True
    },
    {
        "patterns": [r"\bneurips\b", r"\bnips\b", r"neural information processing systems"],
        "name": "NeurIPS",
        "rank_display": "CORE A* (Tier 1, H5: 310)",
        "tier": 1,
        "tier_weight": 2.0,
        "is_peer_reviewed": True
    },
    {
        "patterns": [r"\biclr\b", r"learning representations"],
        "name": "ICLR",
        "rank_display": "CORE A* (Tier 1, H5: 285)",
        "tier": 1,
        "tier_weight": 2.0,
        "is_peer_reviewed": True
    },
    {
        "patterns": [r"\bicml\b", r"international conference on machine learning"],
        "name": "ICML",
        "rank_display": "CORE A* (Tier 1, H5: 245)",
        "tier": 1,
        "tier_weight": 2.0,
        "is_peer_reviewed": True
    },
    {
        "patterns": [r"\biccv\b", r"international conference on computer vision"],
        "name": "ICCV",
        "rank_display": "CORE A* (Tier 1, H5: 239)",
        "tier": 1,
        "tier_weight": 2.0,
        "is_peer_reviewed": True
    },
    {
        "patterns": [r"\beccv\b", r"european conference on computer vision"],
        "name": "ECCV",
        "rank_display": "CORE A* (Tier 1, H5: 186)",
        "tier": 1,
        "tier_weight": 1.9,
        "is_peer_reviewed": True
    },
    {
        "patterns": [r"\bsiggraph\b", r"acm transactions on graphics", r"\btog\b"],
        "name": "SIGGRAPH / ACM TOG",
        "rank_display": "CORE A* (IF: 7.4, Tier 1)",
        "tier": 1,
        "tier_weight": 2.0,
        "is_peer_reviewed": True
    },
    {
        "patterns": [r"\baaai\b", r"association for the advancement of artificial intelligence"],
        "name": "AAAI",
        "rank_display": "CORE A* (Tier 1, H5: 180)",
        "tier": 1,
        "tier_weight": 1.8,
        "is_peer_reviewed": True
    },
    {
        "patterns": [r"\bijcai\b", r"international joint conference on artificial intelligence"],
        "name": "IJCAI",
        "rank_display": "CORE A* (Tier 1, H5: 110)",
        "tier": 1,
        "tier_weight": 1.7,
        "is_peer_reviewed": True
    },
    {
        "patterns": [r"\bacl\b", r"association for computational linguistics"],
        "name": "ACL",
        "rank_display": "CORE A* (Tier 1, H5: 165)",
        "tier": 1,
        "tier_weight": 1.8,
        "is_peer_reviewed": True
    },
    {
        "patterns": [r"\bemnlp\b", r"empirical methods in natural language processing"],
        "name": "EMNLP",
        "rank_display": "CORE A* (Tier 1, H5: 155)",
        "tier": 1,
        "tier_weight": 1.7,
        "is_peer_reviewed": True
    },
    {
        "patterns": [r"\bicra\b", r"robotics and automation \(icra\)"],
        "name": "IEEE ICRA",
        "rank_display": "CORE A (Tier 1, H5: 115)",
        "tier": 1,
        "tier_weight": 1.8,
        "is_peer_reviewed": True
    },
    {
        "patterns": [r"\biros\b", r"intelligent robots and systems"],
        "name": "IEEE/RSJ IROS",
        "rank_display": "CORE A (Tier 1, H5: 95)",
        "tier": 1,
        "tier_weight": 1.7,
        "is_peer_reviewed": True
    },
    {
        "patterns": [r"\bcorl\b", r"conference on robot learning"],
        "name": "CoRL",
        "rank_display": "Top Robotics (Tier 1, H5: 65)",
        "tier": 1,
        "tier_weight": 1.8,
        "is_peer_reviewed": True
    },
    {
        "patterns": [r"\brss\b", r"robotics: science and systems"],
        "name": "RSS",
        "rank_display": "CORE A* (Tier 1, H5: 62)",
        "tier": 1,
        "tier_weight": 1.8,
        "is_peer_reviewed": True
    },

    # --------------------------------------------------------------------------
    # Tier 1 Flagship Journals (JCR Q1 / High Impact Factor)
    # --------------------------------------------------------------------------
    {
        "patterns": [r"pattern analysis and machine intelligence", r"\btpami\b", r"\bpami\b"],
        "name": "IEEE TPAMI",
        "rank_display": "JCR IF: 20.8 (Q1, H5: 175)",
        "tier": 1,
        "tier_weight": 2.0,
        "is_peer_reviewed": True
    },
    {
        "patterns": [r"international journal of computer vision", r"\bijcv\b"],
        "name": "IJCV",
        "rank_display": "JCR IF: 11.6 (Q1, H5: 98)",
        "tier": 1,
        "tier_weight": 1.9,
        "is_peer_reviewed": True
    },
    {
        "patterns": [r"transactions on robotics", r"\bt-ro\b", r"\btro\b"],
        "name": "IEEE T-RO",
        "rank_display": "JCR IF: 9.4 (Q1, H5: 85)",
        "tier": 1,
        "tier_weight": 1.85,
        "is_peer_reviewed": True
    },
    {
        "patterns": [r"nature machine intelligence"],
        "name": "Nature Machine Intelligence",
        "rank_display": "JCR IF: 18.8 (Q1)",
        "tier": 1,
        "tier_weight": 2.0,
        "is_peer_reviewed": True
    },
    {
        "patterns": [r"\bnature\b"],
        "name": "Nature",
        "rank_display": "JCR IF: 50.5 (Q1)",
        "tier": 1,
        "tier_weight": 2.0,
        "is_peer_reviewed": True
    },
    {
        "patterns": [r"\bscience\b"],
        "name": "Science",
        "rank_display": "JCR IF: 44.7 (Q1)",
        "tier": 1,
        "tier_weight": 2.0,
        "is_peer_reviewed": True
    },

    # --------------------------------------------------------------------------
    # Tier 2 Specialized Conferences & Journals (CORE A/B, Robotics/Vision/Graphics)
    # --------------------------------------------------------------------------
    {
        "patterns": [r"robotics and automation letters", r"\bra-l\b", r"\bral\b"],
        "name": "IEEE RA-L",
        "rank_display": "JCR IF: 5.2 (Q1, H5: 92)",
        "tier": 2,
        "tier_weight": 1.45,
        "is_peer_reviewed": True
    },
    {
        "patterns": [r"winter conference on applications of computer vision", r"\bwacv\b"],
        "name": "WACV",
        "rank_display": "CORE A (Tier 2, H5: 75)",
        "tier": 2,
        "tier_weight": 1.4,
        "is_peer_reviewed": True
    },
    {
        "patterns": [r"international conference on 3d vision", r"\b3dv\b"],
        "name": "3DV",
        "rank_display": "CORE B (Tier 2, H5: 55)",
        "tier": 2,
        "tier_weight": 1.35,
        "is_peer_reviewed": True
    },
    {
        "patterns": [r"british machine vision conference", r"\bbmvc\b"],
        "name": "BMVC",
        "rank_display": "CORE B (Tier 2, H5: 48)",
        "tier": 2,
        "tier_weight": 1.3,
        "is_peer_reviewed": True
    },
    {
        "patterns": [r"symposium on computer animation", r"\bsca\b"],
        "name": "ACM SCA",
        "rank_display": "Top Animation (Tier 2)",
        "tier": 2,
        "tier_weight": 1.35,
        "is_peer_reviewed": True
    },
    {
        "patterns": [r"motion,? interaction and games", r"\bmig\b"],
        "name": "ACM MIG",
        "rank_display": "Specialized T2M (Tier 2)",
        "tier": 2,
        "tier_weight": 1.3,
        "is_peer_reviewed": True
    },
    {
        "patterns": [r"computer graphics forum", r"\bcgf\b", r"eurographics"],
        "name": "Eurographics / CGF",
        "rank_display": "CORE A (IF: 2.5, Tier 2)",
        "tier": 2,
        "tier_weight": 1.35,
        "is_peer_reviewed": True
    },
    {
        "patterns": [r"visualization and computer graphics", r"\btvcg\b"],
        "name": "IEEE TVCG",
        "rank_display": "JCR IF: 5.2 (Q1, Tier 2)",
        "tier": 2,
        "tier_weight": 1.4,
        "is_peer_reviewed": True
    },
    {
        "patterns": [r"multibody system dynamics"],
        "name": "Multibody System Dynamics",
        "rank_display": "JCR IF: 3.1 (Q1 Mechanics)",
        "tier": 2,
        "tier_weight": 1.35,
        "is_peer_reviewed": True
    },
    {
        "patterns": [r"autonomous robots", r"\bauro\b"],
        "name": "Autonomous Robots",
        "rank_display": "JCR IF: 3.8 (Q1, Tier 2)",
        "tier": 2,
        "tier_weight": 1.35,
        "is_peer_reviewed": True
    },
    {
        "patterns": [r"computer vision and image understanding", r"\bcviu\b"],
        "name": "CVIU",
        "rank_display": "JCR IF: 4.5 (Q2, Tier 2)",
        "tier": 2,
        "tier_weight": 1.3,
        "is_peer_reviewed": True
    },
    {
        "patterns": [r"pattern recognition", r"\bpr\b"],
        "name": "Pattern Recognition",
        "rank_display": "JCR IF: 7.5 (Q1, Tier 2)",
        "tier": 2,
        "tier_weight": 1.4,
        "is_peer_reviewed": True
    },

    # --------------------------------------------------------------------------
    # Preprints and Non-Peer Reviewed Archives
    # --------------------------------------------------------------------------
    {
        "patterns": [r"\barxiv\b", r"\bcorr\b", r"biorxiv", r"techrxiv", r"ssrn", r"osf\.io"],
        "name": "arXiv",
        "rank_display": "Preprint (arXiv)",
        "tier": 3,
        "tier_weight": 0.9,
        "is_peer_reviewed": False
    }
]


def evaluate_venue(venue_raw: str, url: str = "") -> Dict[str, Any]:
    """
    Deterministically maps a venue name and URL to its academic rank and impact factor.

    Args:
        venue_raw: Raw string from Semantic Scholar / CrossRef metadata.
        url: Paper URL (helpful to catch arxiv.org links when venue is blank).

    Returns:
        Dict containing:
            - impact_factor: str (Formatted label e.g., 'CORE A* (Tier 1, H5: 389)' or 'Preprint (arXiv)')
            - venue_name: str (Clean canonical venue name)
            - tier: int (1=Flagship, 2=Specialized, 3=Baseline/Preprint)
            - tier_weight: float (Score multiplier for ranking formula)
            - is_peer_reviewed: bool
    """
    venue_clean = (venue_raw or "").strip().lower()
    url_clean = (url or "").strip().lower()

    # 1. Direct regex match against canonical database
    for entry in VENUE_DATABASE:
        for pattern in entry["patterns"]:
            if re.search(pattern, venue_clean, re.IGNORECASE) or (entry["name"] == "arXiv" and re.search(pattern, url_clean, re.IGNORECASE)):
                return {
                    "impact_factor": entry["rank_display"],
                    "venue_name": entry["name"],
                    "tier": entry["tier"],
                    "tier_weight": entry["tier_weight"],
                    "is_peer_reviewed": entry["is_peer_reviewed"]
                }

    # 2. Heuristic check for IEEE / ACM / Springer general publications
    if "ieee" in venue_clean:
        return {
            "impact_factor": "Peer-Reviewed (IEEE)",
            "venue_name": venue_raw or "IEEE Publication",
            "tier": 2,
            "tier_weight": 1.2,
            "is_peer_reviewed": True
        }
    if "acm" in venue_clean:
        return {
            "impact_factor": "Peer-Reviewed (ACM)",
            "venue_name": venue_raw or "ACM Publication",
            "tier": 2,
            "tier_weight": 1.2,
            "is_peer_reviewed": True
        }
    if "springer" in venue_clean or "elsevier" in venue_clean:
        return {
            "impact_factor": "Peer-Reviewed (Journal)",
            "venue_name": venue_raw or "Academic Journal",
            "tier": 2,
            "tier_weight": 1.15,
            "is_peer_reviewed": True
        }

    # 3. ArXiv fallback if URL points to arxiv
    if "arxiv" in url_clean:
        return {
            "impact_factor": "Preprint (arXiv)",
            "venue_name": "arXiv",
            "tier": 3,
            "tier_weight": 0.9,
            "is_peer_reviewed": False
        }

    # 4. Unknown / Default Fallback
    display_name = venue_raw if (venue_raw and venue_raw.lower() not in {"unknown", "n/a", "none"}) else "Academic Publication"
    return {
        "impact_factor": "Academic Conf / Unranked",
        "venue_name": display_name,
        "tier": 3,
        "tier_weight": 1.0,
        "is_peer_reviewed": True if display_name != "Academic Publication" else False
    }


def enrich_paper_venue(paper: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enriches a single paper dictionary in-place with deterministic impact factor and tier metadata.
    """
    venue_str = str(paper.get("venue") or "")
    url_str = str(paper.get("url") or "") + " " + str(paper.get("pdf_url") or "")
    evaluation = evaluate_venue(venue_str, url_str)

    paper["impact_factor"] = evaluation["impact_factor"]
    paper["venue_tier"] = evaluation["tier"]
    paper["venue_tier_weight"] = evaluation["tier_weight"]
    paper["is_peer_reviewed"] = evaluation["is_peer_reviewed"]
    if evaluation["venue_name"] and evaluation["venue_name"] != "Academic Publication":
        paper["venue"] = evaluation["venue_name"]
    return paper
