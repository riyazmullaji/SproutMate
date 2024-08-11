import config
import json
import statistics
import time
from datetime import datetime, timedelta
import requests
from boltiot import Bolt, Sms
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Function to compute the Z-score bounds
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
            logging.error(f"Error: {data['message']}")
            return None
    except requests.RequestException as e:
        logging.error(f"Error fetching weather data: {e}")
        return None

# Function to check if significant rain is expected in the next forecast
def is_rain_expected(weather_forecast):
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
    logging.info(f"Forecast time: {forecast_time}, Current time: {current_time}")

    for condition in next_forecast["weather"]:
        description = condition["description"].lower()
        logging.info(f"Weather description: {description}")
        if description in rain_descriptions and rain_descriptions[description] >= 2:
            return True, description

    return False, "no significant rain"

# Function to check for adverse weather conditions
def is_adverse_weather(weather_forecast):
    adverse_conditions = {
        'thunderstorm': 'Thunderstorm conditions are expected.',
        'extreme rain': 'Extreme rain is expected.',
        'freezing rain': 'Freezing rain is expected.',
        'heavy snow': 'Heavy snow is expected.',
        'sleet': 'Sleet is expected.',
        'heavy shower snow': 'Heavy shower snow is expected.',
        'volcanic ash': 'Volcanic ash is expected.',
        'squalls': 'Squalls are expected.',
        'tornado': 'Tornado conditions are expected.'
    }

    for forecast in weather_forecast:
        for condition in forecast["weather"]:
            description = condition["description"].lower()
            for key in adverse_conditions:
                if key in description:
                    return True, adverse_conditions[key]
    return False, "No adverse weather conditions expected."

# Function to read sensor data
def read_sensor_data(bolt):
    response = bolt.analogRead('A0')
    data = json.loads(response)
    if data['success'] != 1:
        logging.error(f"Error retrieving data: {data['value']}")
        return None
    return int(data['value'])

# Function to send SMS
def send_sms(sms, message):
    try:
        response = sms.send_sms(message)
        logging.info(f"SMS sent: {response}")
    except Exception as e:
        logging.error(f"Error sending SMS: {e}")

def main():
    mybolt = Bolt(config.API_KEY, config.DEVICE_ID)
    sms = Sms(config.SSID, config.AUTH_TOKEN, config.TO_NUMBER, config.FROM_NUMBER)
    history_data = []
    api_key = config.WEATHER_API_KEY
    city_name = config.CITY_NAME
    last_message_time = datetime.now() - timedelta(seconds=3600)
    weather_forecast = get_weather_forecast(city_name, api_key)

    while True:
        sensor_value = read_sensor_data(mybolt)
        if sensor_value is None:
            time.sleep(5)
            continue

        soil = 100 - (sensor_value / 1024) * 100
        logging.info(f"The Moisture content is {soil:.2f} % mg/L")
        bound = compute_bounds(history_data, config.FRAME_SIZE, config.MUL_FACTOR)

        if not bound:
            required_data_count = config.FRAME_SIZE - len(history_data)
            logging.info(f"Not enough data to compute Z-score. Need {required_data_count} more data points")
            history_data.append(soil)
            time.sleep(5)
            continue

        if soil < config.THRESHOLD:
            rain_expected, rain_description = is_rain_expected(weather_forecast)
            if rain_expected:
                logging.info(f"Rain is expected soon: {rain_description}")
            elif (datetime.now() - last_message_time).total_seconds() >= 3600:
                logging.info("The Moisture level has decreased. Sending an SMS.")
                send_sms(sms, "Please water the plants")
                last_message_time = datetime.now()

        adverse_weather, adverse_message = is_adverse_weather(weather_forecast)
        if adverse_weather:
            logging.info(f"Adverse weather condition detected: {adverse_message}")
            send_sms(sms, f"Alert: {adverse_message}")

        if soil < bound[1]:
            logging.info("The Moisture level decreased suddenly. Sending an SMS.")
            send_sms(sms, "Someone is damaging the plants")

        logging.debug(f"HIGH BOUND = {bound[0]}")
        logging.debug(f"LOW BOUND = {bound[1]}")
        history_data.append(soil)
        time.sleep(10)

if __name__ == "__main__":
    main()
