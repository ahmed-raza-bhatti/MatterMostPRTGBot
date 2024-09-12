 # Provides functions for working with time, such as adding delays.
import time

 # Allows sending HTTP requests to interact with APIs and web services.
import requests

# Supports regular expression operations for searching and manipulating strings.
import re

# Provides classes for working with dates and times.
from datetime import datetime, timedelta  

# Configuration
# Replace with your Mattermost incoming webhook URL
WEBHOOK_URL = 'https://your-mattermost-server.com/hooks/[your-webhook-key]' 

# Set the variable to your PRTG API endpoint. Ensure it includes your credentials and the necessary parameters
PRTG_API_URL = 'http://[your-prtg-server]/api/table.json?count=5000&content=sensors&output=json&columns=objid,probe,device,sensor,status,message,lastup&username=[your-username]&passhash=[your-passhash]'

# Set the SENSOR_OBJIDS_FILE variable to the path of your file containing sensor object IDs.
SENSOR_OBJIDS_FILE = 'C:\\path\\to\\your\\sensor_objids.txt'


# Function to read sensor objids from a file
def read_objids_from_file(file_path):
    try:
        with open(file_path, 'r') as file:
            objids = [line.strip() for line in file.readlines() if line.strip()]
        print(f"Read objids: {objids}")  # Debug: Print objids read from the file
        return objids
    except Exception as e:
        print(f"Error reading objids from file: {e}")
        return []

# Function to filter sensors based on objids and status (only when down)
def filter_down_sensors(sensors, target_objids):
    filtered_sensors = []
    target_objids_set = set(map(int, target_objids))  # Convert target_objids to integers
    print(f"Target objids: {target_objids_set}")  # Debug: Print target objids

    for sensor in sensors:
        sensor_objid = int(sensor['objid'])  # Convert sensor objid to integer
        if sensor_objid in target_objids_set and sensor['status'] != 'Up':  # Only when down
            filtered_sensors.append(sensor)

    return filtered_sensors

def clean_html(html):
    """Remove HTML tags from a string."""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', html)

def extract_raw_last_up(last_up):
    """Extract and format the last up time."""
    try:
        if last_up:
            date_match = re.search(r'\d{1,2}/\d{1,2}/\d{4} \d{1,2}:\d{2}:\d{2} (AM|PM)', last_up)
            if date_match:
                last_up_str = date_match.group(0)  # Extract the matched date string
                print(f"Raw last_up_str: {last_up_str}")  # Debug: Print raw last up string

                # Parse the extracted date
                last_up_time = datetime.strptime(last_up_str, '%m/%d/%Y %I:%M:%S %p')
                now = datetime.now()

                # Calculate the downtime duration
                downtime_duration = now - last_up_time

                # Convert downtime to days, hours, and minutes
                days_hours_minutes_str = convert_downtime_to_days_hours(downtime_duration)

                return f"{last_up_str} {days_hours_minutes_str}"
        return "Unknown"
    except Exception as e:
        print(f"Error in extract_raw_last_up: {e}")
        return "Unknown"

def convert_downtime_to_days_hours(downtime_duration):
    """Convert downtime duration to days, hours, and minutes."""
    try:
        total_seconds = downtime_duration.total_seconds()
        days = total_seconds // (24 * 3600)
        hours = (total_seconds % (24 * 3600)) // 3600
        minutes = (total_seconds % 3600) // 60
        return f"({int(days)} days, {int(hours)} hours, {int(minutes)} minutes)"
    except Exception as e:
        print(f"Error in convert_downtime_to_days_hours: {e}")
        return "(Unknown)"

# Function to send the PRTG updates to Mattermost
def send_to_mattermost(message):
    headers = {
        'Content-Type': 'application/json',
    }
    data = {
        "text": message,
        "username": "PRTG-ALERT"  # Set the custom name here
    }
    response = requests.post(WEBHOOK_URL, json=data, headers=headers)
    if response.status_code != 200:
        print(f"Failed to send message to Mattermost: {response.status_code}, {response.text}")

# Function to fetch and send updates
def send_prtg_updates():
    try:
        target_objids = read_objids_from_file(SENSOR_OBJIDS_FILE)  # Read sensor objids from file
        response = requests.get(PRTG_API_URL)
        data = response.json()

        # Filter the sensors
        filtered_sensors = filter_down_sensors(data['sensors'], target_objids)

        # Initialize messages
        down_message = ""
        all_okay_message = ""

        if filtered_sensors:
            # Build down message
            down_message += "**🚨 Attention! The following devices are down:**\n\n"
            for sensor in filtered_sensors:
                cleaned_message = clean_html(sensor['message'])  # Clean HTML tags
                if sensor['lastup']:
                    raw_last_up = extract_raw_last_up(sensor['lastup'])
                    down_message += (
                        f"**Sensor ID**: {sensor['objid']}\n"
                        f"**Device**: {sensor['device']}\n"
                        f"**Status**: {sensor['status']}\n"
                        f"**Last Up**: {raw_last_up}\n"
                        f"**Message**: {cleaned_message}\n"
                        f"**-----------------------------**\n"
                    )
                else:
                    down_message += (
                        f"**Sensor ID**: {sensor['objid']}\n"
                        f"**Device**: {sensor['device']}\n"
                        f"**Status**: {sensor['status']}\n"
                        f"**Message**: {cleaned_message}\n"
                        f"**-----------------------------**\n"
                    )

            # Send down message
            send_to_mattermost(down_message)
        else:
            # Build okay message
            all_okay_message = "✅ **All monitored devices are functioning normally.**\n"

            # Send okay message
            send_to_mattermost(all_okay_message)

    except Exception as e:
        print(f"Error fetching PRTG data: {e}")

# Main loop to send updates every minute
if __name__ == "__main__":
    while True:
        send_prtg_updates()
        time.sleep(60)
