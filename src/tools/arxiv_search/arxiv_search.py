"""
Search Arxiv academic paper database, focusing on scientific research papers.
"""
import logging
from typing import Dict, Any, List, Optional

def arxiv_search(query: str, max_results: int = 5 ) -> str:
    """
    Search the Arxiv academic paper database, focusing on scientific research papers.
    
    Args:
        query: Search query string, preferably English academic keywords.
        max_results: Maximum number of results to return, default is 5.
    
    Returns:
        Search result text, including paper title, authors, abstract, and link.
    """
    try:
        from langchain_community.tools.arxiv import ArxivQueryRun
        from langchain_community.utilities import ArxivAPIWrapper
        
        api_wrapper = ArxivAPIWrapper(
            top_k_results=max_results,
            load_max_docs=max_results,
            load_all_available_meta=True
        )
        search_tool = ArxivQueryRun(api_wrapper=api_wrapper)
        results = search_tool.run(query)
        
        return results
    except Exception as e:
        return f"Arxiv search error: {str(e)}"

if __name__ == "__main__":
    results = arxiv_search("Agent Memory")
    print(results)
