"""CSV writers for Anytone AT-D878UV CPS import files."""

from __future__ import annotations

import csv
import logging
from pathlib import Path

from .config import (
    ANALOG_DEFAULTS,
    CHANNEL_COLUMNS,
    DEFAULT_TALKGROUPS,
    DIGITAL_DEFAULTS,
    TALKGROUP_COLUMNS,
    ZONE_COLUMNS,
)
from .models import AnytoneChannel, AnytoneZone, TalkGroup

logger = logging.getLogger(__name__)


def _channel_row(number: int, ch: AnytoneChannel) -> dict[str, str]:
    """Build a full row dict with all columns for a single channel."""
    if ch.channel_type == "D-Digital":
        row = dict(DIGITAL_DEFAULTS)
    else:
        row = dict(ANALOG_DEFAULTS)

    row["No."] = str(number)
    row["Channel Name"] = ch.name
    row["Receive Frequency"] = ch.rx_freq
    row["Transmit Frequency"] = ch.tx_freq
    row["Channel Type"] = ch.channel_type
    row["Transmit Power"] = ch.power
    row["Band Width"] = ch.bandwidth
    row["CTCSS/DCS Encode"] = ch.ctcss_encode
    row["CTCSS/DCS Decode"] = ch.ctcss_decode
    row["Color Code"] = str(ch.color_code)
    row["Slot"] = str(ch.slot)
    row["Contact"] = ch.contact
    row["Contact Call Type"] = ch.contact_call_type
    row["TX Prohibit"] = ch.tx_prohibit

    return row


def write_channels(channels: list[AnytoneChannel], output_dir: Path) -> Path:
    """Write Channel.CSV with all required columns."""
    path = output_dir / "Channel.CSV"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CHANNEL_COLUMNS, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for i, ch in enumerate(channels, start=1):
            writer.writerow(_channel_row(i, ch))
    logger.info("Wrote %d channels to %s", len(channels), path)
    return path


def write_zones(zones: list[AnytoneZone], output_dir: Path) -> Path:
    """Write Zone.CSV."""
    path = output_dir / "Zone.CSV"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=ZONE_COLUMNS, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for i, zone in enumerate(zones, start=1):
            members = "|".join(ch.name for ch in zone.channels)
            a_channel = zone.channels[0].name if zone.channels else ""
            b_channel = zone.channels[0].name if zone.channels else ""
            writer.writerow(
                {
                    "No.": str(i),
                    "Zone Name": zone.name,
                    "Zone Channel Member": members,
                    "A Channel": a_channel,
                    "B Channel": b_channel,
                }
            )
    logger.info("Wrote %d zones to %s", len(zones), path)
    return path


def write_talkgroups(output_dir: Path) -> Path:
    """Write TalkGroups.CSV with default UK DMR talkgroups."""
    talkgroups = [
        TalkGroup(
            name=tg["name"],
            radio_id=tg["id"],
            call_type=tg["call_type"],
            call_alert=tg["alert"],
        )
        for tg in DEFAULT_TALKGROUPS
    ]

    path = output_dir / "TalkGroups.CSV"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=TALKGROUP_COLUMNS, quoting=csv.QUOTE_ALL
        )
        writer.writeheader()
        for i, tg in enumerate(talkgroups, start=1):
            writer.writerow(
                {
                    "No.": str(i),
                    "Radio ID": str(tg.radio_id),
                    "Name": tg.name,
                    "Call Type": tg.call_type,
                    "Call Alert": tg.call_alert,
                }
            )
    logger.info("Wrote %d talkgroups to %s", len(talkgroups), path)
    return path
