"""Constants and defaults for Anytone CPS import files."""

API_BASE_URL = "https://api-beta.rsgb.online"
BANDS = ("2m", "70cm")

# Repeater types to exclude (beacons, TV, packet beacons, digi beacons)
EXCLUDED_TYPES = {"BN", "TV", "PB", "DB"}

# Gateway types (analog gateways, digital gateways)
GATEWAY_TYPES = {"AG", "DG"}

# Maximum channel name / zone name length for Anytone
MAX_NAME_LENGTH = 16

# Maximum channels per zone
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
    "RX Color Code",
    "Slot",
    "Scan List",
    "Receive Group List",
    "PTT Prohibit",
    "Reverse",
    "Idle TX",
    "Slot Suit",
    "AES Digital Encryption",
    "Digital Encryption",
    "Call Confirmation",
    "Talk Around(Simplex)",
    "Work Alone",
    "Custom CTCSS",
    "2TONE Decode",
    "Ranging",
    "Through Mode",
    "APRS RX",
    "Analog APRS PTT Mode",
    "Digital APRS PTT Mode",
    "APRS Report Type",
    "Digital APRS Report Channel",
    "Correct Frequency[Hz]",
    "SMS Confirmation",
    "Exclude channel from roaming",
    "DMR MODE",
    "DataACK Disable",
    "R5ToneBot",
    "R5ToneEot",
    "Auto Scan",
    "Ana Aprs Mute",
    "Send Talker Aias",
    "AnaAprsTxPath",
    "ARC4",
    "ex_emg_kind",
    "idle_tx",
    "Compand",
    "DisturEn",
    "DisturFreq",
    "Rpga_Mdc",
    "dmr_crc_ignore",
    "TxCc",
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
    "RX Color Code": "1",
    "Slot": "1",
    "Scan List": "None",
    "Receive Group List": "None",
    "PTT Prohibit": "Off",
    "Reverse": "Off",
    "Idle TX": "Off",
    "Slot Suit": "Off",
    "AES Digital Encryption": "Normal Encryption",
    "Digital Encryption": "Off",
    "Call Confirmation": "Off",
    "Talk Around(Simplex)": "Off",
    "Work Alone": "Off",
    "Custom CTCSS": "251.1",
    "2TONE Decode": "0",
    "Ranging": "Off",
    "Through Mode": "Off",
    "APRS RX": "Off",
    "Analog APRS PTT Mode": "Off",
    "Digital APRS PTT Mode": "Off",
    "APRS Report Type": "Off",
    "Digital APRS Report Channel": "1",
    "Correct Frequency[Hz]": "0",
    "SMS Confirmation": "Off",
    "Exclude channel from roaming": "0",
    "DMR MODE": "1",
    "DataACK Disable": "0",
    "R5ToneBot": "0",
    "R5ToneEot": "0",
    "Auto Scan": "0",
    "Ana Aprs Mute": "0",
    "Send Talker Aias": "0",
    "AnaAprsTxPath": "0",
    "ARC4": "0",
    "ex_emg_kind": "0",
    "idle_tx": "0",
    "Compand": "0",
    "DisturEn": "0",
    "DisturFreq": "0",
    "Rpga_Mdc": "0",
    "dmr_crc_ignore": "0",
    "TxCc": "1",
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

# ---------- BrandMeister API ----------

BRANDMEISTER_API_URL = "https://api.brandmeister.network/v2"

UK_TG_PREFIX = "235"

NON_UK_CURATED_IDS: set[int] = {
    8, 9, 91, 92, 93, 98,
    901, 902, 903,
    4000, 9990, 234997,
}

PRIVATE_CALL_IDS: set[int] = {4000, 9990, 234997}

# ---------- RadioID ----------

RADIOID_CSV_URL = "https://www.radioid.net/static/user.csv"

TALKGROUP_NAME_OVERRIDES: dict[int, str] = {
    9: "Local",  # Must match channel contact field
    9990: "BM Parrot",
    234997: "UK Parrot",
}
