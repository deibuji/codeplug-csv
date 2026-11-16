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
from .models import Repeater, TalkGroup
from .qdmr import PLACEHOLDER_CALLSIGN, PLACEHOLDER_DMR_ID, write_qdmr
from .simplex import get_static_zones
from .transform import filter_repeaters, transform_repeaters
from .zones import assign_zones

# Largest DMR ID allowed by the radio (24 bit).
MAX_DMR_ID = 16_777_215


def _dmr_id(value: str) -> int:
    """argparse type for --dmr-id."""
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid DMR ID: {value!r}") from None
    if not 0 <= number <= MAX_DMR_ID:
        raise argparse.ArgumentTypeError(
            f"DMR ID must be between 0 and {MAX_DMR_ID}"
        )
    return number

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
        description="Generate Anytone CSV and qDMR YAML files from RSGB repeater data",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Directory for generated codeplug files (default: output/)",
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
    parser.add_argument(
        "--format",
        choices=["all", "anytone", "qdmr"],
        default="all",
        help=(
            "Output format: Anytone CSVs, qDMR/dmrconf YAML, or all "
            "(default: all)"
        ),
    )
    parser.add_argument(
        "--dmr-id",
        type=_dmr_id,
        default=PLACEHOLDER_DMR_ID,
        help=(
            "Your DMR ID for the qDMR codeplug; a placeholder is emitted "
            f"when omitted (default: {PLACEHOLDER_DMR_ID})"
        ),
    )
    parser.add_argument(
        "--callsign",
        type=str,
        default=PLACEHOLDER_CALLSIGN,
        help=(
            "Your callsign for the qDMR codeplug "
            f"(default: {PLACEHOLDER_CALLSIGN})"
        ),
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


async def _fetch_repeaters(bands: list[str]) -> list[Repeater]:
    async with RSGBClient() as client:
        return await client.fetch_bands(bands)


async def _fetch_talkgroups() -> list[TalkGroup]:
    async with BrandMeisterClient() as client:
        return await client.fetch_talkgroups()


async def _download_contacts(dest: Path) -> None:
    async with RadioIDClient() as radioid:
        await radioid.download(dest)


async def _cancel_tasks(*tasks: asyncio.Task | None) -> None:
    """Cancel still-running tasks, then await every task to settle cleanly.

    Awaiting already-finished tasks too consumes any exception they raised, so
    asyncio never reports "Task exception was never retrieved" at shutdown.
    """
    for task in tasks:
        if task is not None and not task.done():
            task.cancel()
    active = [task for task in tasks if task is not None]
    if active:
        await asyncio.gather(*active, return_exceptions=True)


async def _run(args: argparse.Namespace) -> None:
    args.output_dir.mkdir(parents=True, exist_ok=True)

    contacts_task = (
        None
        if args.no_contacts
        else asyncio.create_task(_download_contacts(args.output_dir / "user.csv"))
    )
    fetch_tasks = [
        asyncio.create_task(_fetch_repeaters(args.bands)),
        asyncio.create_task(_fetch_talkgroups()),
    ]

    repeaters_result, talkgroups_result = await asyncio.gather(
        *fetch_tasks, return_exceptions=True
    )

    if isinstance(repeaters_result, Exception):
        logger.error("Failed to fetch repeater data: %s", repeaters_result)
        await _cancel_tasks(*fetch_tasks, contacts_task)
        sys.exit(1)
    if isinstance(talkgroups_result, Exception):
        logger.error("Failed to fetch talkgroup data: %s", talkgroups_result)
        await _cancel_tasks(*fetch_tasks, contacts_task)
        sys.exit(1)

    filtered = filter_repeaters(repeaters_result, locator_prefix=args.locator)
    if not filtered:
        logger.warning(
            "No repeaters matched filters (bands=%s, locator=%s)",
            args.bands,
            args.locator,
        )
        await _cancel_tasks(contacts_task)
        if not args.quiet:
            print("No repeaters matched the filters.")
        sys.exit(0)

    if contacts_task is not None:
        try:
            await contacts_task
        except Exception as exc:
            logger.warning("Failed to download RadioID contacts: %s", exc)

    channels = transform_repeaters(filtered, power=args.power)
    repeater_zones = assign_zones(channels)
    static_zones = get_static_zones()
    all_zones = static_zones + repeater_zones

    # Derive channel list from zone order so channel numbers align with zones
    all_channels = [ch for zone in all_zones for ch in zone.channels]

    if args.format in ("all", "anytone"):
        write_channels(all_channels, args.output_dir)
        write_zones(all_zones, args.output_dir)
        write_talkgroups(talkgroups_result, args.output_dir)

    if args.format in ("all", "qdmr"):
        write_qdmr(
            all_channels,
            all_zones,
            talkgroups_result,
            args.output_dir,
            dmr_id=args.dmr_id,
            callsign=args.callsign,
        )

    if not args.quiet:
        print(f"Generated {len(all_channels)} channels in {len(all_zones)} zones")
        print(f"Output: {args.output_dir.resolve()}")


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    _configure_logging(args.verbose, args.quiet)
    asyncio.run(_run(args))
