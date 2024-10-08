import time
import requests
import re
from datetime import datetime, timedelta
import logging

# Configure logging for debugging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')

# Configuration (Replace with actual values)
WEBHOOK_URL = '<MATTERMOST_WEBHOOK_URL>'  # Placeholder: URL for Mattermost incoming webhook
PRTG_API_URL = '<PRTG_API_URL>'  # Placeholder: URL for PRTG API
SENSOR_OBJIDS_FILE = '<PATH_TO_SENSOR_OBJIDS_FILE>'  # Placeholder: Path to file with sensor objids

# Keep track of previously down sensors to monitor changes
previously_down_sensors = {}

# Function to read sensor objids from a file
def read_objids_from_file(file_path):
    """
    Reads sensor objids from a specified file.

    :param file_path: Path to the file containing sensor objids.
    :return: List of sensor objids.
    """
    try:
        with open(file_path, 'r') as file:
            objids = [line.strip() for line in file.readlines() if line.strip()]
        logging.debug(f"Read {len(objids)} objids from {file_path}")
        return objids
    except Exception as e:
        logging.error(f"Error reading objids from file: {e}")
        return []

# Function to filter sensors based on objids and status (only when down)
def filter_down_sensors(sensors, target_objids):
    """
    Filters sensors that are down based on target objids.

    :param sensors: List of sensors fetched from PRTG API.
    :param target_objids: List of target sensor objids.
    :return: List of sensors that are down.
    """
    filtered_sensors = []
    target_objids_set = set(map(int, target_objids))  # Convert objids to integers

    for sensor in sensors:
        sensor_objid = int(sensor['objid'])  # Ensure sensor objid is an integer
        if sensor_objid in target_objids_set and sensor['status'] != 'Up':  # Only when sensor is down
            filtered_sensors.append(sensor)

    logging.debug(f"Found {len(filtered_sensors)} down sensors after filtering")
    return filtered_sensors

# Function to clean HTML tags from sensor messages
def clean_html(html):
    """
    Removes HTML tags from a string.

    :param html: String containing HTML.
    :return: Cleaned string without HTML tags.
    """
    clean = re.compile('<.*?>')
    return re.sub(clean, '', html)

# Function to extract and format the last up time of a sensor
def extract_raw_last_up(last_up):
    """
    Extracts the last up time of a sensor from the message and converts it to a readable format.

    :param last_up: Raw last up time string from PRTG.
    :return: Formatted last up time and downtime duration.
    """
    try:
        if last_up:
            date_match = re.search(r'\d{1,2}/\d{1,2}/\d{4} \d{1,2}:\d{2}:\d{2} (AM|PM)', last_up)
            if date_match:
                last_up_str = date_match.group(0)
                last_up_time = datetime.strptime(last_up_str, '%m/%d/%Y %I:%M:%S %p')
                now = datetime.now()
                downtime_duration = now - last_up_time
                days_hours_minutes_str = convert_downtime_to_days_hours(downtime_duration)
                return f"{last_up_str} {days_hours_minutes_str}"
        return "Unknown"
    except Exception as e:
        logging.error(f"Error in extract_raw_last_up: {e}")
        return "Unknown"

# Function to convert downtime duration into days, hours, and minutes
def convert_downtime_to_days_hours(downtime_duration):
    """
    Converts a timedelta object into a string representing days, hours, and minutes.

    :param downtime_duration: Timedelta object representing downtime duration.
    :return: Formatted string of days, hours, and minutes.
    """
    try:
        total_seconds = downtime_duration.total_seconds()
        days = total_seconds // (24 * 3600)
        hours = (total_seconds % (24 * 3600)) // 3600
        minutes = (total_seconds % 3600) // 60
        return f"({int(days)} days, {int(hours)} hours, {int(minutes)} minutes)"
    except Exception as e:
        logging.error(f"Error in convert_downtime_to_days_hours: {e}")
        return "(Unknown)"

# Function to send the PRTG updates to Mattermost
def send_to_mattermost(message):
    """
    Sends a message to a Mattermost channel via webhook.

    :param message: The message to be sent.
    """
    headers = {
        'Content-Type': 'application/json',
    }
    data = {
        "text": message,
        "username": "PRTG-ALERT"  # Custom bot name
    }
    try:
        response = requests.post(WEBHOOK_URL, json=data, headers=headers)
        if response.status_code != 200:
            logging.error(f"Failed to send message to Mattermost: {response.status_code}, {response.text}")
        else:
            logging.debug(f"Message sent to Mattermost successfully: {message[:100]}...")  # Log first 100 chars of the message
    except Exception as e:
        logging.error(f"Error sending message to Mattermost: {e}")

# Function to fetch and send updates
def send_prtg_updates():
    """
    Fetches PRTG sensor data, processes it, and sends relevant alerts to Mattermost.
    """
    global previously_down_sensors  # Access global variable to track sensor statuses
    try:
        # Read target sensor objids from file
        target_objids = read_objids_from_file(SENSOR_OBJIDS_FILE)
        response = requests.get(PRTG_API_URL)
        data = response.json()

        # Filter the down sensors
        filtered_sensors = filter_down_sensors(data['sensors'], target_objids)

        # Initialize messages
        down_message = ""
        restore_message = ""
        all_okay_message = ""

        # Handle sensors that are currently down
        if filtered_sensors:
            down_message += "**🚨 Attention! The following devices are down:**\n\n"
            for sensor in filtered_sensors:
                cleaned_message = clean_html(sensor['message'])  # Clean HTML tags
                raw_last_up = extract_raw_last_up(sensor['lastup'])
                down_message += (
                    f"**Sensor ID**: {sensor['objid']}\n"
                    f"**Device**: {sensor['device']}\n"
                    f"**Status**: {sensor['status']}\n"
                    f"**Last Up**: {raw_last_up}\n"
                    f"**Message**: {cleaned_message}\n"
                    f"**-----------------------------**\n"
                )
                previously_down_sensors[sensor['objid']] = sensor  # Track down sensors

            # Send down message to Mattermost
            send_to_mattermost(down_message)

        # Handle sensors that have been restored
        restored_sensors = []
        for objid, sensor in list(previously_down_sensors.items()):
            sensor_status = next((s for s in data['sensors'] if int(s['objid']) == int(objid)), None)
            if sensor_status and sensor_status['status'] == 'Up':  # Sensor is back up
                raw_last_up = extract_raw_last_up(sensor['lastup'])
                restore_message += (
                    f"✅ **Device Restored**\n\n"
                    f"**Sensor ID**: {sensor['objid']}\n"
                    f"**Device**: {sensor['device']}\n"
                    f"**Status**: Up  {raw_last_up} downtime\n"
                    f"**Message**: Device is now responding and functioning normally.\n"
                    f"**-----------------------------**\n"
                )
                restored_sensors.append(objid)  # Track restored sensors

        # Remove restored sensors from the tracking list
        for objid in restored_sensors:
            del previously_down_sensors[objid]

        # Send restore message to Mattermost
        if restore_message:
            send_to_mattermost(restore_message)

        # If no sensors are down, send an all-clear message
        if not previously_down_sensors and not filtered_sensors:
            all_okay_message = "✅ **All monitored devices are functioning normally.**\n"
            send_to_mattermost(all_okay_message)

    except Exception as e:
        logging.error(f"Error fetching PRTG data: {e}")

# Main loop to send updates every minute
if __name__ == "__main__":
    while True:
        send_prtg_updates()
        time.sleep(60)  # Wait for 60 seconds before fetching updates again
