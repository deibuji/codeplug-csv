"""Opt-in live-data checks for channel naming and zone membership."""

from __future__ import annotations

import os

import pytest

from codeplug_csv.config import BANDS
from codeplug_csv.extract import RSGBClient
from codeplug_csv.transform import filter_repeaters, transform_repeaters
from codeplug_csv.zones import assign_zones

pytestmark = [
    pytest.mark.network,
    pytest.mark.asyncio,
    pytest.mark.skipif(
        os.environ.get("CODEPLUG_CSV_LIVE_TESTS") != "1",
        reason="set CODEPLUG_CSV_LIVE_TESTS=1 to run live network checks",
    ),
]


async def test_live_names_are_unique_and_zones_are_single_band():
    async with RSGBClient() as client:
        repeaters = await client.fetch_bands(list(BANDS))

    channels = transform_repeaters(filter_repeaters(repeaters))
    names = [channel.name for channel in channels]

    assert len(names) == len(set(names))

    zones = assign_zones(channels)
    zone_names = [zone.name for zone in zones]
    assert len(zone_names) == len(set(zone_names))

    for zone in zones:
        assert len({channel.band for channel in zone.channels}) == 1, zone.name
        members = [channel.name for channel in zone.channels]
        assert len(members) == len(set(members)), zone.name
