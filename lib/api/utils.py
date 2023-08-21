import sqlite3
from datetime import date as date_, timedelta

SETUP_SQL = """
CREATE TABLE IF NOT EXISTS group_schedule (
    group_id INTEGER,
    date TEXT,
    language TEXT,
    lessons TEXT,
    updated TEXT,
    PRIMARY KEY (group_id, date, language)
);
CREATE INDEX IF NOT EXISTS group_schedule_date_idx ON group_schedule (date);
CREATE INDEX IF NOT EXISTS group_schedule_group_id_idx ON group_schedule (group_id);
CREATE INDEX IF NOT EXISTS group_schedule_language_idx ON group_schedule (language);
"""


def setup_db(connection: sqlite3.Connection):
    """Setup database"""
    cur = connection.cursor()
    cur.executescript(SETUP_SQL)
    connection.commit()
    cur.close()


def get_date_range(date: date_, range: int = 14) -> tuple[date_, date_]:
    """Get date range

    For example, we have date 2023-08-21 and range of 10 days.
    Let's convert it to day of year: 233.
    Then we will have 230 and 239 (240 not included) days of year of range.
    So, we will have date range from 2023-08-18 to 2023-08-28.
    """

    # Free built-in function
    _range = range
    del range

    day_of_year = get_day_of_year(date)

    # Count dates range
    from_day = day_of_year - day_of_year % _range
    to_day = from_day + _range - 1

    # Count years difference
    years_diff = to_day // 365
    to_day = to_day % 365

    from_date = get_date_from_day_of_year(date.year, from_day)
    to_date = get_date_from_day_of_year(date.year + years_diff, to_day)

    return from_date, to_date


def get_day_of_year(date: date_) -> int:
    return date.timetuple().tm_yday


def get_date_from_day_of_year(year: int, day_of_year: int) -> date_:
    return date_(year, 1, 1) + timedelta(days=day_of_year - 1)
