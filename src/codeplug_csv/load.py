"""CSV writers for Anytone CPS import files."""

from __future__ import annotations

import aiofiles
import csv
import logging
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


def _rows_to_csv(fieldnames: list[str], rows: list[dict[str, str]]) -> str:
    """Render a list of row dicts to a CSV string."""
    import io

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return buf.getvalue()


async def write_channels(channels: list[AnytoneChannel], output_dir: Path) -> Path:
    """Write Channel.CSV with all required columns."""
    path = output_dir / "Channel.CSV"
    rows = [_channel_row(i, ch) for i, ch in enumerate(channels, start=1)]
    content = _rows_to_csv(CHANNEL_COLUMNS, rows)
    async with aiofiles.open(path, "w", encoding="utf-8") as f:
        await f.write(content)
    logger.info("Wrote %d channels to %s", len(channels), path)
    return path


async def write_zones(zones: list[AnytoneZone], output_dir: Path) -> Path:
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
    content = _rows_to_csv(ZONE_COLUMNS, rows)
    async with aiofiles.open(path, "w", encoding="utf-8") as f:
        await f.write(content)
    logger.info("Wrote %d zones to %s", len(zones), path)
    return path


async def write_talkgroups(talkgroups: list[TalkGroup], output_dir: Path) -> Path:
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
    content = _rows_to_csv(TALKGROUP_COLUMNS, rows)
    async with aiofiles.open(path, "w", encoding="utf-8") as f:
        await f.write(content)
    logger.info("Wrote %d talkgroups to %s", len(talkgroups), path)
    return path
