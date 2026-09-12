import os
import sys
import re
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.telemetry import get_telemetry
import agent_config as config


def chunk_papers(papers: List[Dict[str, Any]], batch_size: int = 4) -> List[List[Dict[str, Any]]]:
    """Partitions paper list into micro-batches of batch_size to prevent LLM attention loss."""
    if not papers:
        return []
    bs = max(1, batch_size)
    return [papers[i : i + bs] for i in range(0, len(papers), bs)]

def _clean_code_fences(text: str) -> str:
    """Strips outer markdown code block delimiters if present."""
    t = text.strip()
    if t.startswith("```markdown"):
        t = t[len("```markdown"):].strip()
    elif t.startswith("```"):
        t = t[len("```"):].strip()
    if t.endswith("```"):
        t = t[:-3].strip()
    return t

def merge_markdown_tables(table_outputs: List[str]) -> str:
    """Deterministically merges Markdown tables from worker chunks into a single unified table."""
    if not table_outputs:
        return ""
    if len(table_outputs) == 1:
        return _clean_code_fences(table_outputs[0])

    primary_header: Optional[str] = None
    primary_divider: Optional[str] = None
    all_data_rows: List[str] = []
    trailing_notes: List[str] = []

    divider_pattern = re.compile(r"^\|(?:\s*:?-+:?\s*\|)+\s*$")

    for out_text in table_outputs:
        clean = _clean_code_fences(out_text)
        lines = clean.splitlines()
        in_table = False
        found_local_header = False

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            is_table_row = stripped.startswith("|") and stripped.endswith("|")
            is_divider = bool(divider_pattern.match(stripped))

            if is_table_row:
                in_table = True
                if is_divider:
                    if not primary_divider:
                        primary_divider = stripped
                    continue

                if not found_local_header:
                    found_local_header = True
                    if not primary_header:
                        primary_header = stripped
                    continue

                # Data row
                all_data_rows.append(stripped)
            else:
                if in_table and stripped and not stripped.startswith("#"):
                    # Collect relevant footnotes/commentary outside the table
                    if stripped not in trailing_notes:
                        trailing_notes.append(stripped)

    if not primary_header or not primary_divider:
        # Fallback if no structured table was found
        return "\n\n---\n\n".join(_clean_code_fences(t) for t in table_outputs)

    result_parts = [primary_header, primary_divider] + all_data_rows
    table_text = "\n".join(result_parts)

    if trailing_notes:
        table_text += "\n\n" + "\n".join(trailing_notes)

    return table_text


def execute_subagent_mapreduce(
    papers: List[Dict[str, Any]],
    prompt: str,
    domain_name: str = "domain",
    batch_size: Optional[int] = None,
    max_workers: Optional[int] = None,
    telemetry = None
) -> str:
    """
    Executes Hierarchical MapReduce across paper chunks for a sub-agent domain.
    Dispatches parallel worker threads for chunks of 3-4 papers, then merges tables deterministically.
    """
    from src.agents.sub_agents import run_agent, format_papers_for_prompt

    if not papers:
        return f"No {domain_name} papers found."

    bs = batch_size or getattr(config, "SUBAGENT_BATCH_SIZE", 4)
    mw = max_workers or getattr(config, "SUBAGENT_MAX_WORKERS", 4)
    agent_tag = f"sub_agent:{domain_name}" if not domain_name.startswith("sub_agent:") else domain_name

    # Single-shot path if papers fit within 1 batch
    if len(papers) <= bs:
        return run_agent(
            prompt,
            format_papers_for_prompt(papers),
            agent_name=agent_tag,
            telemetry=telemetry
        )

    # Hierarchical MapReduce path
    batches = chunk_papers(papers, batch_size=bs)
    tm = telemetry or get_telemetry()
    tm.thinking(
        f"Partitioning {len(papers)} papers into {len(batches)} worker chunks (batch size: {bs})",
        source=agent_tag
    )

    results: List[str] = ["" for _ in batches]

    def _process_chunk(chunk_idx: int, chunk_papers_data: List[Dict[str, Any]]) -> tuple:
        chunk_tag = f"{agent_tag}:chunk_{chunk_idx + 1}/{len(batches)}"
        user_prompt = format_papers_for_prompt(chunk_papers_data)
        out = run_agent(prompt, user_prompt, agent_name=chunk_tag, telemetry=telemetry)
        return chunk_idx, out

    worker_count = min(mw, len(batches))
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = [executor.submit(_process_chunk, idx, b) for idx, b in enumerate(batches)]
        for future in as_completed(futures):
            c_idx, c_out = future.result()
            results[c_idx] = c_out

    merged_output = merge_markdown_tables(results)
    tm.response(
        f"MapReduce completed: merged {len(papers)} papers across {len(batches)} chunks",
        source=agent_tag
    )
    return merged_output


if __name__ == "__main__":
    print("==================================================")
    print("🗺️ Sub-Agent MapReduce Standalone Health Check")
    print("==================================================")

    # Test 1: Chunking logic
    mock_papers = [{"title": f"Paper {i}", "citations": i} for i in range(11)]
    chunks_4 = chunk_papers(mock_papers, batch_size=4)
    assert len(chunks_4) == 3, f"Expected 3 chunks for 11 items with size 4, got {len(chunks_4)}"
    assert len(chunks_4[0]) == 4 and len(chunks_4[1]) == 4 and len(chunks_4[2]) == 3
    print("[*] Paper Chunking: PASSED")

    # Test 2: Deterministic Markdown Table Merging
    worker_1_table = """
| Paper Title & Year | Citations | Code Repo | Key Metrics |
| :--- | :--- | :--- | :--- |
| [Paper 1 (2024)](url1) | 10 | [repo1](https://github.com/a/b) | FID: 0.12 |
| [Paper 2 (2023)](url2) | 25 | N/A | MPJPE: 45mm |
"""
    worker_2_table = """
```markdown
| Paper Title & Year | Citations | Code Repo | Key Metrics |
| :--- | :--- | :--- | :--- |
| [Paper 3 (2024)](url3) | 5 | [repo3](https://github.com/c/d) | FID: 0.08 |
| [Paper 4 (2022)](url4) | 50 | [repo4](https://github.com/e/f) | FID: 0.20 |
```
"""
    merged = merge_markdown_tables([worker_1_table, worker_2_table])
    assert "| [Paper 1 (2024)](url1) |" in merged
    assert "| [Paper 2 (2023)](url2) |" in merged
    assert "| [Paper 3 (2024)](url3) |" in merged
    assert "| [Paper 4 (2022)](url4) |" in merged
    # Header should appear exactly once
    assert merged.count("| Paper Title & Year |") == 1
    assert "```" not in merged
    print("[*] Markdown Table Merging: PASSED")
    print("✅ All MapReduce Health Checks Passed Successfully!")
    print("==================================================")
