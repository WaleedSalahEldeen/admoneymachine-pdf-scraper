import json
import re
import unicodedata
from html import unescape
from pathlib import Path

WINDOWS_RESERVED = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    "COM1",
    "COM2",
    "COM3",
    "COM4",
    "COM5",
    "COM6",
    "COM7",
    "COM8",
    "COM9",
    "LPT1",
    "LPT2",
    "LPT3",
    "LPT4",
    "LPT5",
    "LPT6",
    "LPT7",
    "LPT8",
    "LPT9",
}

INVALID_CHARS = re.compile(r'[\\/:*?"<>|]+')
WHITESPACE = re.compile(r"\s+")


def safe_filename(value, default="item", max_length=120):
    if value is None:
        value = ""
    value = unescape(str(value))
    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", "ignore").decode("ascii")
    value = INVALID_CHARS.sub("-", value)
    value = WHITESPACE.sub(" ", value).strip(" .")
    if not value:
        value = default
    if value.upper() in WINDOWS_RESERVED:
        value = "_" + value
    if len(value) > max_length:
        value = value[:max_length].rstrip(" .-")
    if not value:
        value = default
    return value


def ensure_dir(path):
    Path(path).mkdir(parents=True, exist_ok=True)


def write_json(path, data):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=True)
