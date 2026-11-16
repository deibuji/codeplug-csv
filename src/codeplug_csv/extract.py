"""Fetch repeater data from the RSGB ETCC API and BrandMeister talkgroups."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import aiofiles
import httpx
from pydantic import ValidationError

from .config import (
    API_BASE_URL,
    BRANDMEISTER_API_URL,
    HTTP_TIMEOUT,
    MAX_CONCURRENT,
    MAX_NAME_LENGTH,
    NON_UK_CURATED_IDS,
    PRIVATE_CALL_IDS,
    RADIOID_CSV_URL,
    RADIOID_TIMEOUT,
    TALKGROUP_NAME_OVERRIDES,
    UK_TG_PREFIX,
)
from .models import Repeater, RepeaterModel, TalkGroup

logger = logging.getLogger(__name__)


def _make_talkgroup(tg_id: int, fallback_name: str) -> TalkGroup:
    """Build an Anytone talkgroup entry for *tg_id*."""
    name = TALKGROUP_NAME_OVERRIDES.get(tg_id, fallback_name)[:MAX_NAME_LENGTH]
    return TalkGroup(
        name=name,
        radio_id=tg_id,
        call_type="Private Call" if tg_id in PRIVATE_CALL_IDS else "Group Call",
        call_alert="None",
    )


class RSGBClient:
    """Client for the RSGB ETCC beta API."""

    def __init__(
        self,
        base_url: str = API_BASE_URL,
        timeout: int = HTTP_TIMEOUT,
        max_concurrent: int = MAX_CONCURRENT,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> RSGBClient:
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def fetch_band(self, band: str) -> list[Repeater]:
        """Fetch all repeaters for a given band (e.g. '2m', '70cm')."""
        url = f"{self.base_url}/band/{band}"
        async with self.semaphore:
            if not self._client:
                raise RuntimeError("Client must be used as an async context manager")
            logger.debug("Fetching %s", url)
            resp = await self._client.get(url)
            resp.raise_for_status()
            data = resp.json().get("data", [])

        # Skip individual malformed records rather than failing the whole run.
        repeaters: list[Repeater] = []
        for item in data:
            try:
                repeaters.append(self._parse(item))
            except ValidationError as exc:
                logger.warning(
                    "Skipping malformed repeater record %r: %s",
                    item.get("repeater") or item.get("id"),
                    exc,
                )
        logger.info("Got %d repeaters for %s", len(repeaters), band)
        return repeaters

    async def fetch_bands(self, bands: list[str]) -> list[Repeater]:
        """Fetch repeaters for multiple bands."""
        tasks = [self.fetch_band(band) for band in bands]
        results = await asyncio.gather(*tasks)
        return [repeater for band_results in results for repeater in band_results]

    @staticmethod
    def _parse(item: dict) -> Repeater:
        cleaned = {k: v for k, v in item.items() if v is not None}
        validated = RepeaterModel.model_validate(cleaned)
        return Repeater(**validated.model_dump())


class BrandMeisterClient:
    """Client for the BrandMeister talkgroup API."""

    def __init__(
        self, base_url: str = BRANDMEISTER_API_URL, timeout: int = HTTP_TIMEOUT
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> BrandMeisterClient:
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def fetch_talkgroups(self) -> list[TalkGroup]:
        """Fetch curated UK-relevant talkgroups from the BrandMeister API."""
        if not self._client:
            raise RuntimeError("Client must be used as an async context manager")
        url = f"{self.base_url}/talkgroup/"
        logger.debug("Fetching %s", url)
        resp = await self._client.get(url)
        resp.raise_for_status()
        data = resp.json()
        talkgroups = self._filter_and_parse(data)
        logger.info("Fetched %d talkgroups from BrandMeister", len(talkgroups))
        return talkgroups

    @staticmethod
    def _filter_and_parse(data: dict) -> list[TalkGroup]:
        """Filter API response to UK-prefix and curated talkgroup IDs."""
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

            is_uk = key.startswith(UK_TG_PREFIX)
            is_curated = tg_id in NON_UK_CURATED_IDS
            if not is_uk and not is_curated:
                continue

            found_ids.add(tg_id)
            talkgroups.append(_make_talkgroup(tg_id, name))

        for tg_id in sorted(NON_UK_CURATED_IDS - found_ids):
            tg = _make_talkgroup(tg_id, str(tg_id))
            talkgroups.append(tg)
            logger.debug(
                "Talkgroup %d not in API response, added as %r", tg_id, tg.name
            )

        talkgroups.sort(key=lambda tg: tg.radio_id)
        return talkgroups


class RadioIDClient:
    """Client for downloading the RadioID DMR user database."""

    def __init__(self, url: str = RADIOID_CSV_URL, timeout: int = RADIOID_TIMEOUT):
        self.url = url
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> RadioIDClient:
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def download(self, dest: Path) -> Path:
        """Stream the RadioID user CSV to *dest* and return the path written.

        The download streams to a temporary ``.part`` file and is only moved
        onto *dest* once complete, so a failed or cancelled run never leaves a
        truncated contact list behind.
        """
        if not self._client:
            raise RuntimeError("Client must be used as an async context manager")
        tmp = dest.with_name(f"{dest.name}.part")
        logger.info("Downloading RadioID database from %s", self.url)
        try:
            async with self._client.stream("GET", self.url) as response:
                response.raise_for_status()
                async with aiofiles.open(tmp, "wb") as fh:
                    async for chunk in response.aiter_bytes():
                        await fh.write(chunk)
            tmp.replace(dest)
        finally:
            tmp.unlink(missing_ok=True)
        logger.info("Wrote RadioID database to %s", dest)
        return dest
