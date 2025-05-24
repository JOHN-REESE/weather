import requests
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable

def get_current_location():
    """
    Retrieves the current location (latitude, longitude, and city)
    based on the machine's public IP address.

    Returns:
        dict: A dictionary containing 'latitude', 'longitude', and 'city',
              or None if the location cannot be determined.
    """
    try:
        # Get IP address and location data from ipinfo.io
        response = requests.get("https://ipinfo.io/json")
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()

        latitude = data.get("loc").split(',')[0]
        longitude = data.get("loc").split(',')[1]
        city = data.get("city")

        if not city: # If city is not directly available from ipinfo.io, try reverse geocoding
            geolocator = Nominatim(user_agent="city_weather_app/1.0")
            # Ensure latitude and longitude are floats for Nominatim
            location = geolocator.reverse((float(latitude), float(longitude)), language='en', zoom=10)
            if location and location.address:
                # Nominatim often returns a detailed address, we need to parse the city
                # This can be complex as address formats vary.
                # We'll look for 'city', 'town', or 'village' in the address components.
                address_components = location.raw.get('address', {})
                city = address_components.get('city', address_components.get('town', address_components.get('village')))
            else:
                # Fallback if reverse geocoding fails or doesn't provide city
                city = "Unknown"


        if latitude and longitude and city:
            return {
                "latitude": float(latitude),
                "longitude": float(longitude),
                "city": city
            }
        else:
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error fetching IP information: {e}")
        return None
    except (GeocoderTimedOut, GeocoderUnavailable) as e:
        print(f"Geocoding service error: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

if __name__ == '__main__':
    print("Fetching your current location...")
    location_data = get_current_location()

    if location_data:
        city = location_data.get("city", "Unknown city")
        latitude = location_data.get("latitude")
        longitude = location_data.get("longitude")

        print(f"Successfully determined your location: {city}")

        if latitude is not None and longitude is not None:
            print(f"Fetching weather for {city} ({latitude}, {longitude})...")
            weather_data = get_weather(latitude, longitude)

            if weather_data:
                temperature = weather_data.get("temperature")
                description = weather_data.get("weather_description")
                print(f"The current weather in {city} is: {temperature}°C, {description}.")
            else:
                print(f"Could not retrieve weather information for {city}.")
        else:
            # This case should ideally not be reached if get_current_location guarantees lat/lon with city
            print("Latitude or longitude missing, cannot fetch weather.")
    else:
        print("Could not determine your current location.")

def get_weather(latitude: float, longitude: float):
    """
    Fetches weather data from Open-Meteo API for the given latitude and longitude.

    Args:
        latitude (float): Latitude of the location.
        longitude (float): Longitude of the location.

    Returns:
        dict: A dictionary containing 'temperature' and 'weather_description',
              or None if weather data cannot be fetched.
    """
    api_url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current_weather=true"

    # WMO Weather interpretation codes
    # Reference: https://open-meteo.com/en/docs (section: WMO Weather interpretation codes)
    # Simplified for this example
    WMO_CODES = {
        0: 'Clear sky',
        1: 'Mainly clear',
        2: 'Partly cloudy',
        3: 'Overcast',
        45: 'Fog',
        48: 'Depositing rime fog',
        51: 'Light drizzle',
        53: 'Moderate drizzle',
        55: 'Dense drizzle',
        56: 'Light freezing drizzle',
        57: 'Dense freezing drizzle',
        61: 'Slight rain',
        63: 'Moderate rain',
        65: 'Heavy rain',
        66: 'Light freezing rain',
        67: 'Heavy freezing rain',
        71: 'Slight snow fall',
        73: 'Moderate snow fall',
        77: 'Snow grains',
        80: 'Slight rain showers',
        81: 'Moderate rain showers',
        82: 'Violent rain showers',
        85: 'Slight snow showers',
        86: 'Heavy snow showers',
        95: 'Thunderstorm', # Slight or moderate
        96: 'Thunderstorm with slight hail',
        99: 'Thunderstorm with heavy hail',
    }

    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()

        current_weather = data.get("current_weather")
        if not current_weather:
            print("Current weather data not found in response.")
            return None

        temperature = current_weather.get("temperature")
        weather_code = current_weather.get("weathercode")

        if temperature is None or weather_code is None:
            print("Temperature or weather code not found in current weather data.")
            return None
        
        # Get weather description from WMO_CODES, default to "Unknown" if code not found
        weather_description = WMO_CODES.get(weather_code, "Unknown weather code")
        
        # Handle ranges for codes 1-3 as per some WMO interpretations if needed,
        # but Open-Meteo provides discrete codes.
        # For simplicity, we use the direct mapping. If weather_code is 1, 2, or 3, it's already handled.
        # If specific ranges like 1-3 -> "Mainly clear, partly cloudy, and overcast" were required,
        # additional logic would be needed here. For now, the direct mapping is used.

        return {
            "temperature": temperature,
            "weather_description": weather_description
        }

    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data: {e}")
        return None
    except ValueError as e: # Handles JSON decoding errors
        print(f"Error parsing weather data: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while fetching weather: {e}")
        return None
