from datetime import datetime


def format_timestamp(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d_%H-%M-%S")
