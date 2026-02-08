"""Fetch repeater data from the RSGB ETCC API."""

from __future__ import annotations

import logging

import requests

from .config import API_BASE_URL
from .models import Repeater

logger = logging.getLogger(__name__)


class RSGBClient:
    """Client for the RSGB ETCC beta API."""

    def __init__(self, base_url: str = API_BASE_URL, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def fetch_band(self, band: str) -> list[Repeater]:
        """Fetch all repeaters for a given band (e.g. '2m', '70cm')."""
        url = f"{self.base_url}/band/{band}"
        logger.info("Fetching %s", url)
        resp = requests.get(url, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json().get("data", [])
        logger.info("Got %d repeaters for %s", len(data), band)
        return [self._parse(item) for item in data]

    def fetch_bands(self, bands: list[str]) -> list[Repeater]:
        """Fetch repeaters for multiple bands."""
        repeaters: list[Repeater] = []
        for band in bands:
            repeaters.extend(self.fetch_band(band))
        return repeaters

    @staticmethod
    def _parse(item: dict) -> Repeater:
        return Repeater(
            repeater=item.get("repeater", ""),
            tx=item.get("tx", 0),
            rx=item.get("rx", 0),
            band=item.get("band", ""),
            mode_codes=item.get("modeCodes") or [],
            ctcss=item.get("ctcss") or 0.0,
            txbw=item.get("txbw") or 12.5,
            town=item.get("town") or "",
            status=item.get("status") or "",
            type=item.get("type") or "",
            locator=item.get("locator") or "",
        )
