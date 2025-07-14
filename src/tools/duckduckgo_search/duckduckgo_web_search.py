"""
Web search using DuckDuckGo, focused on privacy-protecting search results.
"""
from typing import Dict, Any, List, Optional


def duckduckgo_web_search(query: str, max_results: int = 5) -> str:
    """
    Perform a web search using DuckDuckGo, which aggregates results from major search engines with a focus on privacy.
    
    Args:
        query: Search query string (preferably in English)
        max_results: Maximum number of results to return (default: 5)
        
    Returns:
        Search result text, including title, summary, and URL
    """
    try:
        from duckduckgo_search import DDGS
        results = DDGS().text(query, max_results=max_results)
        return results
    except Exception as e:
        return f"DuckDuckGo search error: {str(e)}"
    
if __name__ == "__main__":
    results = duckduckgo_web_search("Who is the most handsome person in China?")
    print(results)