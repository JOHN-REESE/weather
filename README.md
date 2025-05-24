# City Weather Script

This script queries and displays the current weather for the user's automatically detected city. It uses your public IP address to determine your location and then fetches weather data from an external API.

## Requirements

*   Python 3
*   Dependencies listed in `requirements.txt` (geopy, requests)

## Setup

To install the necessary dependencies, run the following command in your terminal:

```bash
pip install -r requirements.txt
```

## Usage

To run the script and get the current weather for your city, execute the following command in your terminal:

```bash
python weather.py
```

The script will then print your detected city and the current weather conditions (temperature and description).
