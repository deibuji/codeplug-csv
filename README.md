# repeater-csv

CLI tool that pulls UK amateur radio repeater data from the [RSGB ETCC API](https://api-beta.rsgb.online/) and generates CSV files importable by the Anytone AT-D878UV CPS software.

Covers 2m and 70cm bands, both analog (FM) and digital (DMR) repeaters.

## Output files

- **Channel.CSV** - All channels with the full column set the AT-D878UV CPS expects (analog + digital)
- **Zone.CSV** - Channels grouped by band and mode (e.g. "2m FM", "70cm DMR")
- **TalkGroups.CSV** - Default UK DMR talkgroups (Local, UK Wide, Regional, BM Parrot)

## Install

```bash
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
```

## Usage

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
3. **Zone** - Groups channels by band + mode, splitting zones that exceed the 250-channel Anytone limit
4. **Load** - Writes the three CSV files

Repeaters with both analog and DMR modes produce two channels (one FM, one DMR).

### DMR color codes

The RSGB API encodes DMR color codes in `modeCodes` as `M:N` (e.g. `["M:3"]` = color code 3). When only bare `"M"` is present, color code defaults to 1.

### Frequency mapping

The API's `tx` field (what the repeater transmits) maps to the Anytone's `Receive Frequency` (what the radio listens to), and vice versa.

## Tests

```bash
pytest
```

## License

MIT
