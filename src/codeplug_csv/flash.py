"""Build and flash dmrconfig codeplug files from generated CSV outputs."""

from __future__ import annotations

import csv
import datetime as dt
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

DEFAULT_RADIO_MODEL = "Anytone AT-D878UV"


class RadioUserLookupError(ValueError):
    """Raised when a Radio ID cannot be found in the RadioID CSV database."""


@dataclass(frozen=True)
class RadioUser:
    """Minimal user profile from RadioID user.csv."""

    radio_id: int
    callsign: str
    first_name: str
    last_name: str
    city: str
    state: str
    country: str


def lookup_radio_user(users_csv: Path, radio_id: int) -> RadioUser:
    """Look up *radio_id* in *users_csv* and return the matching user row."""
    wanted = str(radio_id)

    with open(users_csv, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            if row.get("RADIO_ID", "").strip() != wanted:
                continue
            return RadioUser(
                radio_id=radio_id,
                callsign=row.get("CALLSIGN", "").strip(),
                first_name=row.get("FIRST_NAME", "").strip(),
                last_name=row.get("LAST_NAME", "").strip(),
                city=row.get("CITY", "").strip(),
                state=row.get("STATE", "").strip(),
                country=row.get("COUNTRY", "").strip(),
            )

    raise RadioUserLookupError(
        f"Radio ID {radio_id} was not found in {users_csv}. "
        "Regenerate output/user.csv or pass --users-csv with the correct file."
    )


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def _sanitize_name(value: str, *, max_len: int = 16, fallback: str = "UNNAMED") -> str:
    token = "_".join(value.strip().split())
    token = re.sub(r"[^A-Za-z0-9_-]", "_", token)
    token = re.sub(r"_+", "_", token).strip("_")
    if not token:
        token = fallback
    return token[:max_len]


def _normalize(value: str) -> str:
    return " ".join(value.split()).casefold()


def _format_freq(value: str) -> str:
    freq = float(value)
    return f"{freq:.5f}".rstrip("0").rstrip(".")


def _power_symbol(value: str) -> str:
    normalized = value.strip().casefold()
    if normalized in {"turbo", "high"}:
        return "+"
    return "-"


def _tone_value(value: str) -> str:
    tone = value.strip()
    if not tone or tone.casefold() == "off":
        return "-"
    return tone


def _channel_ro(value: str) -> str:
    return "+" if value.strip().casefold() == "on" else "-"


def _analog_width(value: str) -> str:
    return value.strip().rstrip("Kk") or "12.5"


def _compress_ranges(numbers: list[int]) -> str:
    if not numbers:
        return "-"

    unique_sorted = sorted(set(numbers))
    ranges: list[str] = []
    start = unique_sorted[0]
    end = unique_sorted[0]

    for num in unique_sorted[1:]:
        if num == end + 1:
            end = num
            continue

        if start == end:
            ranges.append(str(start))
        else:
            ranges.append(f"{start}-{end}")

        start = end = num

    if start == end:
        ranges.append(str(start))
    else:
        ranges.append(f"{start}-{end}")

    return ",".join(ranges)


def render_dmrconfig_config(
    *,
    radio_user: RadioUser,
    channel_rows: list[dict[str, str]],
    zone_rows: list[dict[str, str]],
    talkgroup_rows: list[dict[str, str]],
    radio_model: str = DEFAULT_RADIO_MODEL,
) -> str:
    """Render a dmrconfig .conf string from generated CSV rows."""
    if not channel_rows:
        raise ValueError("Channel.CSV has no channels")

    # Build contacts table and map by both original and sanitized names.
    contacts: list[tuple[int, str, str, str]] = []
    contact_index: dict[str, int] = {}
    for row in talkgroup_rows:
        idx = int(row.get("No.", "0") or 0)
        if idx <= 0:
            continue

        name_raw = row.get("Name", "")
        name = _sanitize_name(name_raw, fallback=f"TG{idx}")
        call_type = row.get("Call Type", "Group Call")
        dmr_type = "Private" if "private" in call_type.casefold() else "Group"
        dmr_id = row.get("Radio ID", "").strip()
        contacts.append((idx, name, dmr_type, dmr_id))

        contact_index[_normalize(name_raw)] = idx
        contact_index[_normalize(name)] = idx

    default_contact = contact_index.get(_normalize("Local"), 1)

    # Keep both exact and sanitized name maps for zone member lookup.
    channel_index: dict[str, int] = {}
    sanitized_channel_index: dict[str, int] = {}

    digital_lines: list[str] = []
    analog_lines: list[str] = []

    for row in channel_rows:
        number = int(row["No."])
        raw_name = row.get("Channel Name", "")
        name = _sanitize_name(raw_name, fallback=f"CH{number}")

        channel_index[raw_name.strip()] = number
        sanitized_channel_index[name] = number

        rx = _format_freq(row["Receive Frequency"])
        tx = _format_freq(row["Transmit Frequency"])
        power = _power_symbol(row.get("Transmit Power", "High"))
        ro = _channel_ro(row.get("TX Prohibit", "Off"))

        channel_type = row.get("Channel Type", "A-Analog")
        if channel_type.casefold().startswith("d-"):
            if contacts:
                tx_contact_name = row.get("Contact", "")
                tx_contact = str(
                    contact_index.get(_normalize(tx_contact_name), default_contact)
                )
                rx_group_list = "1"
            else:
                tx_contact = "-"
                rx_group_list = "-"
            color = row.get("Color Code", "1").strip() or "1"
            slot = row.get("Slot", "1").strip() or "1"
            digital_lines.append(
                " "
                f"{number:>4} {name:<16} {rx:<10} {tx:<10} {power} - 1 {ro} "
                f"Color {color} {slot} {rx_group_list} {tx_contact}"
            )
        else:
            rx_tone = _tone_value(row.get("CTCSS/DCS Decode", "Off"))
            tx_tone = _tone_value(row.get("CTCSS/DCS Encode", "Off"))
            admit = "Tone" if rx_tone != "-" or tx_tone != "-" else "-"
            width = _analog_width(row.get("Band Width", "12.5K"))
            analog_lines.append(
                " "
                f"{number:>4} {name:<16} {rx:<10} {tx:<10} {power} - 1 {ro} "
                f"{admit} Normal {rx_tone} {tx_tone} {width}"
            )

    zone_lines: list[str] = []
    for row in zone_rows:
        zone_no = int(row.get("No.", "0") or 0)
        if zone_no <= 0:
            continue

        raw_zone_name = row.get("Zone Name", "")
        zone_name = _sanitize_name(raw_zone_name, fallback=f"ZONE{zone_no}")

        members_raw = row.get("Zone Channel Member", "")
        members: list[int] = []
        for member_name in members_raw.split("|"):
            member_name = member_name.strip()
            if not member_name:
                continue

            channel_no = channel_index.get(member_name)
            if channel_no is None:
                channel_no = sanitized_channel_index.get(
                    _sanitize_name(member_name, fallback="UNKNOWN")
                )
            if channel_no is not None:
                members.append(channel_no)

        zone_lines.append(
            f" {zone_no:>4} {zone_name:<16} {_compress_ranges(members)}"
        )

    rendered: list[str] = []
    rendered.append("# Autogenerated by codeplug-csv")
    now_utc = dt.datetime.now(dt.UTC)
    rendered.append(f"# Generated UTC: {now_utc.strftime('%Y-%m-%d %H:%M:%S')}")
    rendered.append("")
    rendered.append(f"Radio: {radio_model}")
    rendered.append(f"ID: {radio_user.radio_id}")
    rendered.append(f"Name: {_sanitize_name(radio_user.callsign, fallback='NOCALL')}")
    rendered.append(f"Intro Line 1: {_sanitize_name(radio_user.callsign, fallback='NOCALL')}")
    rendered.append("Intro Line 2: codeplug_csv")
    rendered.append("")

    if contacts:
        rendered.append("# Talkgroups")
        rendered.append("Contact Name Type ID RxTone")
        for idx, name, dmr_type, dmr_id in contacts:
            rendered.append(f" {idx:>4} {name:<16} {dmr_type:<7} {dmr_id} -")
        rendered.append("")

        rendered.append("# Receive group list")
        rendered.append("Grouplist Name Contacts")
        contact_numbers = [idx for idx, *_ in contacts]
        rendered.append(f"    1 All_TGs {_compress_ranges(contact_numbers)}")
        rendered.append("")

    if analog_lines:
        rendered.append("# Analog channels")
        rendered.append(
            "Analog Name Receive Transmit Power Scan TOT RO Admit Squelch RxTone TxTone Width"
        )
        rendered.extend(analog_lines)
        rendered.append("")

    if digital_lines:
        rendered.append("# Digital channels")
        rendered.append(
            "Digital Name Receive Transmit Power Scan TOT RO Admit Color Slot RxGL TxContact"
        )
        rendered.extend(digital_lines)
        rendered.append("")

    rendered.append("# Zones")
    rendered.append("Zone Name Channels")
    rendered.extend(zone_lines)
    rendered.append("")

    return "\n".join(rendered)


def write_dmrconfig_config(
    *,
    radio_id: int,
    users_csv: Path,
    channel_csv: Path,
    zone_csv: Path,
    talkgroup_csv: Path,
    output_conf: Path,
    radio_model: str = DEFAULT_RADIO_MODEL,
) -> tuple[Path, RadioUser]:
    """Generate and write a dmrconfig file from exported CSVs."""
    radio_user = lookup_radio_user(users_csv, radio_id)
    channel_rows = _read_csv_rows(channel_csv)
    zone_rows = _read_csv_rows(zone_csv)
    talkgroup_rows = _read_csv_rows(talkgroup_csv)

    output_conf.parent.mkdir(parents=True, exist_ok=True)
    output_conf.write_text(
        render_dmrconfig_config(
            radio_user=radio_user,
            channel_rows=channel_rows,
            zone_rows=zone_rows,
            talkgroup_rows=talkgroup_rows,
            radio_model=radio_model,
        ),
        encoding="utf-8",
    )

    return output_conf, radio_user


def build_flash_command(
    config_path: Path,
    *,
    dmrconfig_bin: str = "dmrconfig",
    trace: bool = False,
    resolve_binary: bool = True,
) -> list[str]:
    """Build the command used to flash a radio with dmrconfig."""
    binary = dmrconfig_bin
    if resolve_binary:
        resolved = shutil.which(dmrconfig_bin)
        if not resolved:
            raise FileNotFoundError(
                f"Could not find '{dmrconfig_bin}' on PATH. Install dmrconfig first."
            )
        binary = resolved

    cmd = [binary, "-c"]
    if trace:
        cmd.append("-t")
    cmd.append(str(config_path))
    return cmd


def flash_with_dmrconfig(
    config_path: Path,
    *,
    dmrconfig_bin: str = "dmrconfig",
    trace: bool = False,
) -> list[str]:
    """Flash using dmrconfig and return the command that was executed."""
    cmd = build_flash_command(
        config_path,
        dmrconfig_bin=dmrconfig_bin,
        trace=trace,
        resolve_binary=True,
    )
    subprocess.run(cmd, check=True)
    return cmd
