import sys
import os

from graph_agent.tools.function.crawler.article import Article
from graph_agent.tools.function.crawler.jina_client import JinaClient
from graph_agent.tools.function.crawler.readability_extractor import ReadabilityExtractor


class Crawler:
    def crawl(self, url: str) -> Article:
        # To help LLMs better understand content, we extract clean
        # articles from HTML, convert them to markdown, and split
        # them into text and image blocks for one single and unified
        # LLM message.
        #
        # Jina is not the best crawler on readability, however it's
        # much easier and free to use.
        #
        # Instead of using Jina's own markdown converter, we'll use
        # our own solution to get better readability results.
        jina_client = JinaClient()
        html = jina_client.crawl(url, return_format="html")
        extractor = ReadabilityExtractor()
        article = extractor.extract_article(html)
        article.url = url
        return article


def crawl_article(url: str) -> str:
    """
    Crawl the web page content of the specified URL and return the content in markdown format.
    """
    try:
        crawler = Crawler()
        article = crawler.crawl(url)
        return article.to_markdown()[:1000]
    except Exception as e:
        return f"Crawling failed: {e}"

if __name__ == "__main__":
    # When running this file directly, add the project root directory to sys.path
    # This allows absolute imports to work properly
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../agent"))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    if len(sys.argv) == 2:
        url = sys.argv[1]
    else:
        url = "https://en.wikipedia.org/wiki/HHhH"
    crawler = Crawler()
    article = crawler.crawl(url)
    print(article.to_markdown())