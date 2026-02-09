"""Fetch repeater data from the RSGB ETCC API and BrandMeister talkgroups."""

from __future__ import annotations

import logging

import requests

from .config import (
    API_BASE_URL,
    BRANDMEISTER_API_URL,
    CURATED_TALKGROUP_IDS,
    MAX_NAME_LENGTH,
    PRIVATE_CALL_IDS,
    TALKGROUP_NAME_OVERRIDES,
)
from .models import Repeater, TalkGroup

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


class BrandMeisterClient:
    """Client for the BrandMeister talkgroup API."""

    def __init__(self, base_url: str = BRANDMEISTER_API_URL, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def fetch_talkgroups(self) -> list[TalkGroup]:
        """Fetch curated UK-relevant talkgroups from the BrandMeister API."""
        url = f"{self.base_url}/talkgroup/"
        logger.info("Fetching %s", url)
        resp = requests.get(url, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        return self._filter_and_parse(data)

    @staticmethod
    def _filter_and_parse(data: dict) -> list[TalkGroup]:
        """Filter API response to curated talkgroup IDs and return TalkGroup list."""
        if not data:
            logger.warning("Empty response from BrandMeister API")
            return []

        talkgroups: list[TalkGroup] = []
        found_ids: set[int] = set()

        for key, name in data.items():
            try:
                tg_id = int(key)
            except (ValueError, TypeError):
                continue

            if tg_id not in CURATED_TALKGROUP_IDS:
                continue

            found_ids.add(tg_id)

            tg_name = TALKGROUP_NAME_OVERRIDES.get(tg_id, name)
            tg_name = tg_name[:MAX_NAME_LENGTH]

            call_type = "Private Call" if tg_id in PRIVATE_CALL_IDS else "Group Call"

            talkgroups.append(
                TalkGroup(
                    name=tg_name,
                    radio_id=tg_id,
                    call_type=call_type,
                    call_alert="None",
                )
            )

        missing = CURATED_TALKGROUP_IDS - found_ids
        for tg_id in sorted(missing):
            tg_name = TALKGROUP_NAME_OVERRIDES.get(tg_id, str(tg_id))
            tg_name = tg_name[:MAX_NAME_LENGTH]
            call_type = "Private Call" if tg_id in PRIVATE_CALL_IDS else "Group Call"
            talkgroups.append(
                TalkGroup(
                    name=tg_name,
                    radio_id=tg_id,
                    call_type=call_type,
                    call_alert="None",
                )
            )
            logger.info(
                "Talkgroup %d not in API response, added as %r", tg_id, tg_name
            )

        talkgroups.sort(key=lambda tg: tg.radio_id)
        return talkgroups
