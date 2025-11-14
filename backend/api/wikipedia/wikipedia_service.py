"""Service for fetching Wikipedia article data."""

import logging
from functools import lru_cache
from typing import Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class WikipediaService:
    """Service for fetching Wikipedia article data."""

    WIKIPEDIA_API_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/"
    WIKIPEDIA_BASE_URL = "https://en.wikipedia.org/wiki/"

    def __init__(self):
        """Initialize Wikipedia service with LRU cache."""
        self._cache = {}  # Manual cache for async function

    @lru_cache(maxsize=128)
    def _get_cached_article(self, title: str) -> Optional[Dict]:
        """Internal cache lookup method.

        This method serves as a cache key storage. The actual data
        is stored in self._cache to work with async operations.

        Args:
            title: Article title

        Returns:
            Cached article data or None
        """
        return self._cache.get(title)

    def _set_cached_article(self, title: str, data: Optional[Dict]) -> None:
        """Store article data in cache.

        Args:
            title: Article title
            data: Article data to cache
        """
        self._cache[title] = data
        # Trigger the lru_cache to register this key
        self._get_cached_article(title)

    async def fetch_article(self, title: str) -> Optional[Dict]:
        """Fetch a single Wikipedia article summary with caching.

        Args:
            title: Article title

        Returns:
            Dictionary with article data or None if not found
        """
        # Check cache first
        cached_data = self._cache.get(title)
        if cached_data is not None:
            logger.info(f"Wikipedia article retrieved from cache: {title}")
            return cached_data

        try:
            # Wikipedia requires a User-Agent header to prevent abuse
            headers = {
                "User-Agent": "WildlifeCameraAPI/0.1 (Educational project; contact: your-email@example.com)"
            }

            async with httpx.AsyncClient(headers=headers) as client:
                # Encode title for URL
                encoded_title = title.replace(" ", "_")
                url = f"{self.WIKIPEDIA_API_URL}{encoded_title}"

                response = await client.get(url, timeout=10.0)

                if response.status_code == 404:
                    logger.warning(f"Wikipedia article not found: {title}")
                    # Cache the None result to avoid repeated failed lookups
                    self._set_cached_article(title, None)
                    return None

                response.raise_for_status()
                data = response.json()

                # Extract relevant fields - use extract for longer text content
                article_data = {
                    "title": data.get("title", title),
                    "description": data.get(
                        "extract"
                    ),  # This contains the full paragraph(s)
                    "image_url": data.get("thumbnail", {}).get("source")
                    if "thumbnail" in data
                    else None,
                    "article_url": data.get("content_urls", {})
                    .get("desktop", {})
                    .get("page", f"{self.WIKIPEDIA_BASE_URL}{encoded_title}"),
                }

                # Cache the successful result
                self._set_cached_article(title, article_data)
                logger.info(f"Wikipedia article fetched and cached: {title}")

                return article_data

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching Wikipedia article '{title}': {e}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Request error fetching Wikipedia article '{title}': {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching Wikipedia article '{title}': {e}")
            return None

    async def fetch_articles(self, titles: List[str]) -> List[Dict]:
        """Fetch multiple Wikipedia articles.

        Args:
            titles: List of article titles

        Returns:
            List of article data dictionaries (excluding failed fetches)
        """
        results = []

        for title in titles:
            article_data = await self.fetch_article(title)
            if article_data:
                results.append(article_data)

        return results
