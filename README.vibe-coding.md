# LastFM to Spotify Playlist Converter for vibe-coding.rocks

This repository contains the code for the LastFM to Spotify Playlist Converter, configured to run at `vibe-coding.rocks/lastfm-to-spotify-importer/`.

## Setup Instructions

### 1. Spotify API Configuration

Before deploying, you need to configure the Spotify API:

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new application or use an existing one
3. Set the Redirect URI to: `https://vibe-coding.rocks/lastfm-to-spotify-importer/callback`
4. Note your Client ID and Client Secret

### 2. LastFM API Configuration

1. Get a LastFM API key from [LastFM API](https://www.last.fm/api/account/create)
2. Note your API key

### 3. Environment Configuration

Create a `.env` file in the root directory with the following:

```
# Environment
ENVIRONMENT=production

# Service URL
SERVICE_URL=https://vibe-coding.rocks

# Base path for application
APP_BASE_PATH=/lastfm-to-spotify-importer

# LastFM API Key
LASTFM_API_KEY=your_lastfm_api_key

# Spotify API Credentials
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret

# Flask Secret Key
FLASK_SECRET_KEY=your_generated_secret_key
```

### 4. Deployment

1. Upload all files to your server directory corresponding to `/lastfm-to-spotify-importer/`
2. Configure your web server according to the instructions in `DEPLOYMENT.md`
3. Test the application by visiting `https://vibe-coding.rocks/lastfm-to-spotify-importer/`

## Files Overview

- `app.py`: The main Flask application
- `wsgi.py`: WSGI entry point for production deployment
- `.htaccess`: Apache configuration for subdirectory deployment
- `config.py`: Configuration settings
- `spotify_client.py`: Spotify API client
- `lastfm_client.py`: LastFM API client
- `playlist_converter.py`: Core conversion logic
- `templates/index.html`: Web interface

## Testing

After deployment, test the following:

1. LastFM username lookup
2. Spotify authentication
3. Playlist creation with different import options

## Support

If you encounter any issues, check the server logs and refer to the troubleshooting section in `DEPLOYMENT.md`. 