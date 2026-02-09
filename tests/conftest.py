"""Shared test fixtures."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from repeater_csv.extract import RSGBClient
from repeater_csv.models import Repeater

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_api_data() -> list[dict]:
    """Raw API response data list."""
    with open(FIXTURES / "sample_api_response.json") as f:
        return json.load(f)["data"]


@pytest.fixture
def sample_repeaters(sample_api_data: list[dict]) -> list[Repeater]:
    """Parsed Repeater objects from fixture data."""
    return [RSGBClient._parse(item) for item in sample_api_data]


@pytest.fixture
def sample_bm_data() -> dict[str, str]:
    """Raw BrandMeister API response data."""
    with open(FIXTURES / "sample_brandmeister_response.json") as f:
        return json.load(f)
