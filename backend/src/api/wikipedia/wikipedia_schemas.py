"""Pydantic schemas for Wikipedia-related request/response validation."""

from typing import List

from pydantic import BaseModel


class WikipediaArticleResponse(BaseModel):
    """Schema for Wikipedia article response."""

    title: str
    description: str | None
    image_url: str | None
    article_url: str


class WikipediaArticlesRequest(BaseModel):
    """Schema for Wikipedia articles request."""

    titles: List[str]  # List of article titles to fetch
