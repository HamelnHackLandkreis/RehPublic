"""Controller for Wikipedia endpoints."""

import logging
from typing import List

from fastapi import APIRouter, HTTPException, status

from api.wikipedia.wikipedia_schemas import (
    WikipediaArticleResponse,
    WikipediaArticlesRequest,
)
from api.wikipedia.wikipedia_service import WikipediaService

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize dependencies
wikipedia_service = WikipediaService()


@router.post(
    "/articles",
    response_model=List[WikipediaArticleResponse],
    status_code=status.HTTP_200_OK,
    tags=["wikipedia"],
)
async def get_wikipedia_articles(
    request: WikipediaArticlesRequest,
) -> List[WikipediaArticleResponse]:
    """Fetch Wikipedia articles with main image, description, and link.

    This endpoint fetches data from the Wikipedia API for the provided article titles.
    For each article, it returns:
    - title: The article title
    - description: A short description or extract from the article
    - image_url: URL to the main/thumbnail image (if available)
    - article_url: Direct link to the Wikipedia article

    Args:
        request: List of Wikipedia article titles to fetch

    Returns:
        List of Wikipedia article data (articles not found will be omitted)

    Example:
        POST /wikipedia/articles
        {
            "titles": ["Red deer", "Wild boar", "European badger"]
        }
    """
    try:
        articles_data = await wikipedia_service.fetch_articles(request.titles)
        articles = [
            WikipediaArticleResponse(**article_data) for article_data in articles_data
        ]
        return articles
    except Exception as e:
        logger.error(f"Failed to fetch Wikipedia articles: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch Wikipedia articles: {str(e)}",
        )
