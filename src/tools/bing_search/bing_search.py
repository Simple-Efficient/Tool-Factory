import os
import requests
import json

from typing import Dict, Any, List, Optional


BING_SEARCH_URL = os.getenv('BING_SEARCH_URL', "")
BING_SEARCH_API_KEY = os.getenv('BING_SEARCH_API_KEY', "")


def bing_search(query: str) -> Dict[str, Any]:
    """
    Search using the Bing Search API.

    Args:
        query: The search query string.

    Returns:
        A dictionary containing the search results.
    """
    url = BING_SEARCH_URL
    
    headers = {
        "Authorization": f"Bearer {BING_SEARCH_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "query": query,
        "api": "bing-search"
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()  # Raise an exception if the request fails

    return response.json()

if __name__ == "__main__":
    print(bing_search("Who is Pony Ma?"))