"""Pydantic schemas for Wikipedia-related request/response validation."""

from typing import List, Optional

from pydantic import BaseModel


class WikipediaArticleResponse(BaseModel):
    """Schema for Wikipedia article response."""

    title: str
    description: Optional[str]
    image_url: Optional[str]
    article_url: str


class WikipediaArticlesRequest(BaseModel):
    """Schema for Wikipedia articles request."""

    titles: List[str]  # List of article titles to fetch
