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
# Set a strong secret key for the session
app.secret_key = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(32))
# Increase session timeout
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour

# Set up the application to work in a subdirectory if needed
if APP_BASE_PATH:
    app.config['APPLICATION_ROOT'] = APP_BASE_PATH
    
# Dictionary to store ongoing import jobs and their status
# Note: In production, this should be replaced with a database or Redis
import_jobs = {}

# Add a global dictionary to store progress
import_progress = {}

class ImportJob:
    def __init__(self, job_id, lastfm_username, import_type, limit, period=None, spotify_token=None):
        self.job_id = job_id
        self.lastfm_username = lastfm_username
        self.import_type = import_type
        self.limit = limit
        self.period = period
        self.status = "pending"
        self.progress = 0
        self.message = "Initializing..."
        self.result = None
        self.error = None
        self.spotify_token = spotify_token

def get_spotify_auth():
    """Get a SpotifyOAuth instance"""
    return SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope="playlist-modify-public playlist-modify-private user-read-private",
        show_dialog="true",  # Ensure lowercase
        cache_handler=None  # Don't use cache, always get fresh tokens
    )

def check_token():
    """Check if the Spotify token is valid and refresh if necessary"""
    if 'spotify_token' not in session:
        print("No Spotify token in session")
        return None
    
    # Check if token is expired and refresh if needed
    if session.get('spotify_token_expires_at', 0) < int(time.time()):
        try:
            print("Token expired, refreshing...")
            auth_manager = get_spotify_auth()
            refresh_token = session.get('spotify_refresh_token')
            
            if not refresh_token:
                print("No refresh token, authentication required")
                return None
                
            token_info = auth_manager.refresh_access_token(refresh_token)
            
            session['spotify_token'] = token_info['access_token']
            session['spotify_refresh_token'] = token_info.get('refresh_token', refresh_token)
            session['spotify_token_expires_at'] = token_info['expires_at']
            
            print(f"Token refreshed, new token: {token_info['access_token'][:15]}...")
        except Exception as e:
            print(f"Error refreshing token: {e}")
            # Token refresh failed, clear session
            session.pop('spotify_token', None)
            session.pop('spotify_refresh_token', None)
            session.pop('spotify_token_expires_at', None)
            return None
    
    token = session['spotify_token']
    print(f"Using token: {token[:15]}...")
    return token

def run_import_job(job):
    try:
        job.status = "running"
        job.message = "Initializing converter..."
        
        # Use the user's Spotify token
        if job.spotify_token:
            job.message = "Using authenticated Spotify account..."
            
            try:
                # Verify token by getting user info first
                spotify_client = SpotifyClient(access_token=job.spotify_token)
                spotify_user = spotify_client.get_current_user_info()
                job.message = f"Authenticated as Spotify user: {spotify_user['name']} ({spotify_user['id']})"
                
                # Now create the converter with the verified token
                converter = PlaylistConverter(spotify_access_token=job.spotify_token)
            except Exception as e:
                job.status = "failed"
                job.error = f"Error with Spotify authentication: {str(e)}"
                return
        else:
            job.status = "failed"
            job.error = "No Spotify authentication provided"
            return
        
        job.message = f"Fetching data for {job.lastfm_username}..."
        
        if job.import_type == "top":
            job.message = f"Converting top {job.limit} tracks for period: {job.period}..."
            result = converter.convert_top_tracks(
                job.lastfm_username, 
                period=job.period, 
                limit=job.limit
            )
        elif job.import_type == "recent":
            job.message = f"Converting recent {job.limit} tracks..."
            result = converter.convert_recent_tracks(
                job.lastfm_username, 
                limit=job.limit
            )
        elif job.import_type == "loved":
            job.message = f"Converting loved {job.limit} tracks..."
            result = converter.convert_loved_tracks(
                job.lastfm_username, 
                limit=job.limit
            )
        else:
            raise ValueError(f"Invalid import type: {job.import_type}")
        
        job.result = result
        job.status = "completed"
        job.progress = 100
        job.message = f"Import completed successfully! Playlist created in {result['playlist'].get('owner_name', 'user')}'s account."
    
    except Exception as e:
        job.status = "failed"
        job.error = str(e)
        job.message = f"Error: {str(e)}"


@app.route('/')
def index():
    # Make session permanent
    session.permanent = True
    
    # Generate a state value for OAuth security
    state = secrets.token_urlsafe(16)
    session['spotify_auth_state'] = state
    
    # Create the Spotify authorization URL
    auth_manager = get_spotify_auth()
    auth_url = auth_manager.get_authorize_url(state=state)
    
    # Ensure the URL is properly encoded and show_dialog is lowercase
    auth_url = auth_url.replace('True', 'true')
    
    return render_template('index.html', periods=LASTFM_PERIODS, spotify_auth_url=auth_url)


@app.route('/callback')
def callback():
    # Handle the callback from Spotify OAuth
    code = request.args.get('code')
    state = request.args.get('state')
    
    print(f"Callback received - Code: {code[:10]}..., State: {state}")
    print(f"Session state: {session.get('spotify_auth_state')}")
    print(f"Session data: {dict(session)}")
    
    if not code and request.args.get('error') == 'access_denied':
        print("Access denied by user")
        return redirect(url_for('index'))
    
    # Verify state to prevent CSRF attacks
    stored_state = session.get('spotify_auth_state')
    if not stored_state:
        print("No stored state found in session")
        print(f"Available session keys: {list(session.keys())}")
        return jsonify({"error": "No stored state found"}), 403
        
    if state != stored_state:
        print(f"State mismatch: received {state}, expected {stored_state}")
        return jsonify({"error": "State verification failed"}), 403
    
    # Exchange code for token
    auth_manager = get_spotify_auth()
    
    try:
        print("Exchanging code for token...")
        token_info = auth_manager.get_access_token(code, check_cache=False)
        print("Token received successfully")
        
        # Store token in session
        session['spotify_token'] = token_info['access_token']
        session['spotify_refresh_token'] = token_info.get('refresh_token')
        session['spotify_token_expires_at'] = token_info['expires_at']
        
        # Clear the state after successful authentication
        session.pop('spotify_auth_state', None)
        
        # Verify token works by getting user info
        print("Verifying token with user info...")
        spotify_client = SpotifyClient(access_token=token_info['access_token'])
        user_info = spotify_client.get_current_user_info()
        print(f"Authenticated as Spotify user: {user_info['name']} ({user_info['id']})")
        
        # Redirect back to the main page
        return redirect(url_for('index'))
    except Exception as e:
        print(f"Authentication error: {str(e)}")
        return jsonify({"error": f"Authentication error: {str(e)}"}), 500


@app.route('/check_auth')
def check_auth():
    # Check if user is authenticated with Spotify
    token = check_token()
    
    if token:
        try:
            # Get basic user info to confirm we're authenticated
            spotify_client = SpotifyClient(access_token=token)
            user_info = spotify_client.get_current_user_info()
            
            return jsonify({
                "authenticated": True,
                "user_info": user_info
            })
        except Exception as e:
            print(f"Error checking authentication: {str(e)}")
            # If there's an error, clear the session
            session.pop('spotify_token', None)
            session.pop('spotify_refresh_token', None)
            session.pop('spotify_token_expires_at', None)
            return jsonify({
                "authenticated": False,
                "error": str(e)
            })
    
    return jsonify({"authenticated": False})


@app.route('/start_import', methods=['POST'])
def start_import():
    # Check if user is authenticated with Spotify
    token = check_token()
    
    if not token:
        return jsonify({"error": "Not authenticated with Spotify. Please log in first."}), 401
    
    lastfm_username = request.form.get('lastfm_username')
    import_type = request.form.get('import_type', 'top')
    limit = int(request.form.get('limit', 50))
    period = request.form.get('period', 'overall')
    
    if not lastfm_username:
        return jsonify({"error": "LastFM username is required"}), 400
    
    # Create a unique ID for this job
    job_id = str(uuid.uuid4())
    
    # Create job object with the user's Spotify token
    job = ImportJob(
        job_id, 
        lastfm_username, 
        import_type, 
        limit, 
        period, 
        spotify_token=token
    )
    import_jobs[job_id] = job
    
    # Start a background thread to run the import
    thread = Thread(target=run_import_job, args=(job,))
    thread.daemon = True
    thread.start()
    
    return jsonify({"job_id": job_id})


@app.route('/job_status/<job_id>')
def job_status(job_id):
    job = import_jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    
    return jsonify({
        "status": job.status,
        "progress": job.progress,
        "message": job.message,
        "result": job.result,
        "error": job.error
    })


@app.route('/user_info/<lastfm_username>')
def user_info(lastfm_username):
    try:
        converter = PlaylistConverter()
        user_info = converter.get_user_info(lastfm_username)
        
        if not user_info:
            return jsonify({"error": "User not found"}), 404
        
        return jsonify(user_info)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/logout')
def logout():
    # Clear the session data
    session.pop('spotify_token', None)
    session.pop('spotify_refresh_token', None)
    session.pop('spotify_token_expires_at', None)
    session.pop('spotify_auth_state', None)
    
    return redirect(url_for('index'))


@app.route('/health')
def health_check():
    """Health check endpoint for Cloud Run"""
    return jsonify({"status": "healthy"})


@app.route('/progress/<job_id>')
def get_progress(job_id):
    if job_id in import_progress:
        return jsonify(import_progress[job_id])
    return jsonify({"error": "Job not found"}), 404


@app.route('/import_playlist', methods=['POST'])
def import_playlist():
    data = request.get_json()
    lastfm_username = data.get('lastfm_username')
    period = data.get('period', 'overall')
    limit = int(data.get('limit', 50))
    
    if not lastfm_username:
        return jsonify({"error": "Last.fm username is required"}), 400
    
    # Generate a unique job ID for this import
    job_id = str(uuid.uuid4())
    import_progress[job_id] = {"total": limit, "processed": 0, "status": "in_progress"}
    
    try:
        # Fetch tracks from Last.fm
        tracks = get_lastfm_tracks(lastfm_username, period, limit)
        if not tracks:
            import_progress[job_id]["status"] = "failed"
            import_progress[job_id]["error"] = "No tracks found"
            return jsonify({"error": "No tracks found"}), 404
        
        # Create a new playlist in Spotify
        playlist_name = f"Last.fm {period} for {lastfm_username}"
        playlist = create_spotify_playlist(playlist_name)
        
        # Add tracks to the playlist
        added_tracks = []
        for i, track in enumerate(tracks):
            spotify_track = search_spotify_track(track['name'], track['artist'])
            if spotify_track:
                added_tracks.append(spotify_track)
            # Update progress after each track
            import_progress[job_id]["processed"] = i + 1
        
        if added_tracks:
            add_tracks_to_playlist(playlist['id'], added_tracks)
            import_progress[job_id]["status"] = "completed"
            return jsonify({
                "message": f"Successfully imported {len(added_tracks)} tracks to Spotify",
                "playlist_url": playlist['external_urls']['spotify'],
                "job_id": job_id
            })
        else:
            import_progress[job_id]["status"] = "failed"
            import_progress[job_id]["error"] = "No tracks could be added to Spotify"
            return jsonify({"error": "No tracks could be added to Spotify"}), 404
    except Exception as e:
        import_progress[job_id]["status"] = "failed"
        import_progress[job_id]["error"] = str(e)
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    # For local development
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))
else:
    # For production
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True) 