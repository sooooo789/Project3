CABLE_TABLE = {
    "35sq": 170,
    "50sq": 220,
    "70sq": 280,
    "95sq": 340,
    "120sq": 400
}

def select_cable(load_current):
    for cable, allowable in CABLE_TABLE.items():
        if allowable >= load_current:
            return cable, allowable
    return None, None
