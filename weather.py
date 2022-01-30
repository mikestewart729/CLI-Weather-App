# weather.py

import argparse
import json
import sys
from configparser import ConfigParser
from urllib import parse, request, error
from pprint import pp
from typing import List

import style

BASE_WEATHER_API_URL = "http://api.openweathermap.org/data/2.5/weather"

# Weather Condition Codes
# https://openweathermap.org/weather-conditions#Weather-Condition-Codes-2
THUNDERSTORM = range(200, 300)
DRIZZLE = range(300, 400)
RAIN = range(500, 600)
SNOW = range(600, 700)
ATMOSPHERE = range(700, 800)
CLEAR = range(800, 801)
CLOUDY = range(801, 900)

def _get_api_key() -> str:
    """
    Fetch the api key from the configuration file.

    Expects a configuration file named 'secrets.ini' with structure:
       [openweather]
       api_key=<YOUR_OPENWEATHER_API_KEY>
    """
    config = ConfigParser()
    config.read('secrets.ini')
    return config['openweather']['api_key']

def read_user_cli_args():
    """
    Handles the user command line interactions.

    Returns:
       argparse.Namespace: populated namespace object
    """
    parser = argparse.ArgumentParser(
        description="Gets weather and temperature information for a city"
    )
    parser.add_argument(
        'city', nargs='+', type=str, help='Enter the city name.'
    )
    parser.add_argument(
        '-c',
        '--centigrade',
        action='store_true',
        help='Display the temperature in degrees Celsius.'
    )
    return parser.parse_args()

def build_weather_query(city_input: List[str], centigrade: bool=False) -> str:
    """
    Builds the URL fo an API request to Openweather's weather API. 

    Args: 
       city_input (List[str]): Name of city as collected by argparse.
       centigrade (bool): Whether or not to use Celsius for temperature.

    Returns: 
       str: URL formatted for a call to Openweather's city name endpoint.
    """
    api_key = _get_api_key()
    city_name = " ".join(city_input)
    url_encoded_city_name = parse.quote_plus(city_name)
    units = 'metric' if centigrade else 'imperial'
    url = (
        f"{BASE_WEATHER_API_URL}?q={url_encoded_city_name}"
        f"&units={units}&APPID={api_key}"
    )
    return url

def get_weather_data(query_url:str) -> dict:
    """
    Makes an API request to a URL and returns the data as a python object.

    Args:
       query_url (str): URL formatted for Openweather's city name endpoint.

    Returns:
       dict: Weather information for a specific city.
    """
    try:
        response = request.urlopen(query_url)
    except error.HTTPError as http_error:
        if http_error.code == 401: # 401 - unauthorized
            sys.exit("Access denied. Check your API key.")
        elif http_error.code == 404: # 404 - not found
            sys.exit("Can't find weather data for this city.")
        else:
            sys.exit(f"Something went wrong... ({http_error.code})")

    data = response.read()

    try: 
        return json.loads(data)
    except json.JSONDecodeError:
        sys.exit("Couldn't read the server response.")

def _select_weather_display_params(weather_id):
    if weather_id in THUNDERSTORM:
        display_params = ("💥", style.RED)
    elif weather_id in DRIZZLE:
        display_params = ("💧", style.CYAN)
    elif weather_id in RAIN:
        display_params = ("💦", style.BLUE)
    elif weather_id in SNOW:
        display_params = ("🌨️", style.WHITE)
    elif weather_id in ATMOSPHERE:
        display_params = ("🌀", style.BLUE)
    elif weather_id in CLEAR:
        display_params = ("🔆", style.YELLOW)
    elif weather_id in CLOUDY:
        display_params = ("💨", style.WHITE)
    else:  # In case the API adds new weather codes
        display_params = ("🌈", style.RESET)
    return display_params

def _relative_temp_color(temperature: float, feels_like: float):
    """
    Returns red if feels_like is hotter than the current temperature and
    blue if feels_like is colder than the current temperature

    Args:
       temperature (float): The current measured temperature.
       feels_like (float): The current feels_like temperature factoring in
          humidity, wind chill, etc.
    
    Returns:
       color: color of relative difference between temperature and feels_like
    """
    color = style.RESET
    if feels_like > temperature:
        color = style.RED
    elif feels_like < temperature:
        color = style.BLUE
    return color

def display_weather_info(weather_data: dict, centigrade: bool=False):
    """
    Prints formatted weather information about a city.

    Args:
       weather_data (dict): API response from Openweather by city name.
       centigrade (bool): Whether or not to use degrees Celsius for temperature.

    More information at https://openweathermap.org/current#name
    """
    city = weather_data['name']
    weather_id = weather_data['weather'][0]['id']
    weather_description = weather_data['weather'][0]['description']
    temperature = weather_data['main']['temp']
    feels_like = weather_data['main']['feels_like']

    style.change_color(style.REVERSE)
    print(f"{city:^{style.PADDING}}", end="")
    style.change_color(style.RESET)

    weather_symbol, color = _select_weather_display_params(weather_id)

    style.change_color(color)
    print(f"\t{weather_symbol}", end=" ")
    print(f"\t{weather_description.capitalize():^{style.PADDING}}", end=" ")
    style.change_color(style.RESET)

    print(f"(Currently {temperature}°{'C' if centigrade else 'F'},", end="")

    rel_color = _relative_temp_color(temperature, feels_like)

    style.change_color(rel_color)
    print(f" feels like {feels_like}°{'C' if centigrade else 'F'}", end="")
    style.change_color(style.RESET)
    print(")")

if __name__ == '__main__':
    user_args = read_user_cli_args()
    query_url = build_weather_query(user_args.city, user_args.centigrade)
    weather_data = get_weather_data(query_url)
    display_weather_info(weather_data, user_args.centigrade)