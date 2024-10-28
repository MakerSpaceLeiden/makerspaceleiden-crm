import re
from collections import namedtuple

STORAGES = {
    "L": {
        "description": "Left cabinet (near door)",
        "num_rows": 6,
        "num_cols": 6,
    },
    "R": {
        "description": "Right cabinet (near WC)",
        "num_rows": 6,
        "num_cols": 6,
    },
    "M": {
        "description": "Front room (with the 3D printers)",
        "num_rows": 26,
        "num_cols": 1,
    },
}

BoxLocation = namedtuple("BoxLocation", "storage col row")


def parse_box_location(text):
    location = None
    m = re.search(r"^([LR]{1})(\d{1})(\d{1})$", text.upper())
    if m:
        location = BoxLocation(m.group(1), int(m.group(2)), int(m.group(3)))
    else:
        m = re.search(r"^M(\d+)$", text.upper())
        location = BoxLocation("M", 1, int(m.group(1)))
    if location and location.storage in STORAGES:
        num_rows = STORAGES[location.storage]["num_rows"]
        num_cols = STORAGES[location.storage]["num_cols"]
        if 0 < location.row <= num_rows and 0 < location.col <= num_cols:
            return location
