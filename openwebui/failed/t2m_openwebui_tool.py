"""
title: IEEE Academic Search Tool
author: Dmitry Strizhak
version: 1.2.0
license: MIT
description: Open WebUI Tool to search IEEE Xplore (via EZproxy), securing full-text PDFs.
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.fetchers.ieee_fetcher import fetch_ieee_papers
from src.utils.pdf_downloader import download_pdfs

class Tools:
    def __init__(self):
        pass

    def search_academic_papers(self, query: str, max_results: int = 5) -> str:
        """
        Searches IEEE Xplore (via Afeka EZproxy) for academic papers on a given topic,
        downloads full-text PDFs to articles/, and returns structured Markdown results.
        
        :param query: Search query topic (e.g. 'text-to-motion', 'physics diffusion', 'RL character control')
        :param max_results: Maximum number of papers to fetch
        """
        unique_papers = fetch_ieee_papers(query=query, max_results=max_results)
        
        if not unique_papers:
            return f"No IEEE papers found for query: '{query}'."
                
        articles_dir = os.path.join(PROJECT_ROOT, "articles")
        downloaded = download_pdfs(unique_papers, output_dir=articles_dir)
        
        report = f"### 📚 IEEE Search Results for '{query}'\n"
        report += f"**Found {len(unique_papers)} IEEE papers.** (Saved {downloaded} PDFs to `articles/`).\n\n"
        
        for i, p in enumerate(unique_papers, 1):
            report += f"{i}. **[{p['title']}]({p['url']})** ({p.get('year', 'N/A')})\n"
            report += f"   - **Venue:** {p.get('venue', 'IEEE')} | **Citations:** {p.get('citations', 0)}\n"
            report += f"   - **PDF Link (EZproxy):** {p.get('pdf_url', 'N/A')}\n"
            report += f"   - **Abstract:** {p.get('abstract', '')[:180]}...\n\n"
            
        return report
