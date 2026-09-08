from datetime import date, datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class Author(BaseModel):
    """Scholarly author metadata."""
    model_config = ConfigDict(extra="ignore")

    name: str
    author_id: Optional[str] = None
    h_index: Optional[int] = None


class PaperMetadata(BaseModel):
    """
    Standardized scholarly publication data model for academic discovery
    and hybrid ranking.
    """
    model_config = ConfigDict(extra="ignore")

    paper_id: str
    title: str
    abstract: Optional[str] = None
    year: int
    publication_date: Optional[date] = None
    venue: str = ""
    venue_tier: Optional[int] = None
    venue_weight: float = 1.0
    fields_of_study: List[str] = Field(default_factory=list)
    citation_count: int = 0
    influential_citation_count: int = 0
    is_open_access: bool = False
    open_access_pdf_url: Optional[str] = None
    code_url: Optional[str] = None
    authors: List[Author] = Field(default_factory=list)
    score: Optional[float] = None
    ranking_bucket: Optional[str] = None  # "foundation" | "sota"
    score_breakdown: Dict[str, Any] = Field(default_factory=dict)

    @property
    def has_code(self) -> bool:
        """Returns True if paper has a detected GitHub or code repository."""
        return bool(self.code_url and self.code_url != "N/A" and "github.com" in self.code_url.lower())

    @property
    def delta_t(self) -> float:
        """
        Calculates elapsed time in years using month precision when available:
        delta_t = max(0.5, current_year - pub_year + (12 - pub_month)/12)
        """
        now = datetime.now()
        curr_year = now.year
        curr_month = now.month

        if self.publication_date:
            pub_year = self.publication_date.year
            pub_month = self.publication_date.month
            dt = (curr_year - pub_year) + ((curr_month - pub_month) / 12.0)
        else:
            pub_year = self.year or curr_year
            # Default to mid-year (June) when month is unspecified
            dt = (curr_year - pub_year) + ((12 - 6) / 12.0)

        return max(0.5, round(dt, 2))

    @property
    def citation_velocity(self) -> float:
        """
        Computes citation velocity with 2.5x weighting for influential citations:
        V_cit = (citations + 2.5 * influential_citations) / delta_t
        """
        dt = self.delta_t
        raw_velocity = (self.citation_count + 2.5 * self.influential_citation_count) / dt
        return round(raw_velocity, 2)


if __name__ == "__main__":
    test_paper = PaperMetadata(
        paper_id="2109.00123",
        title="Physics-Guided Motion Diffusion",
        year=2024,
        publication_date=date(2024, 3, 1),
        venue="CVPR",
        citation_count=45,
        influential_citation_count=8,
        is_open_access=True,
        code_url="https://github.com/example/phys-motion",
        authors=[Author(name="Jane Doe", h_index=32)]
    )
    print(f"[*] Paper: {test_paper.title}")
    print(f"    - Delta T: {test_paper.delta_t} years")
    print(f"    - Citation Velocity: {test_paper.citation_velocity}")
    print(f"    - Has Code: {test_paper.has_code}")
