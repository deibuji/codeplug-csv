"""Zone assignment for Anytone."""

from __future__ import annotations

import logging
from collections import defaultdict

from .config import (
    GATEWAY_LABELS,
    MAX_ZONE_CHANNELS,
    MODE_LABELS,
    fit_name,
)
from .models import AnytoneChannel, AnytoneZone

logger = logging.getLogger(__name__)


def _zone_label(channel: AnytoneChannel) -> str:
    """Return a compact, user-facing zone label for *channel*.

    Repeaters use FM/DMR.  Gateways use AG/DG, which also encodes the mode
    while keeping the gateway channels in their own zones.
    """
    labels = GATEWAY_LABELS if channel.rpt_type == "GW" else MODE_LABELS
    mode = labels.get(channel.mode, channel.mode)
    return f"{channel.region} {channel.band} {mode}"


def _ensure_unique_zone_names(zones: list[AnytoneZone]) -> None:
    """Disambiguate any zone names that collide after truncation."""
    seen: set[str] = set()
    for zone in zones:
        if zone.name not in seen:
            seen.add(zone.name)
            continue

        base = zone.name
        attempt = 2
        while fit_name(base, f"~{attempt}") in seen:
            attempt += 1
        zone.name = fit_name(base, f"~{attempt}")
        seen.add(zone.name)
        logger.warning("Duplicate zone name %r renamed to %r", base, zone.name)


def assign_zones(channels: list[AnytoneChannel]) -> list[AnytoneZone]:
    """Group channels by region + band + mode + type.

    Groups larger than ``MAX_ZONE_CHANNELS`` are split into numbered zones.
    """
    groups: dict[str, list[AnytoneChannel]] = defaultdict(list)
    for channel in channels:
        groups[_zone_label(channel)].append(channel)

    zones: list[AnytoneZone] = []
    for key in sorted(groups):
        members = groups[key]
        if len(members) <= MAX_ZONE_CHANNELS:
            zones.append(AnytoneZone(name=fit_name(key), channels=members))
            continue

        for i in range(0, len(members), MAX_ZONE_CHANNELS):
            chunk = members[i : i + MAX_ZONE_CHANNELS]
            part = i // MAX_ZONE_CHANNELS + 1
            zones.append(
                AnytoneZone(name=fit_name(key, f" {part}"), channels=chunk)
            )

    _ensure_unique_zone_names(zones)
    logger.info("Created %d zones", len(zones))
    return zones
