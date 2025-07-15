import argparse
import datetime
import os
import requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# If modifying these SCOPES, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

OPENWEATHERMAP_API_KEY = os.getenv('OPENWEATHERMAP_API_KEY')  # Set this in your environment


def connect_google_calendar():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    service = build('calendar', 'v3', credentials=creds)
    return service


def get_upcoming_events(service):
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    week_later = (datetime.datetime.utcnow() + datetime.timedelta(days=7)).isoformat() + 'Z'
    events_result = service.events().list(calendarId='primary', timeMin=now, timeMax=week_later,
                                          maxResults=10, singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])
    return events


def get_weather(location):
    if not OPENWEATHERMAP_API_KEY:
        print('OpenWeatherMap API key not set. Please set OPENWEATHERMAP_API_KEY environment variable.')
        return None
    url = f'https://api.openweathermap.org/data/2.5/weather?q={location}&appid={OPENWEATHERMAP_API_KEY}&units=metric'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print('Failed to fetch weather data.')
        return None


def suggest_greener_commutes(events, weather):
    if not events:
        print('No upcoming events to suggest commutes for.')
        return
    if not weather:
        print('No weather data available. Cannot make suggestions.')
        return
    weather_desc = weather['weather'][0]['main'].lower()
    temp = weather['main']['temp']
    print('\n🌍 Greener Commute Suggestions:')
    for event in events:
        summary = event.get('summary', 'No Title')
        location = event.get('location', 'Unknown location')
        # For demo, assume all events are within 5km
        if weather_desc in ['clear', 'clouds'] and 10 <= temp <= 25:
            print(f'- {summary} at {location}: Consider walking or biking (weather is nice: {weather_desc}, {temp}°C)')
        else:
            print(f'- {summary} at {location}: Consider public transport (weather: {weather_desc}, {temp}°C)')


def main():
    parser = argparse.ArgumentParser(description='Climate Action Agent CLI')
    parser.add_argument('--connect-calendar', action='store_true', help='Connect to Google Calendar')
    parser.add_argument('--location', type=str, help='Your city or location for weather data')
    args = parser.parse_args()

    print('🌱 Welcome to the Climate Action Agent CLI!')
    print('This tool helps you reduce your carbon footprint by suggesting greener commute options and eco-friendly actions.')

    events = []
    if args.connect_calendar:
        print('Connecting to Google Calendar...')
        service = connect_google_calendar()
        events = get_upcoming_events(service)
        print(f'Found {len(events)} events in the next week.')
        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            print(f"- {start}: {event.get('summary', 'No Title')}")

    weather = None
    if args.location:
        print(f'Fetching weather data for {args.location}...')
        weather = get_weather(args.location)
        if weather:
            print(f"Current weather in {args.location}: {weather['weather'][0]['description']}, {weather['main']['temp']}°C")

    # Placeholder: Suggest greener commute options
    suggest_greener_commutes(events, weather)

if __name__ == '__main__':
    main() 