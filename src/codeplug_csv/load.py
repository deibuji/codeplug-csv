"""CSV writers for Anytone CPS import files."""

from __future__ import annotations

import csv
import logging
from collections.abc import Iterable
from pathlib import Path

from .config import (
    ANALOG_DEFAULTS,
    CHANNEL_COLUMNS,
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
    row["RX Color Code"] = str(ch.color_code)
    row["TxCc"] = str(ch.color_code)
    row["Slot"] = str(ch.slot)
    row["Contact"] = ch.contact
    row["Contact Call Type"] = ch.contact_call_type
    row["PTT Prohibit"] = ch.tx_prohibit

    return row


def _write_rows(
    path: Path, fieldnames: list[str], rows: Iterable[dict[str, str]]
) -> None:
    """Write rows to *path* with the CRLF line endings the Anytone CPS expects.

    ``newline=""`` is required by the csv module and prevents platform newline
    translation from turning the writer's ``\\r\\n`` into ``\\r\\r\\n`` on Windows.
    """
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)


def write_channels(channels: list[AnytoneChannel], output_dir: Path) -> Path:
    """Write Channel.CSV with all required columns."""
    path = output_dir / "Channel.CSV"
    rows = (_channel_row(i, ch) for i, ch in enumerate(channels, start=1))
    _write_rows(path, CHANNEL_COLUMNS, rows)
    logger.info("Wrote %d channels to %s", len(channels), path)
    return path


def write_zones(zones: list[AnytoneZone], output_dir: Path) -> Path:
    """Write Zone.CSV."""
    path = output_dir / "Zone.CSV"
    rows: list[dict[str, str]] = []
    for i, zone in enumerate(zones, start=1):
        members = "|".join(ch.name for ch in zone.channels)
        a_channel = zone.channels[0].name if zone.channels else ""
        b_channel = zone.channels[0].name if zone.channels else ""
        rows.append(
            {
                "No.": str(i),
                "Zone Name": zone.name,
                "Zone Channel Member": members,
                "A Channel": a_channel,
                "B Channel": b_channel,
            }
        )
    _write_rows(path, ZONE_COLUMNS, rows)
    logger.info("Wrote %d zones to %s", len(zones), path)
    return path


def write_talkgroups(talkgroups: list[TalkGroup], output_dir: Path) -> Path:
    """Write TalkGroups.CSV from a list of TalkGroup objects."""
    path = output_dir / "TalkGroups.CSV"
    rows: list[dict[str, str]] = []
    for i, tg in enumerate(talkgroups, start=1):
        rows.append(
            {
                "No.": str(i),
                "Radio ID": str(tg.radio_id),
                "Name": tg.name,
                "Call Type": tg.call_type,
                "Call Alert": tg.call_alert,
            }
        )
    _write_rows(path, TALKGROUP_COLUMNS, rows)
    logger.info("Wrote %d talkgroups to %s", len(talkgroups), path)
    return path
