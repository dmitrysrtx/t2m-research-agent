import re
from typing import Tuple, Optional

# Canonical Tier 1 Venues (Weight = 2.0)
TIER_1_RULES = [
    # Computer Vision / AI / Machine Learning
    (r"\b(cvpr|ieee/cvf conference on computer vision and pattern recognition|computer vision and pattern recognition)\b", "CVPR"),
    (r"\b(iccv|international conference on computer vision)\b", "ICCV"),
    (r"\b(eccv|european conference on computer vision)\b", "ECCV"),
    (r"\b(neurips|nips|neural information processing systems)\b", "NeurIPS"),
    (r"\b(icml|international conference on machine learning)\b", "ICML"),
    (r"\b(iclr|international conference on learning representations)\b", "ICLR"),
    (r"\b(aaai|aaai conference on artificial intelligence)\b", "AAAI"),
    (r"\b(ijcai|international joint conference on artificial intelligence)\b", "IJCAI"),
    # Robotics / Control / Graphics
    (r"\b(siggraph(\s+asia)?|acm transactions on graphics|tog)\b", "SIGGRAPH/TOG"),
    (r"\b(rss|robotics:\s*science and systems)\b", "RSS"),
    (r"\b(icra|ieee international conference on robotics and automation)\b", "ICRA"),
    (r"\b(iros|ieee/rsj international conference on intelligent robots and systems)\b", "IROS"),
    (r"\b(corl|conference on robot learning)\b", "CoRL"),
    # Top Journals
    (r"\b(tpami|ieee transactions on pattern analysis and machine intelligence|pami)\b", "IEEE TPAMI"),
    (r"\b(tvcg|ieee transactions on visualization and computer graphics)\b", "IEEE TVCG"),
    (r"\b(ijcv|international journal of computer vision)\b", "IJCV"),
    (r"\b(t-?ro|ieee transactions on robotics)\b", "IEEE T-RO"),
    (r"\b(ral|ieee robotics and automation letters)\b", "IEEE RAL"),
]

# Canonical Tier 2 Venues (Weight = 1.35)
TIER_2_RULES = [
    (r"\b(wacv|ieee/cvf winter conference on applications of computer vision)\b", "WACV"),
    (r"\b(3dv|international conference on 3d vision)\b", "3DV"),
    (r"\b(bmvc|british machine vision conference)\b", "BMVC"),
    (r"\b(cgf|computer graphics forum)\b", "CGF"),
    (r"\b(iros\s+workshop|iros\s+ws)\b", "IROS Workshop"),
    (r"\b(ieee\s+iv|intelligent vehicles symposium)\b", "IEEE IV"),
    (r"\b(itsc|intelligent transportation systems conference)\b", "IEEE ITSC"),
    (r"\b(neurocomputing)\b", "Neurocomputing"),
    (r"\b(cviu|computer vision and image understanding)\b", "CVIU"),
    (r"\b(pattern recognition(\s+letters)?)\b", "Pattern Recognition"),
]

# Preprints / Unreviewed Repositories (Weight = 0.85)
PREPRINT_RULES = [
    (r"\b(arxiv|arxiv\.org|techrxiv|biorxiv|medrxiv|preprints?)\b", "arXiv / Preprint"),
]


def normalize_venue_name(venue: Optional[str]) -> str:
    """Cleans punctuation, conference years, and noise prefixes from venue string."""
    if not venue:
        return ""
    text = venue.lower().strip()
    # Strip years like 2020, 2024, '23
    text = re.sub(r"\b20\d{2}\b|\b19\d{2}\b", "", text)
    text = re.sub(r"['’]\d{2}\b", "", text)
    # Strip common prefixes
    text = re.sub(r"^(proceedings\s+of(\s+the)?|intl\.?|international|annual)\s+", "", text)
    # Normalize whitespaces
    text = re.sub(r"\s+", " ", text).strip()
    return text


def classify_venue(venue: Optional[str]) -> Tuple[int, float, str]:
    """
    Assigns a prestige tier and multiplier W_venue to an academic venue.

    Returns:
        (tier, weight, canonical_name)
        - Tier 1: 2.0 (Top Conferences & Journals)
        - Tier 2: 1.35 (Strong Specialized Conferences & Journals)
        - Tier 3: 1.0 (Regional / General Peer-Reviewed Venues)
        - Tier 4 (Preprint): 0.85 (arXiv, bioRxiv, unrefereed)
    """
    if not venue or not venue.strip():
        return (4, 0.85, "Preprint (Unspecified)")

    clean_venue = normalize_venue_name(venue)

    # 1. Match Tier 1
    for pattern, canonical in TIER_1_RULES:
        if re.search(pattern, clean_venue):
            return (1, 2.0, canonical)

    # 2. Match Tier 2
    for pattern, canonical in TIER_2_RULES:
        if re.search(pattern, clean_venue):
            return (2, 1.35, canonical)

    # 3. Match Preprints
    for pattern, canonical in PREPRINT_RULES:
        if re.search(pattern, clean_venue):
            return (4, 0.85, canonical)

    # 4. Default to Tier 3 for other publications
    return (3, 1.0, venue.strip())


if __name__ == "__main__":
    test_venues = [
        "IEEE Transactions on Pattern Analysis and Machine Intelligence (TPAMI 2023)",
        "Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition",
        "European Conference on Computer Vision (ECCV 2024)",
        "3DV 2022 Conference",
        "British Machine Vision Conference (BMVC)",
        "arXiv:2303.12345 [cs.CV]",
        "International Journal of General Robotics",
        ""
    ]
    print("==================================================")
    print("🏛️ Venue Classifier Diagnostic")
    print("==================================================")
    for tv in test_venues:
        tier, weight, name = classify_venue(tv)
        print(f"[*] Raw: '{tv[:45]}...' -> Tier {tier} | Weight: {weight}x | Canonical: {name}")
    print("==================================================")
