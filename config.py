import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists (for local development)
load_dotenv()

# Last.fm API Configuration
LASTFM_API_KEY = os.getenv('LASTFM_API_KEY')
LASTFM_BASE_URL = 'http://ws.audioscrobbler.com/2.0/'

# Spotify API Configuration
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

# Base path for application when deployed as a subdirectory
APP_BASE_PATH = os.getenv('APP_BASE_PATH', '')  # Empty for root

# Dynamically set the redirect URI based on environment
# For local development use localhost, for production use the service URL
is_production = os.getenv('ENVIRONMENT') == 'production'
service_url = os.getenv('SERVICE_URL', 'https://lastfm-spotify-converter-v5nw64kyda-uc.a.run.app')

# Set the redirect URI based on environment
if is_production:
    SPOTIFY_REDIRECT_URI = f"{service_url}/callback"
    print(f"Using production redirect URI: {SPOTIFY_REDIRECT_URI}")
else:
    # For local development
    SPOTIFY_REDIRECT_URI = "http://127.0.0.1:8000/callback"
    print(f"Using local development redirect URI: {SPOTIFY_REDIRECT_URI}")

# Application Settings
DEFAULT_LIMIT = 50
MAX_TRACKS_PER_PLAYLIST = 10000
RATE_LIMIT_DELAY = 0.1  # seconds between API calls

# Supported time periods for Last.fm
LASTFM_PERIODS = {
    'overall': 'overall',
    '7day': '7day', 
    '1month': '1month',
    '3month': '3month',
    '6month': '6month',
    '12month': '12month'
} 