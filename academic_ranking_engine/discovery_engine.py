import asyncio
import re
from datetime import datetime
from typing import List, Dict, Optional, Set
import httpx

from academic_ranking_engine.models import PaperMetadata
from academic_ranking_engine.scorer import calculate_paper_score, ScoringConfig
from academic_ranking_engine.client import AcademicSearchClient


def normalize_title(title: str) -> str:
    """Standardizes title for cross-stream de-duplication."""
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", "", title.lower())
    return " ".join(cleaned.split())


def generate_subqueries(query: str) -> List[str]:
    """Decomposes long multi-topic academic queries into targeted sub-queries."""
    words = [w for w in query.strip().split() if len(w) > 1]
    if len(words) <= 4:
        return []
    sub_q = []
    if "physics" in words and "diffusion" in words:
        base = " ".join([w for w in words if w not in ["physics", "diffusion"]])
        sub_q.extend([f"{base} physics", f"{base} diffusion", "3d human pose physics diffusion"])
    else:
        mid = len(words) // 2
        sub_q.extend([" ".join(words[:mid + 2]), " ".join(words[mid - 1:])])
    return [q.strip() for q in sub_q if q.strip() and q.strip() != query]


class DiscoveryEngine:
    """
    Dual-Bucket Academic Discovery & Hybrid Ranking Engine.
    Mitigates citation-lag bias by concurrently evaluating Foundational Baselines
    and Recent SOTA Frontier works with sub-query expansion and arXiv fallback.
    """

    def __init__(self, client: Optional[AcademicSearchClient] = None, scoring_config: Optional[ScoringConfig] = None):
        self.client = client or AcademicSearchClient()
        self.scoring_config = scoring_config or ScoringConfig()

    async def discover_and_rank(
        self, query: str, total_limit: int = 10, foundation_ratio: float = 0.35
    ) -> List[PaperMetadata]:
        """Retrieves, scores, de-duplicates, and blends foundational vs SOTA papers."""
        curr_year = datetime.now().year
        cutoff_year = curr_year - 2

        target_found = max(1, int(round(total_limit * foundation_ratio)))
        target_sota = total_limit - target_found

        raw_found: List[PaperMetadata] = []
        raw_sota: List[PaperMetadata] = []

        queries_to_run = [query]
        sub_queries = generate_subqueries(query)

        async with httpx.AsyncClient(timeout=self.client.timeout) as session:
            # Step 1: Query with primary query (SOTA then Foundational)
            s_res = await self.client.fetch_semantic_scholar(query, f"{cutoff_year}-{curr_year}", target_sota * 3, session)
            raw_sota.extend(s_res)
            f_res = await self.client.fetch_semantic_scholar(query, f"-{cutoff_year}", target_found * 3, session)
            raw_found.extend(f_res)

            # Step 2: Sub-query expansion if composite query returned scarce papers
            if len(raw_found) + len(raw_sota) < total_limit and sub_queries:
                for sq in sub_queries:
                    if len(raw_found) >= target_found * 2 and len(raw_sota) >= target_sota * 2:
                        break
                    s_sub = await self.client.fetch_semantic_scholar(sq, f"{cutoff_year}-{curr_year}", target_sota * 2, session)
                    raw_sota.extend(s_sub)
                    f_sub = await self.client.fetch_semantic_scholar(sq, f"-{cutoff_year}", target_found * 2, session)
                    raw_found.extend(f_sub)

            # Step 3: ArXiv fallback if S2 failed or returned nothing
            if not raw_found and not raw_sota:
                arxiv_res = await self.client.fetch_arxiv(query, limit=total_limit, client=session)
                for p in arxiv_res:
                    (raw_sota if p.year >= cutoff_year else raw_found).append(p)

        # Step 4: Score and rank Stream A (Foundational)
        for p in raw_found:
            calculate_paper_score(p, "foundation", self.scoring_config)
        raw_found.sort(key=lambda x: x.score or 0.0, reverse=True)

        # Step 5: Score and rank Stream B (Frontier / SOTA)
        for p in raw_sota:
            calculate_paper_score(p, "sota", self.scoring_config)
        raw_sota.sort(key=lambda x: x.score or 0.0, reverse=True)

        # Step 6: De-duplicate and blend
        seen_ids: Set[str] = set()
        seen_titles: Set[str] = set()
        final_papers: List[PaperMetadata] = []

        def _add_unique(paper_list: List[PaperMetadata], max_to_add: int) -> int:
            added = 0
            for paper in paper_list:
                norm = normalize_title(paper.title)
                if paper.paper_id in seen_ids or norm in seen_titles:
                    continue
                seen_ids.add(paper.paper_id)
                seen_titles.add(norm)
                final_papers.append(paper)
                added += 1
                if added >= max_to_add:
                    break
            return added

        added_sota = _add_unique(raw_sota, target_sota)
        added_found = _add_unique(raw_found, target_found)

        # Backfill deficit if one bucket had fewer candidates
        deficit = total_limit - len(final_papers)
        if deficit > 0:
            _add_unique(raw_sota[added_sota:], deficit)
            deficit = total_limit - len(final_papers)
            if deficit > 0:
                _add_unique(raw_found[added_found:], deficit)

        return final_papers

    @staticmethod
    def to_markdown_table(papers: List[PaperMetadata]) -> str:
        """Renders ranked papers into a GitHub-Flavored Markdown summary table."""
        headers = ["Bucket", "Rank", "Title & Year", "Venue (Tier)", "Citations", "Velocity", "Code Repo", "Score"]
        rows = [f"| {' | '.join(headers)} |", f"| {' | '.join(['---'] * len(headers))} |"]
        for idx, p in enumerate(papers, 1):
            tier_str = f"T{p.venue_tier}" if p.venue_tier else "N/A"
            venue_disp = f"{p.venue[:18]} ({tier_str})" if p.venue else f"Preprint ({tier_str})"
            code_disp = f"[GitHub]({p.code_url})" if p.has_code else "N/A"
            title_disp = f"{p.title[:46]}... ({p.year})" if len(p.title) > 46 else f"{p.title} ({p.year})"
            b_tag = "SOTA" if p.ranking_bucket == "sota" else "Found"
            rows.append(
                f"| {b_tag} | #{idx} | {title_disp} | {venue_disp} | "
                f"{p.citation_count} | {p.citation_velocity:.1f}/yr | {code_disp} | **{p.score:.1f}** |"
            )
        return "\n".join(rows)


if __name__ == "__main__":
    async def _test():
        engine = DiscoveryEngine()
        results = await engine.discover_and_rank("monocular 3d human pose physics diffusion", total_limit=10)
        print("==================================================")
        print(f"🎯 Dual-Bucket Discovery Test ({len(results)} papers)")
        print("==================================================")
        print(engine.to_markdown_table(results))
        print("==================================================")

    asyncio.run(_test())
