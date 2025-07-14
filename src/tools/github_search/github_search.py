from typing import Optional
from github import Github
from github.Repository import Repository

import time

def github_search(query: str, 
                 token: Optional[str] = None,
                 sort: str = "stars",
                 order: str = "desc",
                 max_results: int = 10) -> str:
    """
    Tool function for searching GitHub repositories
    
    Args:
        query (str): Search keywords
        token (str, optional): GitHub API token. If not provided, unauthenticated mode will be used (subject to rate limits)
        sort (str): Sorting method, options: 'stars', 'forks', 'updated', etc.
        order (str): Sorting order, options: 'desc' or 'asc'
        max_results (int): Maximum number of results to return
        
    Returns:
        str: Formatted string of search results
    """
    try:
        # Initialize GitHub client
        g = Github(token) if token else Github()
        
        # Execute search
        repositories = g.search_repositories(query=query, sort=sort, order=order)
        
        results = []
        count = 0
        
        for repo in repositories:
            if count >= max_results:
                break
                
            repo_info = {
                "name": repo.full_name,
                "description": repo.description,
                "url": repo.html_url,
                "stars": repo.stargazers_count,
                "forks": repo.forks_count,
                "language": repo.language
            }
            
            results.append(repo_info)
            count += 1
            time.sleep(1)  # Avoid triggering API rate limits
            
        # Format output results
        output = f"Found the following GitHub repositories related to '{query}':\n\n"
        
        for idx, repo in enumerate(results, 1):
            output += f"{idx}. {repo['name']}\n"
            output += f"   Description: {repo['description']}\n"
            output += f"   URL: {repo['url']}\n"
            output += f"   Stars: {repo['stars']}\n"
            output += f"   Forks: {repo['forks']}\n"
            output += f"   Main language: {repo['language']}\n\n"
            
        return output
        
    except Exception as e:
        return f"An error occurred while searching GitHub repositories: {str(e)}" 

if __name__ == "__main__":
    print(github_search("youtube transcript"))