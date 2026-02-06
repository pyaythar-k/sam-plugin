#!/usr/bin/env python3
"""
Shared research fallback utility for SAM workflow.
Implements tiered fallback based on research type.

Feature research: web-search-prime -> context7 -> brave-search -> web-search
Tech research: context7 -> web-search-prime -> brave-search -> web-search
"""

import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ResearchResult:
    """Container for research results with source tracking."""
    content: str
    source: str
    fallback_level: int
    query: str


class ResearchFallback:
    """
    Tiered fallback mechanism for research operations.

    Fallback chains:
    - Feature research: web-search-prime -> context7 -> brave-search -> web-search
    - Tech research: context7 -> web-search-prime -> brave-search -> web-search

    Usage in Claude Code skills:
        # Import concept (this file is documentation/pattern reference)
        fallback = ResearchFallback()

        # Tech research (Context7 first)
        result = fallback.research(
            query="Latest best practices for feature implementation",
            research_type="tech"
        )

        # Feature research (web search first)
        result = fallback.research(
            query="best practices feature domain implementation 2025",
            research_type="feature"
        )
    """

    def __init__(self):
        self.feature_chain = [
            'web-search-prime',
            'context7',
            'brave-search',
            'web-search'
        ]
        self.tech_chain = [
            'context7',
            'web-search-prime',
            'brave-search',
            'web-search'
        ]
        self.attempt_log: List[Dict[str, Any]] = []

    def research(
        self,
        query: str,
        research_type: str = 'tech',
        max_attempts: int = 4
    ) -> Optional[ResearchResult]:
        """
        Execute research with tiered fallback.

        Args:
            query: Research query
            research_type: 'feature' or 'tech'
            max_attempts: Maximum number of methods to try

        Returns:
            ResearchResult or None if all fail

        Example usage in skill:
            # For tech research (Context7 first, then fallbacks)
            result = fallback.research(
                query="Latest Next.js 15 best practices for API routes",
                research_type="tech"
            )

            # For feature research (web search first, then fallbacks)
            result = fallback.research(
                query="authentication best practices 2025",
                research_type="feature"
            )
        """
        chain = self.feature_chain if research_type == 'feature' else self.tech_chain
        chain = chain[:max_attempts]

        for i, method in enumerate(chain):
            try:
                result = self._try_method(method, query, research_type)
                if result:
                    self.attempt_log.append({
                        'method': method,
                        'success': True,
                        'level': i
                    })
                    logger.info(f"✓ Research success via {method} (level {i})")
                    return ResearchResult(
                        content=result,
                        source=method,
                        fallback_level=i,
                        query=query
                    )
            except Exception as e:
                logger.warning(f"✗ {method} failed: {e}")
                self.attempt_log.append({
                    'method': method,
                    'success': False,
                    'error': str(e)
                })
                continue

        logger.error("✗ All research methods failed")
        return None

    def _try_method(self, method: str, query: str, research_type: str) -> Optional[str]:
        """
        Try a specific research method.

        NOTE: This is a placeholder for the actual implementation.
        In Claude Code skills, this would call the appropriate MCP tool:

        Methods:
        - 'web-search-prime': mcp__web-search-prime__webSearchPrime
        - 'context7': mcp__plugin_context7_context7__query-docs
        - 'brave-search': mcp__plugin_brave_search_brave_search__search
        - 'web-search': WebSearch (built-in)

        Example implementation in skill:
            if method == 'context7':
                return mcp__plugin_context7_context7__query-docs(
                    library_id="/vercel/next.js",
                    query=query
                )
            elif method == 'web-search-prime':
                return mcp__web-search-prime__webSearchPrime(
                    search_query=query
                )
            # ... etc
        """
        # Placeholder - actual implementation in Claude Code skill context
        pass

    def get_report(self) -> str:
        """
        Generate a report of research attempts.

        Returns:
            Markdown formatted report of all research attempts
        """
        lines = ["# Research Fallback Report\n"]

        for attempt in self.attempt_log:
            if attempt.get('success'):
                lines.append(f"✓ {attempt['method']}: Success (level {attempt.get('level', 'N/A')})")
            else:
                lines.append(f"✗ {attempt['method']}: {attempt.get('error', 'Unknown error')}")

        return "\n".join(lines)


# CLI for testing
def main():
    """CLI entry point for testing research fallback."""
    import sys

    query = sys.argv[1] if len(sys.argv) > 1 else "test query"
    research_type = sys.argv[2] if len(sys.argv) > 2 else "tech"

    fallback = ResearchFallback()
    result = fallback.research(query, research_type)

    if result:
        print(f"✓ Research completed via {result.source}")
        print(f"Content:\n{result.content}")
    else:
        print("✗ All research methods failed")

    print(f"\n{fallback.get_report()}")


if __name__ == "__main__":
    main()
