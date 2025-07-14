"""
Tavily search API client for timely and accurate search results.
"""
import os

from tavily import TavilyClient

class TavilySearch:
    """Wrapper class for Tavily search client."""
    
    def __init__(self, api_key: str = os.getenv('TAVILY_API_KEY', "")):
        """
        Initialize Tavily search client.
        
        Args:
            api_key: Tavily API key
        """
        self.client = TavilyClient(api_key)

    def search(self, query: str, include_answer: bool = True) -> tuple[str, str]:
        """
        Execute a search query.
        
        Args:
            query: Search query string
            include_answer: Whether to include AI-generated answer
        
        Returns:
            Tuple (answer, urls):
            - answer: AI-generated answer
            - urls: String of search result URLs, separated by newlines
        """
        response = self.client.search(
            query=query,
            include_answer=include_answer
        )

        answer = response.get("answer", "")
        results = response.get("results", [])
        
        urls = []
        for result in results:
            if url := result.get("url"):
                urls.append(url)
                
        return answer, "\n".join(urls)

def tavily_search(query: str):
    """
    Search using Tavily API for timely and accurate results.

    Args:
        query: Search query string, preferably in English.
    
    Returns:
        Tuple (answer, urls):
        - answer: AI-generated answer
        - urls: String of search result URLs, separated by newlines
    """
    tavily_search = TavilySearch()
    answer, urls = tavily_search.search(query)
    return answer, urls

if __name__ == "__main__":
    import  time
    start_time = time.time()
    answer, urls = tavily_search("US-China trade war now")
    end_time = time.time()
    print(answer)
    print(urls)
    print(f"耗时: {end_time - start_time} 秒")