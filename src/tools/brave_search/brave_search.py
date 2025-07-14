"""
Search using the Brave search engine, providing privacy-focused results.
"""
import os
import logging
from typing import Dict, Any, List, Optional


def brave_search(query: str, max_results: int = 5) -> str:
    """
    Search using the Brave search engine with its independent web index for more accurate results.

    Args:
        query: Search query string, preferably in English.
        max_results: Maximum number of results to return, default is 5.

    Returns:
        Search result text, including title, summary, and URL.
    """
    try:
        from langchain_community.tools import BraveSearch
        from langchain_community.utilities import BraveSearchWrapper

        api_key = os.getenv("BRAVE_SEARCH_API_KEY", "")
        if not api_key:
            return "Error: BRAVE_SEARCH_API_KEY is not set."

        search_wrapper = BraveSearchWrapper(
            api_key=api_key,
            search_kwargs={"count": max_results}
        )
        search_tool = BraveSearch(search_wrapper=search_wrapper)
        results = search_tool.run(query)

        return results
    except Exception as e:
        return f"Brave search error: {str(e)}"

if __name__ == "__main__":
    results = brave_search("Who is the most influential person in China?")
    print(results)
