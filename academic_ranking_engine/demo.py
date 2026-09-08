import asyncio
import sys
from academic_ranking_engine.discovery_engine import DiscoveryEngine
from academic_ranking_engine.models import PaperMetadata

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


def display_results_rich(papers: list[PaperMetadata], query: str):
    """Renders dual-bucket ranked papers in a color-coded Rich terminal table."""
    console = Console()
    console.print(Panel.fit(
        f"[bold cyan]Academic Paper Discovery & Hybrid Ranking Engine[/bold cyan]\n"
        f"Query: [yellow]'{query}'[/yellow] | Papers Ranked: [green]{len(papers)}[/green]",
        title="🎓 Discovery Engine Demo",
        border_style="cyan"
    ))

    table = Table(title="🏆 Dual-Bucket Ranked Publications (Foundational vs SOTA)", border_style="dim")
    table.add_column("Rank", justify="center", style="bold white", width=5)
    table.add_column("Bucket", justify="center", style="bold", width=12)
    table.add_column("Title & Year", style="cyan", width=42)
    table.add_column("Venue (Tier)", style="magenta", width=22)
    table.add_column("Citations", justify="right", style="green", width=9)
    table.add_column("Velocity", justify="right", style="yellow", width=11)
    table.add_column("Code Repo", justify="center", style="blue", width=12)
    table.add_column("Score", justify="right", style="bold red", width=8)

    for idx, p in enumerate(papers, 1):
        bucket_style = "[bold green]SOTA (65%)[/bold green]" if p.ranking_bucket == "sota" else "[bold blue]Found (35%)[/bold blue]"
        tier_tag = f"T{p.venue_tier}" if p.venue_tier else "N/A"
        venue_short = (p.venue[:14] + "..") if len(p.venue) > 16 else (p.venue or "Preprint")
        venue_display = f"{venue_short} ({tier_tag})"

        code_display = "[green]✓ GitHub[/green]" if p.has_code else "[dim]N/A[/dim]"
        title_display = f"{p.title[:38]}... ({p.year})" if len(p.title) > 38 else f"{p.title} ({p.year})"

        table.add_row(
            f"#{idx}",
            bucket_style,
            title_display,
            venue_display,
            str(p.citation_count),
            f"{p.citation_velocity:.1f}/yr",
            code_display,
            f"{p.score:.1f}"
        )

    console.print(table)


def display_results_plain(papers: list[PaperMetadata], query: str):
    """Fallback plain text printer if rich is not installed."""
    print("=" * 80)
    print(f"🎓 Academic Paper Discovery & Hybrid Ranking Engine: '{query}'")
    print("=" * 80)
    engine = DiscoveryEngine()
    print(engine.to_markdown_table(papers))
    print("=" * 80)


async def main():
    query = sys.argv[1] if len(sys.argv) > 1 else "monocular 3d human pose physics diffusion"
    print(f"[*] Initializing Discovery Engine for query: '{query}'...")

    engine = DiscoveryEngine()
    # Discover 10 papers with 35% Foundational / 65% SOTA blend
    ranked_papers = await engine.discover_and_rank(
        query=query,
        total_limit=10,
        foundation_ratio=0.35
    )

    if HAS_RICH:
        display_results_rich(ranked_papers, query)
    else:
        display_results_plain(ranked_papers, query)

    # Print score details for top paper
    if ranked_papers:
        top = ranked_papers[0]
        print(f"\n[+] Top Ranked Paper: '{top.title}'")
        print(f"    - Score: {top.score} (Tier {top.venue_tier}, Weight: {top.venue_weight}x)")
        print(f"    - Citation Velocity: {top.citation_velocity} cit/yr (Citations: {top.citation_count}, Influential: {top.influential_citation_count})")
        print(f"    - Code Repository: {top.code_url or 'N/A'}")
        print(f"    - Score Breakdown: {top.score_breakdown}")


if __name__ == "__main__":
    asyncio.run(main())
