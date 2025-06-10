# LastFM to Spotify Web Interface

This web interface allows users to easily import their LastFM listening history to Spotify playlists.

## Features

- Import top tracks (based on different time periods)
- Import recently played tracks
- Import loved tracks
- Select the number of tracks to import
- View LastFM user profile information
- Live import progress tracking

## Setup and Running

1. Make sure you have completed the API setup as described in the main README.md
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the web interface:
   ```bash
   python app.py
   ```

4. Open your browser and navigate to:
   ```
   http://127.0.0.1:8000
   ```

## Usage

1. Enter your LastFM username and click "Check User" to verify your account
2. Select the import type (Top Tracks, Recent Tracks, or Loved Tracks)
3. If importing Top Tracks, select the time period
4. Choose the number of tracks to import using the slider
5. Click "Start Import" to begin the process
6. The page will show live progress updates
7. When complete, click the "Open Playlist" button to view your new Spotify playlist

## Requirements

- Python 3.6+
- Valid LastFM API Key
- Valid Spotify API credentials (Client ID and Client Secret) 