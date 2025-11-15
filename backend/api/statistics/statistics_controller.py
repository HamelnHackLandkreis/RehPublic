"""Controller for statistics endpoints."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.database import get_db
from api.statistics.statistics_schemas import (
    SpeciesCountResponse,
    StatisticsResponse,
    TimePeriodStatisticsResponse,
)
from api.locations.location_service import SpottingService

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize dependencies
spotting_service = SpottingService()


@router.get(
    "",
    response_model=StatisticsResponse,
    status_code=status.HTTP_200_OK,
    tags=["statistics"],
)
def get_statistics(
    period: str = Query(
        "day",
        description="Time period range: 'day' (current day), 'week' (last 7 days), 'month' (last 30 days), or 'year' (last 365 days)",
        pattern="^(day|week|month|year)$",
    ),
    granularity: Optional[str] = Query(
        None,
        description="Grouping granularity: 'hourly', 'daily', or 'weekly'. If not provided, defaults based on period (day=hourly, week/month=daily, year=weekly)",
        pattern="^(hourly|daily|weekly)$",
    ),
    limit: Optional[int] = Query(
        None,
        description="Maximum number of spottings to include in statistics before aggregation. If not provided, all spottings in the period are included.",
        gt=0,
    ),
    location_id: Optional[str] = Query(
        None,
        description="Optional location ID to filter statistics by a specific location.",
    ),
    db: Session = Depends(get_db),
) -> StatisticsResponse:
    """Get statistics for animal spottings grouped by time period.

    Returns statistics grouped by time intervals:
    - period="day": Current day (00:00 to now)
    - period="week": Last 7 days
    - period="month": Last 30 days
    - period="year": Last 365 days

    Granularity options:
    - "hourly": Group by hour
    - "daily": Group by day
    - "weekly": Group by week

    Each time period includes:
    - start_time and end_time (ISO 8601 format)
    - species array with name and count
    - total_spottings count

    Query Parameters:
        period: Time period range - "day", "week", "month", or "year" (default: "day")
        granularity: Grouping granularity - "hourly", "daily", or "weekly" (optional, auto-selected if not provided)
        limit: Maximum number of spottings to include before aggregation (optional, for performance)

    Returns:
        Statistics response with list of time periods and their species counts

    Example:
        GET /statistics?period=day&granularity=hourly
        GET /statistics?period=week&granularity=daily
        GET /statistics?period=month&granularity=weekly
        GET /statistics?period=year&granularity=weekly&limit=10000
    """
    try:
        stats_data = spotting_service.get_statistics(
            db,
            period=period,
            granularity=granularity,
            limit=limit,
            location_id=location_id,
        )

        # Convert to response models
        statistics = []
        for stat in stats_data:
            species_list = [
                SpeciesCountResponse(name=species["name"], count=species["count"])
                for species in stat["species"]
            ]
            statistics.append(
                TimePeriodStatisticsResponse(
                    start_time=stat["start_time"],
                    end_time=stat["end_time"],
                    species=species_list,
                    total_spottings=stat["total_spottings"],
                )
            )

        return StatisticsResponse(statistics=statistics)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}",
        )
