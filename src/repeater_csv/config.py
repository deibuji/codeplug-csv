"""Constants and defaults for Anytone AT-D878UV CPS import files."""

API_BASE_URL = "https://api-beta.rsgb.online"
BANDS = ("2m", "70cm")

# Repeater types to exclude (beacons, TV, packet beacons, digi beacons)
EXCLUDED_TYPES = {"BN", "TV", "PB", "DB"}

# Gateway types (analog gateways, digital gateways)
GATEWAY_TYPES = {"AG", "DG"}

# Maximum channel name / zone name length for Anytone
MAX_NAME_LENGTH = 16

# Maximum channels per zone on the AT-D878UV
MAX_ZONE_CHANNELS = 250

# ---------- Anytone Channel.CSV column definitions ----------

CHANNEL_COLUMNS = [
    "No.",
    "Channel Name",
    "Receive Frequency",
    "Transmit Frequency",
    "Channel Type",
    "Transmit Power",
    "Band Width",
    "CTCSS/DCS Decode",
    "CTCSS/DCS Encode",
    "Contact",
    "Contact Call Type",
    "Radio ID",
    "Busy Lock/TX Permit",
    "Squelch Mode",
    "Optional Signal",
    "DTMF ID",
    "2Tone ID",
    "5Tone ID",
    "PTT ID",
    "Color Code",
    "Slot",
    "Scan List",
    "Receive Group List",
    "TX Prohibit",
    "Reverse",
    "Simplex TDMA",
    "TDMA Adaptive",
    "Encryption Type",
    "Digital Encryption",
    "Call Confirmation",
    "Talk Around",
    "Work Alone",
    "Custom CTCSS",
    "2TONE Decode",
    "Ranging",
    "Through Mode",
    "Digi APRS RX",
    "Analog APRS PTT Mode",
    "Digital APRS PTT Mode",
    "APRS Report Type",
    "Digital APRS Report Channel",
    "Correct Frequency[Hz]",
    "SMS Confirmation",
    "Exclude channel from roaming",
]

# Defaults for columns we don't map from the API
ANALOG_DEFAULTS = {
    "Channel Type": "A-Analog",
    "Transmit Power": "High",
    "Band Width": "12.5K",
    "CTCSS/DCS Decode": "Off",
    "CTCSS/DCS Encode": "Off",
    "Contact": "",
    "Contact Call Type": "Group Call",
    "Radio ID": "",
    "Busy Lock/TX Permit": "Off",
    "Squelch Mode": "Carrier",
    "Optional Signal": "Off",
    "DTMF ID": "1",
    "2Tone ID": "1",
    "5Tone ID": "1",
    "PTT ID": "Off",
    "Color Code": "1",
    "Slot": "1",
    "Scan List": "None",
    "Receive Group List": "None",
    "TX Prohibit": "Off",
    "Reverse": "Off",
    "Simplex TDMA": "Off",
    "TDMA Adaptive": "Off",
    "Encryption Type": "Normal Encryption",
    "Digital Encryption": "Off",
    "Call Confirmation": "Off",
    "Talk Around": "Off",
    "Work Alone": "Off",
    "Custom CTCSS": "251.1",
    "2TONE Decode": "0",
    "Ranging": "Off",
    "Through Mode": "Off",
    "Digi APRS RX": "Off",
    "Analog APRS PTT Mode": "Off",
    "Digital APRS PTT Mode": "Off",
    "APRS Report Type": "Off",
    "Digital APRS Report Channel": "1",
    "Correct Frequency[Hz]": "0",
    "SMS Confirmation": "Off",
    "Exclude channel from roaming": "0",
}

DIGITAL_DEFAULTS = {
    **ANALOG_DEFAULTS,
    "Channel Type": "D-Digital",
    "Band Width": "12.5K",
    "Busy Lock/TX Permit": "Always",
    "Squelch Mode": "Carrier",
    "Contact": "Local",
    "Contact Call Type": "Group Call",
}

# ---------- Zone.CSV column definitions ----------

ZONE_COLUMNS = [
    "No.",
    "Zone Name",
    "Zone Channel Member",
    "A Channel",
    "B Channel",
]

# ---------- TalkGroups.CSV column definitions ----------

TALKGROUP_COLUMNS = [
    "No.",
    "Radio ID",
    "Name",
    "Call Type",
    "Call Alert",
]

# Default UK DMR talkgroups
DEFAULT_TALKGROUPS = [
    {"name": "Local", "id": 9, "call_type": "Group Call", "alert": "None"},
    {"name": "UK Wide", "id": 235, "call_type": "Group Call", "alert": "None"},
    {"name": "Regional", "id": 8, "call_type": "Group Call", "alert": "None"},
    {"name": "BM Parrot", "id": 9990, "call_type": "Private Call", "alert": "None"},
]
