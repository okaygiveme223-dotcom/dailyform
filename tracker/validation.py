import math
import re
from datetime import date

SUBJECTS = {"Biology 9700", "Chemistry 9701", "Physics 9702", "Pure Mathematics 1"}
METHODS = {"Active recall", "Past paper", "Corrections", "Notes"}


def integer(value, maximum):
    return type(value) is int and 0 < value <= maximum


def validate_records(records):
    if not isinstance(records, list) or len(records) > 10000:
        raise ValueError("Use a backup containing up to 10,000 entries.")
    cleaned = []
    seen = set()
    for row in records:
        if not isinstance(row, dict):
            raise ValueError("Invalid entry.")
        entry_id = row.get("id")
        if not isinstance(entry_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", entry_id) or entry_id in seen:
            raise ValueError("Entry IDs must be unique.")
        seen.add(entry_id)
        title = row.get("title")
        if not isinstance(title, str) or not 1 <= len(title.strip()) <= 120:
            raise ValueError("Enter a title of up to 120 characters.")
        day = row.get("date")
        if not isinstance(day, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day):
            raise ValueError("Invalid date.")
        date.fromisoformat(day)
        item = {"id": entry_id, "title": title.strip(), "date": day, "type": row.get("type")}
        if item["type"] == "Academic":
            if row.get("subject") not in SUBJECTS or row.get("method") not in METHODS or not integer(row.get("minutes"), 1440):
                raise ValueError("Check the subject, method and duration (1–1440 minutes).")
            item.update({key: row[key] for key in ("subject", "method", "minutes")})
        elif item["type"] == "Gym":
            weight = row.get("kg")
            if not integer(row.get("sets"), 100) or not integer(row.get("reps"), 1000) or type(weight) not in (int, float) or not math.isfinite(weight) or not 0 <= weight <= 2000:
                raise ValueError("Check sets (1–100), reps (1–1000) and weight (0–2000 kg).")
            item.update({key: row[key] for key in ("sets", "reps", "kg")})
        else:
            raise ValueError("Unknown entry type.")
        cleaned.append(item)
    return cleaned
