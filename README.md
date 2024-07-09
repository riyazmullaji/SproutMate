# SmartSprout
Sprout Mate (SmartSprout) is an intelligent plant care system that utilizes Bolt IoT technology to monitor soil moisture and integrate real-time weather forecasts. By calculating Z-score bounds for moisture levels and fetching weather data from OpenWeatherMap, it ensures optimal plant health by sending SMS alerts for necessary actions, such as watering or protecting plants from potential damage. The system proactively prevents overwatering by considering upcoming rain and detects sudden moisture changes, offering a comprehensive, automated solution for plant care with minimal user intervention.

## Features

- **Soil Moisture Monitoring:** SmartSprout continuously tracks soil moisture levels to prevent over or under-watering.
- **Weather Integration:** Utilizes real-time weather forecasts to adjust watering schedules based on upcoming rain.
- **SMS Alerts:** Receive SMS alerts when soil moisture levels are low or when rain is expected, ensuring timely intervention.
- **Schematic Diagram:** Refer to the provided schematic diagram for hardware setup guidance.

## Hardware Requirements

To set up SmartSprout, you'll need the following hardware components:

- Bolt IoT Bolt WiFi Module
- Soil Moisture Sensor
- Breadboard
- Jumper Wires

## Software Requirements

SmartSprout relies on the following software apps and libraries:

- Bolt IoT Bolt Cloud
- OpenWeather API
- Twilio API

## Installation

To install SmartSprout, follow these steps:

1. Clone this repository to your local machine.
2. Set up your Bolt IoT Bolt WiFi Module and soil moisture sensor according to the hardware setup guide provided.
3. Obtain API keys for OpenWeather and Twilio and replace the placeholders in the code with your actual keys.
4. Deploy the SmartSprout code to your Bolt WiFi Module.
5. Access the provided schematic diagram for hardware setup guidance.

## Usage

Once installed, SmartSprout will automatically begin monitoring your plants and adjusting watering schedules based on soil moisture levels and weather forecasts. SMS alerts will be sent when intervention is required.

## Contributing

Contributions to SmartSprout are welcome! If you have any ideas for improvements or new features, feel free to submit a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- This project was inspired by the desire to simplify plant care and optimize plant health using IoT technology.
- Special thanks to Bolt IoT, OpenWeather, and Twilio for providing the tools and APIs necessary to build SmartSprout.
