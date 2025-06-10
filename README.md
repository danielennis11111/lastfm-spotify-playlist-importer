# 🎵 Last.fm to Spotify Playlist Converter

Convert your Last.fm listening data into Spotify playlists automatically! This tool fetches your music data from Last.fm's free API and creates corresponding playlists in your Spotify account.

## Features

- **Multiple Data Sources**: Import from Last.fm top tracks, recent tracks, or loved tracks
- **Time Period Support**: Create playlists from different time periods (7 days, 1 month, 3 months, etc.)
- **Smart Matching**: Intelligent track matching between Last.fm and Spotify
- **Batch Processing**: Handle large amounts of data efficiently
- **Preview Mode**: Preview tracks before creating playlists
- **Customization**: Custom playlist names, descriptions, and privacy settings
- **Rate Limiting**: Respects API rate limits to avoid getting blocked
- **Progress Tracking**: Real-time progress bars for long operations

## Prerequisites

### 1. Last.fm API Key
1. Visit [Last.fm API Account Creation](https://www.last.fm/api/account/create)
2. Create an API account and get your API key
3. **Note**: The Last.fm API is completely free for non-commercial use

### 2. Spotify App Credentials
1. Visit [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new app
3. Get your **Client ID** and **Client Secret**
4. Set the **Redirect URI** to: `http://127.0.0.1:8000/callback`

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd spotify-playlist-converter
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up API credentials**:
   
   **Option A: Interactive Setup (Recommended)**
   ```bash
   python main.py setup
   ```
   
   **Option B: Manual Setup**
   Create a `.env` file in the project directory:
   ```env
   # Last.fm API Configuration
   LASTFM_API_KEY=your_lastfm_api_key_here
   
   # Spotify API Configuration
   SPOTIFY_CLIENT_ID=your_spotify_client_id_here
   SPOTIFY_CLIENT_SECRET=your_spotify_client_secret_here
   SPOTIFY_REDIRECT_URI=http://127.0.0.1:8000/callback
   ```

## Usage

The tool provides several commands for different types of playlist creation:

### Basic Commands

```bash
# Convert top tracks from Last.fm to Spotify playlist
python main.py top YOUR_LASTFM_USERNAME

# Convert recent tracks
python main.py recent YOUR_LASTFM_USERNAME

# Convert loved tracks  
python main.py loved YOUR_LASTFM_USERNAME
```

### Advanced Options

```bash
# Top tracks with specific time period
python main.py top YOUR_USERNAME --period 3month --limit 100

# Private playlist with custom name
python main.py top YOUR_USERNAME --private --name "My Favorite Songs"

# Preview tracks before creating playlist
python main.py top YOUR_USERNAME --preview

# Custom description and limit
python main.py recent YOUR_USERNAME --limit 30 --description "My recent discoveries"
```

### Utility Commands

```bash
# Get user information
python main.py info YOUR_USERNAME

# List available time periods
python main.py periods

# Get help
python main.py --help
python main.py top --help
```

## Command Reference

### `top` - Convert Top Tracks
Converts your Last.fm top tracks for a specific time period.

**Options:**
- `--period, -p`: Time period (`overall`, `7day`, `1month`, `3month`, `6month`, `12month`)
- `--limit, -l`: Number of tracks to import (default: 50)
- `--name, -n`: Custom playlist name
- `--description, -d`: Custom playlist description
- `--private`: Make playlist private (default: public)
- `--preview`: Preview tracks without creating playlist

**Examples:**
```bash
# Your top tracks of all time
python main.py top rj

# Top tracks from last 3 months, limited to 25 songs
python main.py top rj --period 3month --limit 25

# Private playlist with custom name
python main.py top rj --period 1month --private --name "December Favorites"
```

### `recent` - Convert Recent Tracks
Converts your recently played tracks.

**Options:**
- `--limit, -l`: Number of tracks to import (default: 50)
- `--name, -n`: Custom playlist name  
- `--description, -d`: Custom playlist description
- `--private`: Make playlist private
- `--preview`: Preview tracks

**Examples:**
```bash
# Recent 50 tracks
python main.py recent rj

# Recent 100 tracks with custom name
python main.py recent rj --limit 100 --name "What I've Been Playing"
```

### `loved` - Convert Loved Tracks
Converts your loved/hearted tracks from Last.fm.

**Options:**
- `--limit, -l`: Number of tracks to import (default: 50)
- `--name, -n`: Custom playlist name
- `--description, -d`: Custom playlist description  
- `--private`: Make playlist private
- `--preview`: Preview tracks

**Examples:**
```bash
# All loved tracks (up to 50)
python main.py loved rj

# First 25 loved tracks as private playlist
python main.py loved rj --limit 25 --private
```

## How It Works

1. **Fetch Data**: Connects to Last.fm API and fetches your listening data
2. **Search Spotify**: For each track, searches Spotify using artist and track name
3. **Smart Matching**: Uses intelligent matching to find the best Spotify track
4. **Create Playlist**: Creates a new Spotify playlist in your account
5. **Add Tracks**: Adds all matched tracks to the playlist

## Matching Algorithm

The tool uses a sophisticated matching algorithm:

1. **Exact Search**: First tries exact artist and track name matching
2. **Fuzzy Search**: Falls back to more flexible search strategies
3. **Scoring System**: Ranks results based on artist similarity, track name similarity, and popularity
4. **Threshold Filtering**: Only includes tracks with a confidence score above 30%

## Limitations

- **API Rate Limits**: Both Last.fm and Spotify have rate limits, so large imports may take time
- **Track Availability**: Not all Last.fm tracks may be available on Spotify
- **Matching Accuracy**: Track matching is ~70-90% accurate depending on your music library
- **Spotify Limits**: Maximum 100 tracks per playlist creation request
- **Last.fm Data**: Requires public Last.fm profile or API access

## Troubleshooting

### Common Issues

**"No tracks found"**
- Check that the Last.fm username is correct and public
- Verify the user has tracks in the requested time period

**"Spotify authentication failed"**
- Check your Client ID and Client Secret
- Ensure redirect URI is set to `http://127.0.0.1:8000/callback`
- Make sure you approve the authentication in your browser

**"Rate limit exceeded"**
- Wait a few minutes and try again
- Reduce the number of tracks with `--limit`

**Low match rate**
- This is normal for niche music or non-English tracks
- The tool will still create a playlist with found tracks

### Debug Mode

For troubleshooting, you can check the individual API responses:

```python
from lastfm_client import LastFmClient
from spotify_client import SpotifyClient

# Test Last.fm connection
lastfm = LastFmClient()
tracks = lastfm.get_user_top_tracks('your_username', limit=5)
print(tracks)

# Test Spotify connection  
spotify = SpotifyClient()
results = spotify.search_track('Radiohead', 'Creep')
print(results)
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is for educational and personal use. Please respect the API terms of service for both Last.fm and Spotify.

## Disclaimer

This tool is not affiliated with Last.fm or Spotify. Use responsibly and respect rate limits. 