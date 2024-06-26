import config
import json
import statistics
import time
from datetime import datetime, timedelta
import requests
from boltiot import Bolt, Sms

# Function to compute the Z-score bounds
def compute_bounds(history_data, frame_size, factor):
    # Ensure enough data points
    if len(history_data) < frame_size:
        return None

    # Maintain a fixed-size history
    if len(history_data) > frame_size:
        del history_data[0:len(history_data) - frame_size]

    # Calculate mean and standard deviation
    Mn = statistics.mean(history_data)
    StdDev = statistics.stdev(history_data)
    Zn = factor * StdDev
    High_bound = Mn + Zn
    Low_bound = Mn - Zn

    return [High_bound, Low_bound]

# Function to get the weather forecast for a city
def get_weather_forecast(city_name, api_key):
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city_name}&appid={api_key}&units=metric"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if data["cod"] == "200":
            return data["list"]
        else:
            print(f"Error: {data['message']}")
            return None
    except requests.RequestException as e:
        print(f"Error fetching weather data: {e}")
        return None

# Function to check if significant rain is expected in the next forecast
def is_rain_expected(weather_forecast):
    # Define rain description thresholds
    rain_descriptions = {
        'light rain': 1,
        'moderate rain': 2,
        'heavy intensity rain': 3,
        'very heavy rain': 4,
        'extreme rain': 5,
        'freezing rain': 6,
        'shower rain': 7,
        'ragged shower rain': 8,
        'light intensity shower rain': 9,
        'heavy intensity shower rain': 10,
    }

    next_forecast = weather_forecast[0]
    forecast_time = datetime.fromtimestamp(next_forecast["dt"])
    current_time = datetime.now()

    print(f"Forecast time: {forecast_time}, Current time: {current_time}")

    # Check the description of the next forecast
    for condition in next_forecast["weather"]:
        description = condition["description"].lower()
        print(f"Weather description: {description}")

        if description in rain_descriptions:
            if rain_descriptions[description] >= 2:  # Moderate rain or more intense
                return True, description
    
    return False, "no significant rain"

def main():
    # Initialize Bolt and SMS objects
    mybolt = Bolt(config.API_KEY, config.DEVICE_ID)
    sms = Sms(config.SSID, config.AUTH_TOKEN, config.TO_NUMBER, config.FROM_NUMBER)
    history_data = []
    api_key = config.WEATHER_API_KEY
    city_name = config.CITY_NAME

    # Initialize last message time
    last_message_time = datetime.now() - timedelta(seconds=3600)

    while True:
        # Read sensor data
        response = mybolt.analogRead('A0')
        data = json.loads(response)
        if data['success'] != 1:
            print("There was an error while retrieving the data.")
            print("This is the error:" + data['value'])
            time.sleep(10)
            continue

        print("This is the value " + data['value'])

        try:
            # Calculate soil moisture percentage
            soil = (int(data['value']) / 1024) * 100
            soil = 100 - soil
            print("The Moisture content is ", soil, " % mg/L")

        except Exception as e:
            print("There was an error while parsing the response: ", e)
            continue

        # Compute Z-score bounds for soil moisture
        bound = compute_bounds(history_data, config.FRAME_SIZE, config.MUL_FACTOR)

        if not bound:
            required_data_count = config.FRAME_SIZE - len(history_data)
            print("Not enough data to compute Z-score. Need", required_data_count, "more data points")
            history_data.append(soil)
            time.sleep(2)
            continue

        try:
            # Fetch weather forecast data
            weather_forecast = get_weather_forecast(config.CITY_NAME, api_key)
            if soil < config.THRESHOLD:
                rain_expected, rain_description = is_rain_expected(weather_forecast)
                if rain_expected:
                    print("Rain is expected soon. No need to water the plants.")
                    print("Rain description in the next forecast:", rain_description)
                else:
                    if (datetime.now() - last_message_time).total_seconds() >= 3600:
                        print("The Moisture level has decreased. Sending an SMS.")
                        response = sms.send_sms("Please water the plants")
                        print("This is the response ", response)
                        last_message_time = datetime.now()  # Update last message time

        except Exception as e:
            print("There was an error while processing: ", e)

        try:
            # Check if soil moisture levels are outside bounds
            if soil > bound[0]:
                print("The Moisture level increased suddenly. Sending an SMS.")
                response = sms.send_sms("Someone is damaging the plants")
                print("This is the response ", response)
            elif soil < bound[1]:
                print("The Moisture level decreased suddenly. Sending an SMS.")
                response = sms.send_sms("Someone is damaging the plants")
                print("This is the response ", response)

            # Print bounds for debugging
            print("HIGH BOUND = ", bound[0])
            print("LOW BOUND = ", bound[1])
            history_data.append(soil)

        except Exception as e:
            print("Error", e)
        time.sleep(10)

if __name__ == "__main__":
    main()
