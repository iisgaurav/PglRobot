import time
from datetime import datetime

def extract_time(time_val: str) -> datetime | None:
    if any(time_val.endswith(unit) for unit in ('m', 'h', 'd')):
        unit = time_val[-1]
        time_num = time_val[:-1]
        if not time_num.isdigit():
            return None

        if unit == 'm':
            bantime = int(time.time()) + int(time_num) * 60
        elif unit == 'h':
            bantime = int(time.time()) + int(time_num) * 60 * 60
        elif unit == 'd':
            bantime = int(time.time()) + int(time_num) * 24 * 60 * 60
        else:
            return None
        return datetime.fromtimestamp(bantime)
    else:
        return None
