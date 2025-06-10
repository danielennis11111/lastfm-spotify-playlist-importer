# 🚀 Quick Start Guide

Get your Last.fm data into Spotify playlists in 5 minutes!

## Step 1: Get API Keys

### Last.fm API Key (Free)
1. Go to https://www.last.fm/api/account/create
2. Fill out the form (use any app name/description)
3. Copy your **API Key**

### Spotify App Credentials (Free)
1. Go to https://developer.spotify.com/dashboard
2. Click **"Create app"**
3. Fill in:
   - **App name**: "Last.fm Playlist Converter" 
   - **App description**: "Personal playlist converter"
   - **Redirect URI**: `http://127.0.0.1:8000/callback`
4. Copy your **Client ID** and **Client Secret**

## Step 2: Install & Setup

```bash
# Install dependencies
pip3 install -r requirements.txt

# Interactive setup (recommended)
python3 main.py setup
```

Or manually create a `.env` file:
```env
LASTFM_API_KEY=your_lastfm_api_key
SPOTIFY_CLIENT_ID=your_spotify_client_id  
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8000/callback
```

## Step 3: Test Connection

```bash
# Test Last.fm only (no Spotify needed)
python3 test_lastfm.py

# Check user info
python3 main.py info YOUR_LASTFM_USERNAME
```

## Step 4: Create Your First Playlist

```bash
# Preview your top tracks first
python3 main.py top YOUR_USERNAME --preview

# Create playlist from your top tracks
python3 main.py top YOUR_USERNAME

# Create from recent tracks
python3 main.py recent YOUR_USERNAME

# Create from loved tracks  
python3 main.py loved YOUR_USERNAME
```

## Popular Commands

```bash
# Top tracks from last 3 months, 50 songs
python3 main.py top YOUR_USERNAME --period 3month --limit 50

# Private playlist with custom name
python3 main.py top YOUR_USERNAME --private --name "My Favorites"

# Recent 30 tracks
python3 main.py recent YOUR_USERNAME --limit 30
```

## Need Help?

```bash
# See all commands
python3 main.py --help

# Get help for specific command
python3 main.py top --help

# List time periods
python3 main.py periods
```

## Troubleshooting

**"No tracks found"** → Check your Last.fm username is correct and public

**"Authentication failed"** → Verify your API credentials in `.env` file

**Low match rate** → Normal for niche music, tool will still create playlist with found tracks

---

🎵 **That's it!** Your Last.fm data is now a Spotify playlist! 