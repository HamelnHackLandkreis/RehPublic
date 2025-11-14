"""Pytest configuration for API tests."""

import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from api.models import Base
from api.database import get_db
from api.main import app

# Set TESTING environment variable to skip production DB initialization
os.environ["TESTING"] = "1"

# Create test database
TEST_DATABASE_URL = "sqlite:///./test_wildlife_camera.db"
test_engine = create_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    """Override database dependency for testing."""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Override the dependency
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module", autouse=True)
def setup_test_database():
    """Set up test database once for all tests."""
    # Create tables
    Base.metadata.create_all(bind=test_engine)
    yield
    # Drop tables after all tests
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client():
    """Create test client with fresh database."""
    # Clear all data before each test
    db = TestSessionLocal()
    try:
        # Delete all records from tables (in correct order due to foreign keys)
        from api.spottings.spotting_models import Spotting
        from api.images.image_models import Image
        from api.locations.location_models import Location

        db.query(Spotting).delete()
        db.query(Image).delete()
        db.query(Location).delete()
        db.commit()
    finally:
        db.close()

    with TestClient(app) as test_client:
        yield test_client
