# config.py

# Bolt device configuration
API_KEY = "your_bolt_api_key"       # Replace with your Bolt Cloud API key
DEVICE_ID = "your_device_id"        # Replace with your Bolt device ID

# Twilio SMS service configuration
SSID = "your_twilio_ssid"           # Replace with your Twilio SSID
AUTH_TOKEN = "your_twilio_auth_token"  # Replace with your Twilio Auth Token
TO_NUMBER = "recipient_phone_number"  # Replace with the recipient's phone number
FROM_NUMBER = "twilio_phone_number"  # Replace with your Twilio phone number

# OpenWeatherMap API configuration
WEATHER_API_KEY = "your_openweathermap_api_key"  # Replace with your OpenWeatherMap API key
CITY_NAME = "your_city_name"  # Replace with the city name for weather forecasting

# Soil moisture monitoring configuration
FRAME_SIZE = 10  # Number of data points for computing Z-score bounds
MUL_FACTOR = 2  # Factor to multiply the standard deviation for setting bounds
THRESHOLD = 30  # Soil moisture threshold to determine if watering is needed (%)
