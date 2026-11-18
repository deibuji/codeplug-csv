"""Zone assignment for Anytone."""

from __future__ import annotations

import logging
from collections import defaultdict

from .config import (
    GATEWAY_LABELS,
    MAX_ZONE_CHANNELS,
    MODE_LABELS,
    band_label,
    band_rank,
    fit_name,
)
from .models import AnytoneChannel, AnytoneZone
from .regions import region_sort_key

logger = logging.getLogger(__name__)


def _zone_parts(channel: AnytoneChannel) -> tuple[str, str, str]:
    """Return the (region, band, mode) labels shown in a zone name.

    Repeaters use FM/DV.  Gateways use AG/DG, which also encodes the mode
    while keeping the gateway channels in their own zones.
    """
    labels = GATEWAY_LABELS if channel.rpt_type == "GW" else MODE_LABELS
    mode = labels.get(channel.mode, channel.mode)
    return channel.region, band_label(channel.band), mode


def _zone_key(channel: AnytoneChannel) -> tuple[tuple[bool, str], int, str, str]:
    """Return the sortable grouping key for *channel*.

    Bands use an explicit rank so VHF sorts before UHF (sorting the rendered
    label would put UHF first and renumber every channel in Channel.CSV), and
    regions are ranked so the ``OTHER`` catch-all sorts last.
    """
    region, band, mode = _zone_parts(channel)
    return region_sort_key(region), band_rank(channel.band), band, mode


def _zone_label(key: tuple[tuple[bool, str], int, str, str]) -> str:
    """Render a grouping key as the user-facing zone name."""
    (_is_other, region), _rank, band, mode = key
    return f"{region} {band} {mode}"


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
    groups: dict[tuple[tuple[bool, str], int, str, str], list[AnytoneChannel]] = (
        defaultdict(list)
    )
    for channel in channels:
        groups[_zone_key(channel)].append(channel)

    zones: list[AnytoneZone] = []
    for key in sorted(groups):
        members = groups[key]
        label = _zone_label(key)
        if len(members) <= MAX_ZONE_CHANNELS:
            zones.append(AnytoneZone(name=fit_name(label), channels=members))
            continue

        for i in range(0, len(members), MAX_ZONE_CHANNELS):
            chunk = members[i : i + MAX_ZONE_CHANNELS]
            part = i // MAX_ZONE_CHANNELS + 1
            zones.append(
                AnytoneZone(name=fit_name(label, f" {part}"), channels=chunk)
            )

    _ensure_unique_zone_names(zones)
    logger.info("Created %d zones", len(zones))
    return zones


def drop_empty_zones(zones: list[AnytoneZone]) -> list[AnytoneZone]:
    """Return *zones* with any channel-less zone removed.

    Zones are built from channels, so an empty zone means its members were
    dropped upstream.  Writing it would emit a Zone.CSV row with no
    ``Zone Channel Member`` and an empty ``A Channel``, which the CPS cannot
    import, so it is dropped loudly rather than silently written.
    """
    for zone in zones:
        if not zone.channels:
            logger.warning("Dropping empty zone %r", zone.name)
    return [zone for zone in zones if zone.channels]
