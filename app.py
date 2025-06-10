#!/usr/bin/env python3

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
import uuid
import time
import secrets
from threading import Thread
from dotenv import load_dotenv
from playlist_converter import PlaylistConverter
from config import LASTFM_PERIODS, APP_BASE_PATH
from spotify_client import SpotifyClient
from spotipy.oauth2 import SpotifyOAuth
from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(32))

# Set up the application to work in a subdirectory if needed
if APP_BASE_PATH:
    app.config['APPLICATION_ROOT'] = APP_BASE_PATH

# Dictionary to store ongoing import jobs and their status
import_jobs = {}

def get_spotify_auth():
    """Get a SpotifyOAuth instance"""
    return SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope="playlist-modify-public playlist-modify-private user-read-private",
        show_dialog=True,
        cache_handler=None
    )

def check_token():
    """Check if the Spotify token is valid and refresh if necessary"""
    if 'spotify_token' not in session:
        return None
    
    # Check if token is expired and refresh if needed
    if session.get('spotify_token_expires_at', 0) < int(time.time()):
        try:
            auth_manager = get_spotify_auth()
            refresh_token = session.get('spotify_refresh_token')
            
            if not refresh_token:
                return None
                
            token_info = auth_manager.refresh_access_token(refresh_token)
            
            # Update session with new token info
            session['spotify_token'] = token_info['access_token']
            session['spotify_refresh_token'] = token_info.get('refresh_token', refresh_token)
            session['spotify_token_expires_at'] = token_info['expires_at']
            session.modified = True
            
        except Exception as e:
            session.clear()
            return None
    
    return session['spotify_token']

@app.route('/')
def index():
    """Render the main page"""
    # Generate a state value for OAuth security
    state = secrets.token_urlsafe(16)
    session['spotify_auth_state'] = state
    
    # Create the Spotify authorization URL
    auth_manager = get_spotify_auth()
    auth_url = auth_manager.get_authorize_url(state=state)
    
    # Check if user is already authenticated
    token = check_token()
    is_authenticated = bool(token)
    
    return render_template('index.html', 
                         auth_url=auth_url,
                         is_authenticated=is_authenticated)

@app.route('/callback')
def callback():
    """Handle the Spotify OAuth callback"""
    # Verify state parameter to prevent CSRF
    if request.args.get('state') != session.get('spotify_auth_state'):
        return redirect(url_for('index'))
    
    # Get the authorization code
    code = request.args.get('code')
    if not code:
        return redirect(url_for('index'))
    
    try:
        # Exchange code for tokens
        auth_manager = get_spotify_auth()
        token_info = auth_manager.get_access_token(code)
        
        # Store tokens in session
        session['spotify_token'] = token_info['access_token']
        session['spotify_refresh_token'] = token_info.get('refresh_token')
        session['spotify_token_expires_at'] = token_info['expires_at']
        
        # Get user info
        spotify_client = SpotifyClient(access_token=token_info['access_token'])
        user_info = spotify_client.get_current_user_info()
        
        # Store user info in session
        session['spotify_user_info'] = user_info
        session.modified = True
        
        return redirect(url_for('index'))
        
    except Exception as e:
        return redirect(url_for('index'))

@app.route('/check_auth')
def check_auth():
    """Check if the user is authenticated with Spotify"""
    token = check_token()
    if not token:
        return jsonify({'authenticated': False})
    
    user_info = session.get('spotify_user_info')
    if not user_info:
        try:
            spotify_client = SpotifyClient(access_token=token)
            user_info = spotify_client.get_current_user_info()
            session['spotify_user_info'] = user_info
            session.modified = True
        except Exception:
            return jsonify({'authenticated': False})
    
    return jsonify({
        'authenticated': True,
        'user_info': user_info
    })

@app.route('/import_playlist', methods=['POST'])
def import_playlist():
    """Start the import process"""
    data = request.get_json()
    lastfm_username = data.get('lastfm_username')
    track_limit = int(data.get('limit', 50))
    
    if not lastfm_username:
        return jsonify({'error': 'LastFM username is required'}), 400
    
    # Check if user is authenticated
    token = check_token()
    if not token:
        return jsonify({'error': 'Not authenticated with Spotify'}), 401
    
    # Create a unique job ID
    job_id = str(uuid.uuid4())
    
    # Initialize job status
    import_jobs[job_id] = {
        'status': 'pending',
        'progress': 0,
        'message': 'Initializing...',
        'start_time': time.time()
    }
    
    # Start the import process in a background thread
    thread = Thread(target=process_import, args=(job_id, lastfm_username, track_limit))
    thread.start()
    
    return jsonify({'job_id': job_id})

def process_import(job_id: str, lastfm_username: str, track_limit: int):
    """Process the import in a background thread"""
    try:
        # Get the user's token
        token = check_token()
        if not token:
            import_jobs[job_id]['status'] = 'failed'
            import_jobs[job_id]['error'] = 'Not authenticated with Spotify'
            return
        
        # Create the converter with the user's token
        converter = PlaylistConverter(spotify_access_token=token)
        
        # Update job status
        import_jobs[job_id]['status'] = 'running'
        import_jobs[job_id]['message'] = f'Fetching data for {lastfm_username}...'
        
        # Convert the tracks
        result = converter.convert_top_tracks(
            lastfm_username,
            period='overall',
            limit=track_limit
        )
        
        # Update job status
        import_jobs[job_id]['status'] = 'completed'
        import_jobs[job_id]['progress'] = 100
        import_jobs[job_id]['message'] = 'Import completed successfully!'
        import_jobs[job_id]['result'] = result
        
    except Exception as e:
        import_jobs[job_id]['status'] = 'failed'
        import_jobs[job_id]['error'] = str(e)

@app.route('/check_status/<job_id>')
def check_status(job_id):
    """Check the status of an import job"""
    if job_id not in import_jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job = import_jobs[job_id]
    return jsonify({
        'status': job['status'],
        'progress': job['progress'],
        'message': job['message'],
        'error': job.get('error'),
        'result': job.get('result')
    })

@app.route('/logout')
def logout():
    """Clear the session data"""
    session.clear()
    return redirect(url_for('index'))

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    # For local development
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))
else:
    # For production
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True) 