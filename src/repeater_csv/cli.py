"""CLI entry point for repeater-csv."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .config import BANDS
from .extract import RSGBClient
from .load import write_channels, write_talkgroups, write_zones
from .simplex import get_static_zones
from .transform import filter_repeaters, transform_repeaters
from .zones import assign_zones

logger = logging.getLogger("repeater_csv")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="repeater-csv",
        description="Generate Anytone AT-D878UV CSV files from RSGB repeater data",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Directory for generated CSV files (default: output/)",
    )
    parser.add_argument(
        "-b",
        "--bands",
        nargs="+",
        choices=list(BANDS),
        default=list(BANDS),
        help="Bands to include (default: all)",
    )
    parser.add_argument(
        "--locator",
        type=str,
        default=None,
        help="Filter by Maidenhead grid square prefix (e.g. IO91)",
    )
    parser.add_argument(
        "--power",
        type=str,
        choices=["Turbo", "High", "Mid", "Low"],
        default="High",
        help="Transmit power level (default: High)",
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

    args.output_dir.mkdir(parents=True, exist_ok=True)

    client = RSGBClient()
    try:
        repeaters = client.fetch_bands(args.bands)
    except Exception as e:
        logger.error("Failed to fetch repeater data: %s", e)
        sys.exit(1)

    filtered = filter_repeaters(repeaters, locator_prefix=args.locator)
    if not filtered:
        logger.warning("No repeaters matched the filters")
        print("No repeaters matched the filters.")
        sys.exit(0)

    channels = transform_repeaters(filtered, power=args.power)
    repeater_zones = assign_zones(channels)
    static_zones = get_static_zones()
    all_zones = repeater_zones + static_zones

    # Derive channel list from zone order so channel numbers align with zones
    all_channels = [ch for zone in all_zones for ch in zone.channels]

    write_channels(all_channels, args.output_dir)
    write_zones(all_zones, args.output_dir)
    write_talkgroups(args.output_dir)

    print(f"Generated {len(all_channels)} channels in {len(all_zones)} zones")
    print(f"Output: {args.output_dir.resolve()}")
