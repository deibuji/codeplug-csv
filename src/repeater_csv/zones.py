"""Zone assignment for Anytone AT-D878UV."""

from __future__ import annotations

import logging
from collections import defaultdict

from .config import MAX_NAME_LENGTH, MAX_ZONE_CHANNELS
from .models import AnytoneChannel, AnytoneZone

logger = logging.getLogger(__name__)


def assign_zones(channels: list[AnytoneChannel]) -> list[AnytoneZone]:
    """Group channels into zones by band + mode, splitting at MAX_ZONE_CHANNELS."""
    groups: dict[str, list[AnytoneChannel]] = defaultdict(list)
    for ch in channels:
        key = f"{ch.band} {ch.mode}"
        groups[key].append(ch)

    zones: list[AnytoneZone] = []
    for key in sorted(groups):
        members = groups[key]
        if len(members) <= MAX_ZONE_CHANNELS:
            zone_name = key[:MAX_NAME_LENGTH]
            zones.append(AnytoneZone(name=zone_name, channels=members))
        else:
            # Split into multiple zones
            for i in range(0, len(members), MAX_ZONE_CHANNELS):
                chunk = members[i : i + MAX_ZONE_CHANNELS]
                part = i // MAX_ZONE_CHANNELS + 1
                zone_name = f"{key} {part}"[:MAX_NAME_LENGTH]
                zones.append(AnytoneZone(name=zone_name, channels=chunk))

    logger.info("Created %d zones", len(zones))
    return zones
