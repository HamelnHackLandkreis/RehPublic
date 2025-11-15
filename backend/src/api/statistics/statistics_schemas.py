"""Pydantic schemas for statistics-related request/response validation."""

from datetime import datetime
from typing import List

from pydantic import BaseModel


class SpeciesCountResponse(BaseModel):
    """Schema for species count in statistics."""

    name: str
    count: int


class TimePeriodStatisticsResponse(BaseModel):
    """Schema for statistics for a time period."""

    start_time: datetime
    end_time: datetime
    species: List[SpeciesCountResponse]
    total_spottings: int


class StatisticsResponse(BaseModel):
    """Schema for statistics endpoint response."""

    statistics: List[TimePeriodStatisticsResponse]
