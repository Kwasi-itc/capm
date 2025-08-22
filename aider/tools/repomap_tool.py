"""
An intelligent repository mapping tool inspired by the Aider repomap implementation.

This tool builds a semantic graph of the codebase to rank and display the most
relevant components based on their definitions and references, using the PageRank
algorithm. It uses tree-sitter for language-aware parsing and diskcache for
performance.

Required dependencies:
pip install networkx grep-ast diskcache tqdm jsonschema
"""
from __future__ import annotations
import math
import shutil
from abc import ABC, abstractmethod
from typing import Any, Dict, List
from pathlib import Path
from collections import defaultdict, Counter, namedtuple
import concurrent.futures
import os

# --- Third-party libraries ---
import jsonschema
import networkx as nx
from aider.tools.base_tool import BaseTool
from diskcache import Cache
from tqdm import tqdm
import logging

logger = logging.getLogger(__name__)

# --- grep-ast for code parsing ---
# tree_sitter is a dependency of grep-ast
from grep_ast import filename_to_lang
from grep_ast.tsl import get_language, get_parser, USING_TSL_PACK
from aider.repomap import get_scm_fname


# --- Intelligent RepoMap Tool ---

# Named tuple for clarity when handling parsed tags
Tag = namedtuple("Tag", "rel_fname fname line name kind".split())

class RepoMapTool(BaseTool):
    """
    A tool that generates an intelligent map of a repository using graph analysis
    to identify and rank the most important files and code definitions.
    """
    name: str = "intelligent_repomap"
    description: str = (
        "Generates an intelligent repository map by building a code graph and using "
        "PageRank to find the most relevant files and symbols. Use 'focus_files' to "
        "center the map around specific areas of interest."
    )
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "The root directory path of the repository to scan.",
                "default": ".",
            },
            "focus_files": {
                "type": "array",
                "items": {"type": "string"},
                "description": "A list of files to prioritize in the ranking, helping to focus the map.",
                "default": [],
            },
            "max_tokens": {
                "type": "integer",
                "description": "The target maximum token count for the final map.",
                "default": 2048,
            }
        },
        "required": [],
    }

    def __init__(self, root: str | Path | None = None):
        self.root = Path(root).resolve() if root else Path.cwd()

        # Common virtual-env / dependency folders we should skip when walking the repo
        self.EXCLUDE_DIRS = {
            ".git",
            "venv",
            ".venv",
            "env",
            ".env",
            "aider-env",
            "__pycache__",
            "node_modules",
            "site-packages",
            "build",        # ignore build artefacts
            ".next",        # ignore Next.js build output
        }
        # Use a versioned cache directory to avoid conflicts if the tool's logic changes.
        cache_version = 5 if USING_TSL_PACK else 4
        self.cache_dir = self.root / f".repomap.cache.v{cache_version}"
        self._initialize_cache()
        self.definitions = defaultdict(set)

    def _initialize_cache(self):
        """Initializes the disk cache, handling potential DB errors by recreating it."""
        try:
            self.tags_cache = Cache(self.cache_dir)
        except Exception as e:
            logger.warning("Could not initialize disk cache at %s: %s", self.cache_dir, e)
            logger.warning("Attempting to recreate cache.")
            try:
                if self.cache_dir.exists():
                    shutil.rmtree(self.cache_dir)
                self.tags_cache = Cache(self.cache_dir)
            except Exception as e2:
                logger.error("Failed to recreate cache. Falling back to in-memory dict: %s", e2)
                self.tags_cache = {}

    def _get_rel_path(self, p: Path) -> str:
        """Get the relative path as a string from the repo root."""
        return str(p.relative_to(self.root))

    def _token_count(self, text: str) -> int:
        """A simple, fast estimation of token count (chars / 4)."""
        return len(text) // 4

    def _get_tags_from_file(self, file_path: Path) -> List[Tag]:
        """
        Parses a single file using tree-sitter to extract code tags (definitions and references).
        Results are cached on disk for performance.
        """
        rel_fname = self._get_rel_path(file_path)
        try:
            mtime = file_path.stat().st_mtime
        except FileNotFoundError:
            return []

        cache_key = str(file_path)
        cached = self.tags_cache.get(cache_key)
        if cached and cached.get("mtime") == mtime:
            return [Tag(**tag_dict) for tag_dict in cached["data"]]

        tags = self._parse_tags_raw(file_path, rel_fname)
        
        # Store as list of dicts for JSON compatibility in cache
        self.tags_cache[cache_key] = {"mtime": mtime, "data": [t._asdict() for t in tags]}
        return tags

    def _parse_tags_raw(self, file_path: Path, rel_fname: str) -> List[Tag]:
        """The core parsing logic for a file using tree-sitter queries."""
        lang = filename_to_lang(str(file_path))
        if not lang:
            return []

        try:
            language = get_language(lang)
            parser = get_parser(lang)
            query_scm_path = get_scm_fname(lang)
            if not query_scm_path or not query_scm_path.exists():
                return []
            query_scm = query_scm_path.read_text()
            code = file_path.read_bytes()
        except Exception as e:
            logger.warning("Skipping file %s due to setup error: %s", file_path, e)
            return []

        tree = parser.parse(code)
        query = language.query(query_scm)
        captures = query.captures(tree.root_node)

        # Handle different return shapes between tree-sitter-language-pack and tree-sitter-languages
        if USING_TSL_PACK:
            all_nodes = []
            for tag_name, nodes in captures.items():
                all_nodes += [(node, tag_name) for node in nodes]
        else:
            all_nodes = captures

        results = []
        for node, tag_name in all_nodes:
            kind = None
            if tag_name.startswith("name.definition."):
                kind = "def"
            elif tag_name.startswith("name.reference."):
                kind = "ref"

            if kind:
                tag = Tag(
                    rel_fname=rel_fname,
                    fname=str(file_path),
                    name=node.text.decode("utf-8", errors="ignore"),
                    kind=kind,
                    line=node.start_point[0] + 1, # Use 1-based line numbers
                )
                results.append(tag)
        return results

    def _build_code_graph(self, all_files: List[Path]) -> nx.MultiDiGraph:
        """
        Builds a directed graph where nodes are files and edges represent code references.
        """
        defines = defaultdict(set)
        references = defaultdict(list)
        self.definitions.clear()

        # Gather all definitions and references from files
        files_to_process = [f for f in all_files if f.is_file()]
        cpu_cnt = os.cpu_count() or 4
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(cpu_cnt, 8)) as executor:
            futures = {
                executor.submit(self._get_tags_from_file, fp): fp for fp in files_to_process
            }
            for fut in tqdm(
                concurrent.futures.as_completed(futures),
                total=len(futures),
                desc="1/3 Parsing files",
                unit="file",
            ):
                file_path = futures[fut]
                rel_path_str = self._get_rel_path(file_path)
                try:
                    tags = fut.result()
                except Exception as e:
                    logger.warning("Error parsing %s: %s", file_path, e)
                    continue

                for tag in tags:
                    if tag.kind == "def":
                        defines[tag.name].add(rel_path_str)
                        self.definitions[(rel_path_str, tag.name)].add(tag)
                    elif tag.kind == "ref":
                        references[tag.name].append(rel_path_str)

        # Build the graph from the collected data
        G = nx.MultiDiGraph()
        idents = set(defines.keys()).intersection(references.keys())

        for ident in tqdm(idents, desc="2/3 Building graph", unit="ident"):
            definers = defines[ident]
            for referencer, num_refs in Counter(references[ident]).items():
                for definer in definers:
                    if referencer != definer:
                        weight = math.sqrt(num_refs) # Diminish returns for many refs
                        G.add_edge(referencer, definer, weight=weight, ident=ident)
        return G

    def _rank_definitions(self, G: nx.MultiDiGraph, focus_files: List[str]) -> List[Tag]:
        """
        Ranks code definitions using PageRank on the code graph.
        """
        if not G.nodes:
            return []

        personalization = {file: 1.0 for file in focus_files if file in G}

        try:
            pagerank_scores = nx.pagerank(G, weight="weight", personalization=personalization or None)
        except ZeroDivisionError:
            return []

        # Distribute rank from files to the definitions within them
        ranked_definitions = defaultdict(float)
        for src, dst, data in G.edges(data=True):
            if src in pagerank_scores:
                rank = pagerank_scores.get(src, 0) * data["weight"]
                ranked_definitions[(dst, data["ident"])] += rank
        
        sorted_defs = sorted(ranked_definitions.items(), key=lambda item: item[1], reverse=True)

        ranked_tags = []
        for (fname, ident), _ in sorted_defs:
            ranked_tags.extend(list(self.definitions.get((fname, ident), [])))
            
        return ranked_tags

    def _format_map(self, tags: List[Tag]) -> str:
        """Formats the final list of ranked tags into a readable tree structure."""
        if not tags:
            return ""

        output = []
        files_to_render: dict[str, list[str]] = defaultdict(list)

        # Cache file contents so we only read each source file once
        file_lines_cache: dict[str, list[str]] = {}

        def get_snippet(file_path: str, line_no: int) -> str:
            """Return the stripped source line at 1-based *line_no* (may be empty)."""
            if file_path not in file_lines_cache:
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        file_lines_cache[file_path] = f.readlines()
                except Exception:
                    file_lines_cache[file_path] = []
            lines = file_lines_cache[file_path]
            if 0 <= (line_no - 1) < len(lines):
                snippet = lines[line_no - 1].strip()
                # Truncate very long lines to keep output readable
                return snippet[:120]
            return ""

        # Group tags by file, adding a helpful code snippet after the name/line
        for tag in tags:
            snippet = get_snippet(tag.fname, tag.line)
            if snippet:
                files_to_render[tag.rel_fname].append(
                    f"  - {tag.name} (line {tag.line}): {snippet}"
                )
            else:
                files_to_render[tag.rel_fname].append(f"  - {tag.name} (line {tag.line})")

        for fname, items in files_to_render.items():
            output.append(f"{fname}:")
            # Show unique, sorted items to avoid redundancy
            unique_items = sorted(list(set(items)))
            output.extend(unique_items[:10]) # Limit to top 10 items per file
            if len(unique_items) > 10:
                output.append("  - ...")
            output.append("")

        return "\n".join(output)

    def run(self, path: str = ".", focus_files: List[str] = [], max_tokens: int = 2048) -> str:
        """Main execution method for the tool."""
        self.root = Path(path).resolve()
        logger.info(f"Starting intelligent repo map for {self.root}")

        def _should_exclude(p: Path) -> bool:
            return any(part in self.EXCLUDE_DIRS for part in p.parts)

        all_files = [p for p in self.root.rglob('*') if p.is_file() and not _should_exclude(p)]

        # Convert focus files to repository-relative paths so they match graph node names
        focus_files_rel = [
            self._get_rel_path(Path(f).resolve()) for f in focus_files
            if Path(f).exists()
        ]
        
        graph = self._build_code_graph(all_files)
        ranked_tags = self._rank_definitions(graph, focus_files_rel)

        # Binary search to find the optimal number of tags for the token limit
        low, high = 0, len(ranked_tags)
        best_map = ""
        
        pbar = tqdm(total=high, desc="3/3 Formatting map", unit="tag")
        while low <= high:
            mid = (low + high) // 2
            if mid == 0:
                pbar.update(high)
                break
            
            # Advance the progress bar by the *actual* amount of new tags examined
            increment = mid - pbar.n
            if increment > 0:
                pbar.update(increment)
            
            current_tags = ranked_tags[:mid]
            formatted_map = self._format_map(current_tags)
            token_count = self._token_count(formatted_map)

            if token_count <= max_tokens:
                best_map = formatted_map
                low = mid + 1
            else:
                high = mid - 1
        # Ensure the progress bar reaches 100 % before closing
        if pbar.n < pbar.total:
            pbar.update(pbar.total - pbar.n)
        pbar.close()

        return best_map or "Could not generate a repository map within the token limit."
