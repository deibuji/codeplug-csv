# repeater-csv

CLI tool that pulls UK amateur radio repeater data from the [RSGB ETCC API](https://api-beta.rsgb.online/) and generates CSV files importable by the Anytone AT-D878UV CPS software.

Covers 2m and 70cm bands, both analog (FM) and digital (DMR) repeaters.

## Output files

- **Channel.CSV** - All channels with the full column set the AT-D878UV CPS expects (analog + digital)
- **Zone.CSV** - Repeater channels grouped by UK region, band, and mode (e.g. "NE 2m FM", "LONDON 70cm DMR"), plus static simplex/utility zones
- **TalkGroups.CSV** - UK-relevant DMR talkgroups fetched from the BrandMeister API

## Install

```bash
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
```

## Usage

The project includes a [Taskfile](https://taskfile.dev/) for common commands:

```bash
task test                        # Run the test suite
task run                         # Generate CSVs in output/
task run -- --locator IO91       # Pass extra CLI args
task                             # Run tests then generate output
```

Or call the CLI directly:

```bash
repeater-csv -o output/                    # All 2m + 70cm repeaters
repeater-csv -b 70cm -o output/            # 70cm only
repeater-csv -b 2m 70cm -o output/         # Explicit both bands
repeater-csv --locator IO91 -o output/     # Filter by grid square prefix
repeater-csv --power Mid -o output/        # Set transmit power (Turbo/High/Mid/Low)
repeater-csv -v -o output/                 # Verbose logging
```

Or run as a module:

```bash
python -m repeater_csv -o output/
```

## How it works

1. **Extract** - Fetches repeater data from `GET /band/2m` and `GET /band/70cm`
2. **Transform** - Filters to operational analog/DMR repeaters, swaps TX/RX frequencies to the radio's perspective, generates channel names (max 16 chars), extracts DMR color codes from the API's `modeCodes` field
3. **Zone** - Groups repeater channels by UK region + band + mode, splitting zones that exceed the 250-channel Anytone limit. Appends static simplex/utility zones.
4. **Load** - Writes the three CSV files. Channel numbers are derived from zone order so each zone's channels are contiguous.

Repeaters with both analog and DMR modes produce three channels (one FM, two DMR — TS1 and TS2).

### DMR color codes

The RSGB API encodes DMR color codes in `modeCodes` as `M:N` (e.g. `["M:3"]` = color code 3). When only bare `"M"` is present, color code defaults to 1.

### Static zones

Eight additional zones are included with every codeplug:

| Zone | Channels | Notes |
|------|----------|-------|
| HOTSPOT | 4ch | DMR hotspot on 434.000/438.800 MHz, simplex + repeater modes |
| VHF FM SIMPLEX | V16–V46 (31ch) | 145.200–145.575 MHz, V40 = calling channel |
| UHF FM SIMPLEX | U272–U288 (17ch) | 433.400–433.600 MHz, U280 = calling channel |
| VHF DV SIMPLEX | 2M DV CALL (1ch) | 144.6125 MHz, DMR CC1 TS1 |
| UHF DV SIMPLEX | DH1–DH8 (8ch) | 438.5875–438.6750 MHz, DH3 = calling channel |
| PMR446 | PMR 1–16 (16ch) | 446.00625–446.19375 MHz, TX prohibited |
| ISS | 7ch | Doppler-shifted downlinks + cross-band repeater |
| MARINE VHF | 22ch | Simplex-only channels, TX prohibited |

### BrandMeister talkgroups

Talkgroups are fetched from the [BrandMeister API](https://api.brandmeister.network/v2/talkgroup/) at runtime and filtered to a curated set of ~22 UK-relevant IDs (e.g. Local, UK Wide, Regional, TAC channels). Private call IDs (BM Parrot 9990, UK Parrot 234997) are not present in the API so they are added automatically as fallbacks. All DMR channels default to TG9 (Local).

### Frequency mapping

The API's `tx` field (what the repeater transmits) maps to the Anytone's `Receive Frequency` (what the radio listens to), and vice versa.

## Tests

```bash
task test
```

## License

MIT
