from datetime import datetime

def format_datetime(value, format="%d/%m/%Y %H:%M"):
    if value is None:
        return ""
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return value
    return value.strftime(format)
import json

def from_json(value):
    if not value:
        return []
    try:
        return json.loads(value)
    except (ValueError, TypeError):
        return []
