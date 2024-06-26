import sqlite3
import time
from contextlib import closing
from datetime import datetime
from typing import Optional, Tuple

import pytz
import requests
import schedule
from retrying import retry

from config import settings
from status import get_device_status

DB_FILE = settings.DB_FILE
BOT_TOKEN = settings.BOT_TOKEN
CHANNEL_ID = settings.CHANNEL_ID


def create_db() -> None:
    """
    Creates a SQLite database with a table named 'status' if it does not already exist.

    The 'status' table has two columns:
    - timestamp (INTEGER): The timestamp of the status entry.
    - status (TEXT): The status text.

    The function connects to the database file specified by `DB_FILE`, executes the
    SQL command to create the table if it does not already exist, commits the changes,
    and then closes the connection.
    """
    with sqlite3.connect(DB_FILE) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute(
                """CREATE TABLE IF NOT EXISTS status
                   (timestamp INTEGER, status TEXT)"""
            )
            conn.commit()

    print("DB initialized")


def get_last_status() -> Optional[Tuple[int, bool]]:
    """
    Retrieves the most recent status entry from the 'status' table in the SQLite database.

    Returns:
        A tuple containing the timestamp (int) and status (bool) of the most recent entry,
        or None if the table is empty.

    The function connects to the database file specified by `DB_FILE`, executes a SQL query
    to fetch the most recent status entry, and then closes the connection.
    """
    with sqlite3.connect(DB_FILE) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute(
                "SELECT timestamp, status FROM status ORDER BY timestamp DESC LIMIT 1"
            )
            row = cursor.fetchone()
    if row:
        return row[0], bool(int(row[1]))
    return None


def insert_status(timestamp: int, status: bool) -> None:
    """
    Inserts a new status entry into the 'status' table in the SQLite database.

    Args:
        timestamp (int): The timestamp of the status entry.
        status (bool): The status value.

    The function connects to the database file specified by `DB_FILE`, executes an SQL
    command to insert the new status entry, commits the changes, and then closes the connection.
    """
    with sqlite3.connect(DB_FILE) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute(
                "INSERT INTO status (timestamp, status) VALUES (?, ?)",
                (timestamp, int(status)),
            )
            conn.commit()


def post_to_channel(message: str, disable_notification: bool = False):
    """
    Sends a message to a specified Telegram channel using the Telegram Bot API.

    Args:
        message (str): The message text to send to the Telegram channel.
        disable_notification (bool): if True send in silent

    The function constructs the URL for the Telegram Bot API's `sendMessage` endpoint,
    sets the necessary parameters including the chat ID and message text, and sends
    a POST request to the API.
    """
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    params = {"chat_id": CHANNEL_ID, "text": message}
    if disable_notification:
        params["disable_notification"] = True
    requests.post(url, params=params)


def format_time(hours: int, minutes: int) -> str:
    if hours == 0 and minutes == 0:
        return "менше хвилини"

    days = hours // 24
    hours = hours % 24

    time_str = ""
    if days > 0:
        if days == 1:
            time_str += "1 день "
        elif days >= 2 and days <= 4:
            time_str += f"{days} дні "
        else:
            time_str += f"{days} днів "

    if hours > 0:
        if hours == 1:
            time_str += "1 годин "
        elif hours >= 2 and hours <= 4:
            time_str += f"{hours} години "
        else:
            time_str += f"{hours} годин "

    if minutes > 0:
        if minutes == 1:
            time_str += "1 хвилину"
        elif minutes >= 2 and minutes <= 4:
            time_str += f"{minutes} хвилини"
        else:
            time_str += f"{minutes} хвилин"

    return time_str


def check_status() -> None:
    print("Check status...")
    current_status = get_device_status()
    status_from_db = get_last_status()
    if isinstance(status_from_db, tuple):
        last_status_in_db_timestamp, last_status_in_db = status_from_db
    else:
        last_status_in_db = status_from_db
        last_status_in_db_timestamp = int(time.time())

    # DB is empty
    if last_status_in_db is None:
        insert_status(int(time.time()), current_status)

    # If current status is different from the last status in the database
    # then insert the current status into the database and post a message to the channel
    if current_status != last_status_in_db:
        insert_status(int(time.time()), current_status)
        # calculate time difference between the current time and the last status change
        time_diff = int(time.mktime(time.localtime())) - int(
            last_status_in_db_timestamp
        )
        hours, remainder = divmod(time_diff, 3600)
        minutes, _ = divmod(remainder, 60)

        # Get the current time in Kyiv timezone
        kyiv_tz = pytz.timezone("Europe/Kyiv")
        current_time = datetime.now(kyiv_tz).time()

        # Check if the current time is between 23:00 and 9:00 AM
        disable_notification = current_time.hour >= 23 or current_time.hour < 9

        # Є світло, коли не було
        if (current_status is True) and (last_status_in_db is False):
            time_str = format_time(hours, minutes)
            post_to_channel(
                f"Є світло 💡\n" f"Відключення тривало: {time_str}",
                disable_notification,
            )
            time.sleep(600)

        # Зникло світло
        if (current_status is False or None) and (last_status_in_db is True):
            time_str = format_time(hours, minutes)
            post_to_channel(
                f"Світло відключили 🕯🔋\n" f"Світло було: {time_str}",
                disable_notification,
            )


@retry(wait_fixed=2000)
def check_status_with_retry() -> None:
    check_status()


def main() -> None:
    create_db()
    schedule.every(settings.SCHEDULE_TIME).minutes.do(check_status_with_retry)

    while True:
        schedule.run_pending()
        time.sleep(settings.SCHEDULE_TIME)


if __name__ == "__main__":
    main()
