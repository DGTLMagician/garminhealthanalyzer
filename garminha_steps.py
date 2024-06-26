import datetime
import time
import random
import json
import logging
import os
import sys
import requests
import calendar
import html
import matplotlib.pyplot as plt
import numpy as np
import garth

from dotenv import load_dotenv
from garth.exc import GarthException
from getpass import getpass
from openai import OpenAI
from influxdb import InfluxDBClient

# function to convert sleep json data to InfluxDB suitable format and write it to InfluxDB
def stepjson_to_influxdb(host,port,database,json_data):
	# creating a connection to influxDB
    client = InfluxDBClient(host,port,username=influxuser, password=influxpass)  # replace with your InfluxDB host and port
	# switch to specific database
    client.switch_database(database)  # replace with your database name
    # Extracting relevant data from the JSON and converting to desired format, if not found assigning default values
    # Preparing json payload which will be pushed to InfluxDB
    influx_data = []
    for item in json_data:
        data_point = {
            "measurement": "step_data",  # You can replace "step_data" with your required measurement name
            "tags": {
                "measurement": "step_data" # You can add more tags if required
            },
            "time": item['calendarDate'],
            "fields": {
                "totalSteps": int(item['totalSteps']),
                "totalDistance": float(item['totalDistance']),
                "stepGoal": int(item['stepGoal'])
            }
        }
        influx_data.append(data_point)
    # Write points to InfluxDB
    client.write_points(influx_data)

# Entry point for the script
if __name__ == "__main__":
    # Loading environment variables
    load_dotenv()
    # assigning environment variables
    email = os.getenv("GARMINEMAIL")
    password = os.getenv("GARMINPASSWORD")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    garmintoken = os.getenv("GARMINTOKENS") or "~/.garminconnect"
    influxhost = os.getenv("INFLUXHOST")
    influxport = os.getenv("INFLUXPORT")
    influxuser = os.getenv("INFLUXUSER")
    influxpass = os.getenv("INFLUXPASS")
    influxdatabase = os.getenv("INFLUXDB")

    # Login to Garmin
    # If there's MFA, you'll be prompted during the login
    if os.path.isfile(garmintoken):
        try:
            garth.resume(garmintoken)
            garth.client.username
        except:
            # Login to Garmin
            garth.login(email, password)

            garth.save(garmintoken)
    else:
        # Login to Garmin
        garth.login(email, password)

        garth.save(garmintoken)


    # if command line arguments are passed use them to set the start and end date else use default values
    if len(sys.argv) >= 2:
        start_date = datetime.date.today() - datetime.timedelta(days=int(sys.argv[1]))
        end_date = datetime.date.today() - datetime.timedelta(days=int(sys.argv[2]))
    elif len(sys.argv) >= 1:
        start_date = datetime.date.today() - datetime.timedelta(days=int(sys.argv[1]))
        end_date = datetime.date.today()
    else:
        start_date = datetime.date.today() - datetime.timedelta(days=365*2)  # 2 years ago from today
        end_date = datetime.date.today()

    print(f"Syncing {start_date} until {end_date}")
    # Add time delta
    delta = datetime.timedelta(days=7)
    end_date_step = (start_date + delta) - datetime.timedelta(days=1)
    # iterating over days from start to end
    while not end_date_step > end_date:
        print(f"Working on Day: {start_date} End date Set: {end_date_step}")
        # fetching steps data for the day and writing to the InfluxDB
        try:
            steps = garth.connectapi(f"/usersummary-service/stats/steps/daily/{start_date}/{end_date_step}")
            stepjson_to_influxdb(influxhost,influxport,influxdatabase,steps)
        except:
            print(f"Fetching step data failed for {start_date}")
        #print(steps)
        start_date += delta
        end_date_step += delta

        # random sleep period to prevent detection
        time.sleep(random.randint(120,300))
