PRTG to Mattermost Alert Bot
This Python script monitors PRTG sensors and sends alerts to a Mattermost channel if any sensors are down. It reads a list of sensor object IDs from a file, checks their status via the PRTG API, and posts updates to Mattermost every minute.

Configuration
Webhook URL
Replace WEBHOOK_URL with your Mattermost webhook URL.

Sensor Object IDs File
Update SENSOR_OBJIDS_FILE with the path to your file containing the sensor object IDs.

PRTG API URL
Adjust PRTG_API_URL if necessary to match your PRTG server's API endpoint and credentials.

Script Overview
Dependencies
requests: For making HTTP requests.
re: For regular expression operations.
datetime: For date and time manipulation.
time: For adding delays.
Functions
read_objids_from_file(file_path)
Reads sensor object IDs from the specified file. Returns a list of object IDs.

filter_down_sensors(sensors, target_objids)
Filters the list of sensors to include only those with object IDs in target_objids and a status that is not 'Up'.

clean_html(html)
Removes HTML tags from a given string using regular expressions.

extract_raw_last_up(last_up)
Extracts and formats the last update time from a given string. Calculates the downtime duration in days, hours, and minutes.

convert_downtime_to_days_hours(downtime_duration)
Converts a timedelta object into a string representing the duration in days, hours, and minutes.

send_to_mattermost(message)
Sends a message to Mattermost using the webhook URL.

send_prtg_updates()
Fetches sensor data from PRTG, filters for down sensors, and sends an alert message to Mattermost. If all sensors are up, it sends a confirmation message.

Main Loop
The script runs in an infinite loop, calling send_prtg_updates() every 60 seconds to keep the Mattermost channel updated.

Usage
Ensure all dependencies are installed.
Update the configuration variables (WEBHOOK_URL, SENSOR_OBJIDS_FILE, PRTG_API_URL).
Run the script: python script_name.py.

Example OUTPUT:

# Example output message for a down sensor
**Sensor ID**: 12345
**Device**: Device Name
**Status**: Down
**Last Up**: 09/12/2024 02:30:00 PM (2 days, 3 hours, 15 minutes)
**Message**: Sensor is not responding.
**-----------------------------**
