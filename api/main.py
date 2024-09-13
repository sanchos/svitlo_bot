import pytz
from fastapi import FastAPI
from datetime import datetime, timedelta
import os

app = FastAPI()

# File to store the last heartbeat timestamp
HEARTBEAT_FILE = "heartbeat.txt"


def get_last_heartbeat():
    """Read the last heartbeat timestamp from the file."""
    if not os.path.exists(HEARTBEAT_FILE):
        return None

    with open(HEARTBEAT_FILE, "r") as file:
        timestamp_str = file.read().strip()
        try:
            return datetime.fromisoformat(timestamp_str)  # Expect full ISO datetime
        except ValueError:
            return None


def update_heartbeat():
    """Update the heartbeat file with the current timestamp."""
    with open(HEARTBEAT_FILE, "w") as file:
        # Get the current time in Kyiv timezone (full datetime, not just time)
        kyiv_tz = pytz.timezone("Europe/Kyiv")
        current_time = datetime.now(kyiv_tz)  # Get full datetime (date + time)

        # Write full datetime (date + time) in ISO format
        file.write(current_time.isoformat())


@app.post("/api/heartbeat")
async def heartbeat():
    """Receive heartbeat from Mikrotik and update the timestamp."""
    update_heartbeat()
    return {"message": "Heartbeat received"}


@app.get("/api/status")
async def status():
    """Check the status of the Mikrotik device based on the last heartbeat."""
    last_heartbeat = get_last_heartbeat()
    if not last_heartbeat:
        return {"status": "NOT_OK", "detail": "No heartbeat received"}

    # Get the current time in Kyiv timezone (full datetime)
    kyiv_tz = pytz.timezone("Europe/Kyiv")
    current_time = datetime.now(kyiv_tz)

    # Compare full datetime objects to see if the last heartbeat was within 1 minute
    if current_time - last_heartbeat <= timedelta(minutes=1):
        return {"status": "OK"}
    else:
        return {"status": "NOT_OK"}


# Run the Uvicorn server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)
