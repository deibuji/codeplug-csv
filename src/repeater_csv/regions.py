"""Map Maidenhead locators to UK regions."""

from __future__ import annotations

# Primary lookup: 4-char grid square → region
_GRID_SQUARE_REGION: dict[str, str] = {
    # SW England
    "IO70": "SW",
    "IO80": "SW",
    "IO81": "SW",
    "IO90": "SW",
    # Wales
    "IO71": "WAL",
    "IO72": "WAL",
    "IO73": "WAL",
    # NW England
    "IO83": "NW",
    "IO84": "NW",
    # Midlands
    "IO82": "MIDL",
    "IO92": "MIDL",
    # NE England
    "IO93": "NE",
    "IO94": "NE",
    # SE England
    "IO91": "SE",
    "JO00": "SE",
    "JO01": "SE",
    # East Anglia
    "JO02": "E.ANG",
    "JO03": "E.ANG",
    # Scotland
    "IO67": "SCOT",
    "IO68": "SCOT",
    "IO69": "SCOT",
    "IO75": "SCOT",
    "IO76": "SCOT",
    "IO77": "SCOT",
    "IO78": "SCOT",
    "IO79": "SCOT",
    "IO85": "SCOT",
    "IO86": "SCOT",
    "IO87": "SCOT",
    "IO88": "SCOT",
    "IO95": "SCOT",
    "IO96": "SCOT",
    "IO97": "SCOT",
    "IP90": "SCOT",
    # Northern Ireland
    "IO54": "N.IRE",
    "IO64": "N.IRE",
    "IO65": "N.IRE",
    "IO74": "N.IRE",
    # Channel Islands
    "IN79": "CH.IS",
    "IN89": "CH.IS",
}

# Subsquare-column overrides for boundary grid squares.
# Each entry: grid_square → (column_range_start, column_range_end, override_region)
# Columns are A-X (0-23). Range is inclusive.
_SUBSQUARE_OVERRIDES: dict[str, tuple[str, str, str]] = {
    "IO81": ("A", "L", "WAL"),       # Cardiff, Merthyr etc → WAL (default SW)
    "IO83": ("A", "J", "WAL"),       # Wrexham, Mold → WAL (default NW)
    "IO91": ("T", "X", "LONDON"),    # London area (default SE)
    "IO74": ("G", "X", "NW"),        # Isle of Man → NW (default N.IRE)
}

_DEFAULT_REGION = "SE"


def locator_to_region(locator: str) -> str:
    """Return the UK region for a Maidenhead locator string.

    Uses the first 4 characters as the grid square, with optional
    subsquare-column refinement when a 5th+ character is present.

    Falls back to 'SE' for unrecognised locators.
    """
    if not locator or len(locator) < 4:
        return _DEFAULT_REGION

    grid = locator[:4].upper()
    base = _GRID_SQUARE_REGION.get(grid)

    if base is None:
        return _DEFAULT_REGION

    # Check subsquare override if we have at least a 5th character
    if len(locator) >= 5 and grid in _SUBSQUARE_OVERRIDES:
        col = locator[4].upper()
        lo, hi, override = _SUBSQUARE_OVERRIDES[grid]
        if lo <= col <= hi:
            return override

    return base
