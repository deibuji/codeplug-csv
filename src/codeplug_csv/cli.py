"""CLI entry point for codeplug-csv."""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from .config import BANDS
from .extract import BrandMeisterClient, RadioIDClient, RSGBClient
from .load import write_channels, write_talkgroups, write_zones
from .simplex import get_static_zones
from .transform import filter_repeaters, transform_repeaters
from .zones import assign_zones

logger = logging.getLogger("codeplug_csv")


def _configure_logging(verbose: bool, quiet: bool) -> None:
    if verbose:
        level = logging.DEBUG
    elif quiet:
        level = logging.WARNING
    else:
        level = logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="codeplug-csv",
        description="Generate Anytone CSV files from RSGB repeater data",
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
        "--no-contacts",
        action="store_true",
        help="Skip downloading the RadioID digital contact list",
    )
    verbosity = parser.add_mutually_exclusive_group()
    verbosity.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose (DEBUG) logging",
    )
    verbosity.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress all output except warnings and errors",
    )
    return parser.parse_args(argv)


async def _run(args: argparse.Namespace) -> None:
    args.output_dir.mkdir(parents=True, exist_ok=True)

    try:
        async with RSGBClient() as client:
            repeaters = await client.fetch_bands(args.bands)
    except Exception:
        logger.exception("Failed to fetch repeater data")
        sys.exit(1)

    try:
        async with BrandMeisterClient() as client:
            talkgroups = await client.fetch_talkgroups()
    except Exception:
        logger.exception("Failed to fetch talkgroup data")
        sys.exit(1)

    filtered = filter_repeaters(repeaters, locator_prefix=args.locator)
    if not filtered:
        logger.warning(
            "No repeaters matched filters (bands=%s, locator=%s)",
            args.bands,
            args.locator,
        )
        print("No repeaters matched the filters.")
        sys.exit(0)

    channels = transform_repeaters(filtered, power=args.power)
    repeater_zones = assign_zones(channels)
    static_zones = get_static_zones()
    all_zones = static_zones + repeater_zones

    # Derive channel list from zone order so channel numbers align with zones
    all_channels = [ch for zone in all_zones for ch in zone.channels]

    write_channels(all_channels, args.output_dir)
    write_zones(all_zones, args.output_dir)
    write_talkgroups(talkgroups, args.output_dir)

    if not args.no_contacts:
        try:
            async with RadioIDClient() as radioid:
                await radioid.download(args.output_dir / "user.csv")
        except Exception:
            logger.warning("Failed to download RadioID contacts", exc_info=True)
            print(
                "Warning: RadioID contact list download failed (continuing without it)"
            )

    print(f"Generated {len(all_channels)} channels in {len(all_zones)} zones")
    print(f"Output: {args.output_dir.resolve()}")
    logger.info(
        "Generated %d channels in %d zones (output=%s)",
        len(all_channels),
        len(all_zones),
        args.output_dir.resolve(),
    )


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    _configure_logging(args.verbose, args.quiet)
    asyncio.run(_run(args))
