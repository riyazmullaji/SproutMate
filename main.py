import json
import statistics
import time
from datetime import datetime, timedelta
import requests
from boltiot import Bolt, Sms
import config  # Ensure this file contains your necessary configurations

def compute_bounds(history_data, frame_size, factor):
    if len(history_data) < frame_size:
        return None

    if len(history_data) > frame_size:
        del history_data[0:len(history_data) - frame_size]

    Mn = statistics.mean(history_data)
    StdDev = statistics.stdev(history_data)
    Zn = factor * StdDev
    High_bound = Mn + Zn
    Low_bound = Mn - Zn

    return [High_bound, Low_bound]

def get_coordinates(city_name, api_key):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={api_key}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if "coord" in data:
            return data["coord"]["lat"], data["coord"]["lon"]
        else:
            print(f"Error: {data['message']}")
            return None, None
    except requests.RequestException as e:
        print(f"Error fetching coordinates: {e}")
        return None, None

def get_weather_forecast(lat, lon, api_key):
    url = f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric"
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

def is_rain_expected(weather_forecast, time_delta=1, rain_threshold=2.5):
    current_time = datetime.now()
    end_time = current_time + timedelta(hours=time_delta)

    for forecast in weather_forecast:
        forecast_time = datetime.fromtimestamp(forecast["dt"])
        if current_time <= forecast_time <= end_time:
            description = forecast["weather"][0]["description"].lower()
            print(f"Checking forecast for time: {forecast_time}, description: {description}")
            if "rain" in description:
                rain_intensity = forecast.get("rain", {}).get("3h", 0)
                print(f"Rain intensity: {rain_intensity} mm")
                if rain_intensity >= rain_threshold:
                    return True
    return False

def send_sms(sms, message):
    try:
        response = sms.send_sms(message)
        print("SMS Response: ", response)
    except Exception as e:
        print("Error sending SMS: ", e)

def process_moisture_data(soil, bound, last_message_time, sms, rain_expected):
    if soil < config.threshold:
        if rain_expected:
            print("Rain expected soon. No need to water the plants.")
        else:
            if (datetime.now() - last_message_time).total_seconds() >= 3600:
                print("Moisture level low. Sending SMS.")
                send_sms(sms, "Please water the plants")
                last_message_time = datetime.now()

    if soil > bound[0]:
        print("Moisture level increased suddenly. Sending SMS.")
        send_sms(sms, "Someone is damaging the plants")
    elif soil < bound[1]:
        print("Moisture level decreased suddenly. Sending SMS.")
        send_sms(sms, "Someone is damaging the plants")

    print("HIGH BOUND = ", bound[0])
    print("LOW BOUND = ", bound[1])

    return last_message_time

def main():
    mybolt = Bolt(config.API_KEY, config.DEVICE_ID)
    sms = Sms(config.SSID, config.AUTH_TOKEN, config.TO_NUMBER, config.FROM_NUMBER)
    history_data = []
    api_key = config.WEATHER_API_KEY
    city_name = config.CITY_NAME

    last_message_time = datetime.now() - timedelta(seconds=3600)  # Set last_message_time 3600 seconds ago

    while True:
        try:
            response = mybolt.analogRead('A0')
            data = json.loads(response)
            if data['success'] != 1:
                print("Error retrieving data: ", data['value'])
                time.sleep(10)
                continue

            soil = (int(data['value']) / 1024) * 100
            soil = 100 - soil
            print("Moisture content: ", soil, " %")

        except Exception as e:
            print("Error parsing response: ", e)
            time.sleep(10)
            continue

        bound = compute_bounds(history_data, config.FRAME_SIZE, config.MUL_FACTOR)

        if not bound:
            required_data_count = config.FRAME_SIZE - len(history_data)
            print(f"Not enough data to compute Z-score. Need {required_data_count} more data points")
            history_data.append(soil)
            time.sleep(2)
            continue

        try:
            lat, lon = get_coordinates(city_name, api_key)
            if lat is not None and lon is not None:
                weather_forecast = get_weather_forecast(lat, lon, api_key)
                if weather_forecast:
                    rain_expected = is_rain_expected(weather_forecast)
                    print(f"Rain expected in the next hour: {rain_expected}")
                else:
                    rain_expected = False
            else:
                print("Error fetching coordinates, skipping rain check.")
                rain_expected = False

        except Exception as e:
            print("Error processing weather data: ", e)
            rain_expected = False

        last_message_time = process_moisture_data(soil, bound, last_message_time, sms, rain_expected)
        history_data.append(soil)

        time.sleep(10)

if __name__ == "__main__":
    main()
