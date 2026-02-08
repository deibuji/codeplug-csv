"""Transform RSGB repeater data into Anytone channel format."""

from __future__ import annotations

import logging
import re

from .config import EXCLUDED_TYPES, MAX_NAME_LENGTH
from .models import AnytoneChannel, Repeater

logger = logging.getLogger(__name__)


def filter_repeaters(
    repeaters: list[Repeater],
    locator_prefix: str | None = None,
) -> list[Repeater]:
    """Keep only operational analog/DMR repeaters, excluding beacons etc."""
    result = []
    for r in repeaters:
        if r.status != "OPERATIONAL":
            continue
        if r.type in EXCLUDED_TYPES:
            continue
        has_analog = "A" in r.mode_codes
        has_dmr = any(mc == "M" or mc.startswith("M:") for mc in r.mode_codes)
        if not (has_analog or has_dmr):
            continue
        if locator_prefix and not r.locator.upper().startswith(locator_prefix.upper()):
            continue
        result.append(r)
    logger.info("Filtered to %d repeaters", len(result))
    return result


def _hz_to_mhz(hz: int) -> str:
    """Convert frequency in Hz to MHz string with 5 decimal places."""
    return f"{hz / 1_000_000:.5f}"


def _clean_callsign(callsign: str) -> str:
    """Strip link suffixes like -L, -R from callsign."""
    return re.sub(r"-[A-Z]$", "", callsign)


def _make_channel_name(callsign: str, town: str, suffix: str) -> str:
    """Build a channel name within MAX_NAME_LENGTH chars.

    Format: '{callsign} {town_truncated} {suffix}'
    """
    clean = _clean_callsign(callsign)
    # Reserve space for callsign + space + suffix
    prefix_len = len(clean) + 1 + len(suffix) + 1  # +1 for space before suffix
    available = MAX_NAME_LENGTH - prefix_len
    if available > 0 and town:
        town_part = town[:available]
        name = f"{clean} {town_part} {suffix}"
    else:
        name = f"{clean} {suffix}"
    return name[:MAX_NAME_LENGTH]


def _extract_color_code(mode_codes: list[str]) -> int:
    """Extract DMR color code from modeCodes.

    'M:3' → 3, bare 'M' → 1 (default).
    """
    for mc in mode_codes:
        if mc.startswith("M:"):
            try:
                return int(mc.split(":")[1])
            except (IndexError, ValueError):
                pass
    return 1


def _bandwidth_str(txbw: float) -> str:
    """Convert txbw value to Anytone bandwidth string."""
    if txbw >= 25:
        return "25K"
    return "12.5K"


def _ctcss_str(ctcss: float) -> str:
    """Format CTCSS tone or 'Off'."""
    if ctcss > 0:
        return f"{ctcss:.1f}"
    return "Off"


def _band_label(band: str) -> str:
    """Normalise band string to lowercase label."""
    return band.lower().replace(" ", "")


def transform_repeaters(
    repeaters: list[Repeater],
    power: str = "High",
) -> list[AnytoneChannel]:
    """Convert filtered Repeater list to AnytoneChannel list.

    Multimode repeaters (both A and M in modeCodes) produce two channels.
    """
    channels: list[AnytoneChannel] = []
    for r in repeaters:
        has_analog = "A" in r.mode_codes
        has_dmr = any(mc == "M" or mc.startswith("M:") for mc in r.mode_codes)
        band = _band_label(r.band)

        # API tx = repeater transmits → radio receives
        rx_freq = _hz_to_mhz(r.tx)
        tx_freq = _hz_to_mhz(r.rx)

        if has_analog:
            channels.append(
                AnytoneChannel(
                    name=_make_channel_name(r.repeater, r.town, "FM"),
                    rx_freq=rx_freq,
                    tx_freq=tx_freq,
                    channel_type="A-Analog",
                    bandwidth=_bandwidth_str(r.txbw),
                    ctcss_encode=_ctcss_str(r.ctcss),
                    ctcss_decode=_ctcss_str(r.ctcss),
                    power=power,
                    band=band,
                    mode="FM",
                )
            )

        if has_dmr:
            cc = _extract_color_code(r.mode_codes)
            channels.append(
                AnytoneChannel(
                    name=_make_channel_name(r.repeater, r.town, "DMR"),
                    rx_freq=rx_freq,
                    tx_freq=tx_freq,
                    channel_type="D-Digital",
                    bandwidth="12.5K",
                    power=power,
                    color_code=cc,
                    slot=1,
                    contact="Local",
                    contact_call_type="Group Call",
                    band=band,
                    mode="DMR",
                )
            )

    logger.info("Generated %d channels", len(channels))
    return channels
