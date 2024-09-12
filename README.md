# MatterMostPRTGBot
This Python script monitors PRTG sensors and sends alerts to a Mattermost channel if any sensors are down. It reads a list of sensor object IDs from a file, checks their status via the PRTG API, and posts updates to Mattermost every minute.
