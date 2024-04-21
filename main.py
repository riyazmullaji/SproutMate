import config
import json
import statistics
import time
from datetime import datetime, timedelta
import requests
from boltiot import Bolt, Sms

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

def is_rain_expected(weather_forecast, time_delta=1, rain_threshold=2.5):
    current_time = datetime.now()
    end_time = current_time + timedelta(hours=time_delta)

    for forecast in weather_forecast:
        forecast_time = datetime.fromtimestamp(forecast["dt"])
        if forecast_time <= end_time:
            if "rain" in forecast["weather"][0]["description"].lower():
                rain_intensity = forecast.get("rain", {}).get("3h", 0)
                if rain_intensity >= rain_threshold:
                    return True
    return False

def main():
    mybolt = Bolt(config.API_KEY, config.DEVICE_ID)
    sms = Sms(config.SSID, config.AUTH_TOKEN, config.TO_NUMBER, config.FROM_NUMBER)
    history_data = []
    api_key = config.WEATHER_API_KEY
    city_name = config.CITY_NAME

    last_message_time = datetime.now() - timedelta(seconds=3600)  # Set last_message_time 3600 seconds ago

    while True:
        response = mybolt.analogRead('A0')
        data = json.loads(response)
        if data['success'] != 1:
            print("There was an error while retrieving the data.")
            print("This is the error:" + data['value'])
            time.sleep(10)
            continue

        print("This is the value " + data['value'])

        try:
            soil = (int(data['value']) / 1024) * 100
            soil = 100 - soil
            print("The Moisture content is ", soil, " % mg/L")
        except Exception as e:
            print("There was an error while parsing the response: ", e)
            continue

        bound = compute_bounds(history_data, config.FRAME_SIZE, config.MUL_FACTOR)

        if not bound:
            required_data_count = config.FRAME_SIZE - len(history_data)
            print("Not enough data to compute Z-score. Need", required_data_count, "more data points")
            history_data.append(soil)
            time.sleep(2)
            continue

        try:
            weather_forecast = get_weather_forecast(config.CITY_NAME, api_key)
            if soil < config.threshold:
                if is_rain_expected(weather_forecast):
                    print("Rain is expected within the next hour. No need to water the plants.")
                else:
                    if (datetime.now() - last_message_time).total_seconds() >= 3600:
                        print("The Moisture level has decreased. Sending an SMS.")
                        response = sms.send_sms("Please water the plants")
                        print("This is the response ", response)
                        last_message_time = datetime.now()  # Update last message time

        except Exception as e:
            print("There was an error while processing: ", e)

        try:
            if soil > bound[0]:
                print("The Moisture level increased suddenly. Sending an SMS.")
                response = sms.send_sms("Someone is damaging the plants")
                print("This is the response ", response)
            elif soil < bound[1]:
                print("The Moisture level decreased suddenly. Sending an SMS.")
                response = sms.send_sms("Someone is damaging the plants")
                print("This is the response ", response)

            print("HIGH BOUND = ", bound[0])
            print("LOW BOUND = ", bound[1])
            history_data.append(soil)

        except Exception as e:
            print("Error", e)
        time.sleep(10)

if __name__ == "__main__":
   main()
