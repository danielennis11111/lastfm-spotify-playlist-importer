# Deploying to vibe-coding.rocks

This guide outlines how to deploy the LastFM to Spotify Importer application to vibe-coding.rocks/lastfm-to-spotify-importer/.

## Prerequisites

1. Access to your web hosting for vibe-coding.rocks
2. Cyberduck or another FTP client to upload files
3. A server environment capable of running Python/Flask applications (web hosting with Python support)

## Configuration Steps

### 1. Update Spotify Developer Settings

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Select your application
3. Update the Redirect URI to: `https://vibe-coding.rocks/lastfm-to-spotify-importer/callback`
4. Save the changes

### 2. Prepare Environment Configuration

Create a `.env` file in the root directory with the following content:

```
# Environment
ENVIRONMENT=production

# Service URL - Your production domain
SERVICE_URL=https://vibe-coding.rocks

# Base path for application when deployed as a subdirectory
APP_BASE_PATH=/lastfm-to-spotify-importer

# LastFM API Credentials
LASTFM_API_KEY=YOUR_LASTFM_API_KEY

# Spotify API Credentials
SPOTIFY_CLIENT_ID=YOUR_SPOTIFY_CLIENT_ID
SPOTIFY_CLIENT_SECRET=YOUR_SPOTIFY_CLIENT_SECRET

# Flask Secret Key - Generate a strong one for production
FLASK_SECRET_KEY=your_secure_random_key_here

# Development settings (not used in production but kept for reference)
PORT=8000
```

Replace the placeholder values with your actual API keys and generate a secure random key for FLASK_SECRET_KEY.

### 3. Install Dependencies on Your Server

Make sure your server has Python 3.8+ installed along with pip. Then install the required dependencies:

```bash
pip install -r requirements.txt
```

### 4. Configure Web Server

#### Option A: WSGI Server (Recommended)

If your hosting supports WSGI applications (like uWSGI or Gunicorn):

1. Create a WSGI file (e.g., `wsgi.py`):

```python
from app import app as application

if __name__ == "__main__":
    application.run()
```

2. Configure your web server to use this WSGI file

#### Option B: CGI/FastCGI

If your hosting only supports CGI or FastCGI:

1. Create a CGI wrapper script according to your hosting provider's specifications
2. Point it to your Flask application

### 5. Upload Files

Using Cyberduck or your preferred FTP client:

1. Connect to your web hosting
2. Navigate to the directory where you want to deploy (should be accessible as `/lastfm-to-spotify-importer/` on your domain)
3. Upload all application files, maintaining the directory structure
4. Make sure to set correct permissions (typically 755 for directories and 644 for files)

### 6. Testing

After deployment:

1. Visit https://vibe-coding.rocks/lastfm-to-spotify-importer/
2. Test the Spotify authentication flow
3. Check the application logs for any errors

## Troubleshooting

If you encounter issues:

1. Check your web server logs for errors
2. Verify that the redirect URI in Spotify Developer Dashboard exactly matches your application URL
3. Ensure environment variables are properly loaded
4. Check that all required dependencies are installed

## Security Considerations

1. Ensure your `.env` file with sensitive API keys is not publicly accessible
2. Use HTTPS for all connections
3. Consider implementing rate limiting if your hosting plan has bandwidth restrictions 