# codeplug-csv

CLI tool that pulls UK amateur radio repeater data from the [RSGB ETCC API](https://api-beta.rsgb.online/) and generates CSV files importable by the Anytone CPS software.

Covers 2m and 70cm bands, both analog (FM) and digital (DMR) repeaters.

## Output files

- **Channel.CSV** - All channels with the full column set the Anytone CPS expects (analog + digital)
- **Zone.CSV** - Repeater channels grouped by UK region, band, mode, and type (e.g. "NE 2m FM", "LONDON 70cm DMR", "NE 2m AG"), plus static simplex/utility zones
- **TalkGroups.CSV** - UK-relevant DMR talkgroups fetched from the BrandMeister API
- **user.csv** - Full worldwide DMR contact list downloaded from [RadioID](https://www.radioid.net/) (importable as a Digital Contact List in the CPS)

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
codeplug-csv -o output/                    # All 2m + 70cm repeaters
codeplug-csv -b 70cm -o output/            # 70cm only
codeplug-csv -b 2m 70cm -o output/         # Explicit both bands
codeplug-csv --locator IO91 -o output/     # Filter by grid square prefix
codeplug-csv --power Mid -o output/        # Set transmit power (Turbo/High/Mid/Low)
codeplug-csv -v -o output/                 # Verbose logging
codeplug-csv -q -o output/                 # Quiet: warnings and errors only
codeplug-csv --no-contacts -o output/      # Skip the RadioID contact download
```

Or run as a module:

```bash
python -m codeplug_csv -o output/
```

### Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `CODEPLUG_CSV_API_BASE_URL` | `https://api-beta.rsgb.online` | RSGB ETCC API base URL |
| `CODEPLUG_CSV_BRANDMEISTER_URL` | `https://api.brandmeister.network/v2` | BrandMeister API base URL |
| `CODEPLUG_CSV_RADIOID_URL` | `https://www.radioid.net/static/user.csv` | RadioID contact list URL |
| `CODEPLUG_CSV_HTTP_TIMEOUT` | `30` | HTTP timeout in seconds for RSGB/BrandMeister |
| `CODEPLUG_CSV_RADIOID_TIMEOUT` | `60` | HTTP timeout in seconds for the contact download |
| `CODEPLUG_CSV_MAX_CONCURRENT` | `5` | Max concurrent RSGB band requests (minimum 1) |

## How it works

1. **Extract** - Fetches repeater data from `GET /band/2m` and `GET /band/70cm`
2. **Transform** - Filters to operational analog/DMR repeaters, removes exact duplicate API rows, swaps TX/RX frequencies to the radio's perspective, and generates unique channel names (max 16 chars). Names keep the API callsign suffix (e.g. `-L`, `-C`) and include the band, so the same callsign on 2m and 70cm stays distinct. DMR color codes are extracted from the API's `modeCodes` field.
3. **Zone** - Groups repeater channels by UK region + band + mode + type. Repeaters use `FM`/`DMR`; gateways use `AG`/`DG`. Zones above the 250-channel Anytone limit are split into numbered zones. Static simplex/utility zones are appended.
4. **Load** - Writes the CSV files. Channel numbers are derived from zone order so each zone's channels are contiguous, and every zone member resolves to exactly one channel name.

Repeaters with both analog and DMR modes produce three channels (one FM, two DMR — TS1 and TS2).

### DMR color codes

The RSGB API encodes DMR color codes in `modeCodes` as `M:N` (e.g. `["M:3"]` = color code 3). When only bare `"M"` is present, color code defaults to 1.

### Static zones

Eight additional zones are included with every codeplug:

| Zone | Channels | Notes |
|------|----------|-------|
| HOTSPOT | 4ch | DMR hotspot on 434.000/438.800 MHz, simplex + repeater modes |
| VHF FM SIMPLEX | V16–V45 (30ch) | 145.200–145.5625 MHz, V40 = calling channel |
| UHF FM SIMPLEX | U272–U286 (8ch) | 433.400–433.575 MHz at 25 kHz spacing, U280 = calling channel |
| VHF DV SIMPLEX | 2M DV CALL + 19 V-channels (20ch) | 144.6125 MHz calling + usable 2m FM/DV simplex channels, DMR CC1 TS1 |
| UHF DV SIMPLEX | DH1–DH8 (8ch) | 438.5875–438.6750 MHz, DH3 = calling channel |
| PMR446 | PMR 1–16 (16ch) | 446.00625–446.19375 MHz, TX prohibited |
| ISS | 7ch | Doppler-shifted downlinks + cross-band repeater |
| MARINE VHF | 22ch | Simplex-only channels, TX prohibited |

All DV simplex channels use CC1, TS1 and TG9 (Local). The 2m DV set excludes channels designated for internet gateways, slow Morse, FM calling, GB2RS and rally talk-in. V16 (145.200) is included but is shared with the ISS Earth-to-Space uplink.

### Zone labels

Dynamic zones are named `{region} {band} {mode}`. Repeater zones use `FM` or `DMR`; gateway zones use `AG` (analog gateway) or `DG` (digital gateway). Examples: `SW 2m FM`, `SCOT 70cm DMR`, `MIDL 2m AG`.

In `Zone.CSV`, `A Channel` defaults to the first member and `B Channel` to the second (or the first member for a single-channel zone).

| Region | Meaning |
|--------|---------|
| `SW` | South West England |
| `WAL` | Wales |
| `NW` | North West England |
| `MIDL` | Midlands |
| `NE` | North East England |
| `SE` | South East England |
| `E.ANG` | East Anglia |
| `SCOT` | Scotland |
| `N.IRE` | Northern Ireland |
| `CH.IS` | Channel Islands |
| `LONDON` | London |
| `OTHER` | Unmapped or invalid Maidenhead locator |

### BrandMeister talkgroups

Talkgroups are fetched from the [BrandMeister API](https://api.brandmeister.network/v2/talkgroup/) at runtime and filtered to a curated set of ~22 UK-relevant IDs (e.g. Local, UK Wide, Regional, TAC channels). Private call IDs (BM Parrot 9990, UK Parrot 234997) are not present in the API so they are added automatically as fallbacks. All DMR channels default to TG9 (Local).

### Frequency mapping

The API's `tx` field (what the repeater transmits) maps to the Anytone's `Receive Frequency` (what the radio listens to), and vice versa.

## CI

A GitHub Actions workflow builds the codeplug every Monday and on manual dispatch. The zipped CSV files are uploaded as a `codeplug` build artifact. Download the latest build from the [Releases](../../releases) page.

## Tests

```bash
task test
```

Live-data checks are opt-in because they hit the RSGB API:

```bash
CODEPLUG_CSV_LIVE_TESTS=1 .venv/bin/python -m pytest -m network
```

## License

MIT
