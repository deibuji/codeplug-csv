"""CLI for generating and optionally flashing dmrconfig codeplug files."""

from __future__ import annotations

import argparse
import logging
import shlex
import subprocess
import sys
from pathlib import Path

from .flash import (
    DEFAULT_RADIO_MODEL,
    RadioUserLookupError,
    build_flash_command,
    write_dmrconfig_config,
)

logger = logging.getLogger("codeplug_csv.flash")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="codeplug-csv-flash",
        description=(
            "Build a dmrconfig codeplug from generated CSV files and "
            "optionally flash it to the radio"
        ),
    )
    parser.add_argument(
        "--radio-id",
        type=int,
        required=True,
        help="DMR Radio ID to apply (looked up in users.csv)",
    )
    parser.add_argument(
        "--users-csv",
        type=Path,
        default=Path("output/user.csv"),
        help="Path to RadioID users CSV (default: output/user.csv)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Directory containing Channel.CSV, Zone.CSV, TalkGroups.CSV",
    )
    parser.add_argument(
        "--output-conf",
        type=Path,
        default=None,
        help="Where to write the dmrconfig .conf file (default: output/codeplug-<id>.conf)",
    )
    parser.add_argument(
        "--radio-model",
        type=str,
        default=DEFAULT_RADIO_MODEL,
        help=f"dmrconfig radio model (default: {DEFAULT_RADIO_MODEL})",
    )
    parser.add_argument(
        "--dmrconfig-bin",
        type=str,
        default="dmrconfig",
        help="Executable used for flashing (default: dmrconfig)",
    )
    parser.add_argument(
        "--trace",
        action="store_true",
        help="Pass -t to dmrconfig for serial trace logging",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write to radio now. Without this flag, only generate .conf and print command.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(levelname)s: %(message)s",
    )

    output_dir = args.output_dir
    output_conf = args.output_conf or (output_dir / f"codeplug-{args.radio_id}.conf")

    channel_csv = output_dir / "Channel.CSV"
    zone_csv = output_dir / "Zone.CSV"
    talkgroup_csv = output_dir / "TalkGroups.CSV"

    required_files = [channel_csv, zone_csv, talkgroup_csv, args.users_csv]
    missing = [path for path in required_files if not path.exists()]
    if missing:
        print("Missing required files:")
        for path in missing:
            print(f"  - {path}")
        print("Run 'task run' first to generate CSV outputs.")
        sys.exit(1)

    try:
        conf_path, user = write_dmrconfig_config(
            radio_id=args.radio_id,
            users_csv=args.users_csv,
            channel_csv=channel_csv,
            zone_csv=zone_csv,
            talkgroup_csv=talkgroup_csv,
            output_conf=output_conf,
            radio_model=args.radio_model,
        )
    except RadioUserLookupError as exc:
        print(exc)
        sys.exit(1)
    except Exception as exc:
        logger.exception("Failed to build dmrconfig config")
        print(f"Failed to build dmrconfig config: {exc}")
        sys.exit(1)

    print(
        "Matched Radio ID "
        f"{user.radio_id} -> {user.callsign} {user.first_name} {user.last_name}".strip()
    )
    print(f"Generated dmrconfig file: {conf_path.resolve()}")

    preview_cmd = build_flash_command(
        conf_path,
        dmrconfig_bin=args.dmrconfig_bin,
        trace=args.trace,
        resolve_binary=False,
    )
    print(f"Flash command: {shlex.join(preview_cmd)}")

    if not args.write:
        print("Dry run complete. Re-run with --write to flash the radio.")
        return

    try:
        run_cmd = build_flash_command(
            conf_path,
            dmrconfig_bin=args.dmrconfig_bin,
            trace=args.trace,
            resolve_binary=True,
        )
        subprocess.run(run_cmd, check=True)
    except FileNotFoundError as exc:
        print(exc)
        sys.exit(1)
    except subprocess.CalledProcessError as exc:
        print(f"dmrconfig failed with exit code {exc.returncode}")
        sys.exit(exc.returncode)

    print("Flashing completed successfully.")


if __name__ == "__main__":
    main()
