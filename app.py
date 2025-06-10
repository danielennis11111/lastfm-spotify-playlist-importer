#!/usr/bin/env python3

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, Response
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
from job_manager import JobManager
import json

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(32))

# Set up the application to work in a subdirectory if needed
if APP_BASE_PATH:
    app.config['APPLICATION_ROOT'] = APP_BASE_PATH

# Initialize job manager
job_manager = JobManager()

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
    """Check if the current token is valid and refresh if needed"""
    if 'token_info' not in session:
        return None
    
    token_info = session['token_info']
    if not token_info:
        return None
    
    # Check if token is expired
    if time.time() > token_info['expires_at']:
        auth_manager = get_spotify_auth()
        token_info = auth_manager.refresh_access_token(token_info['refresh_token'])
        session['token_info'] = token_info
    
    return token_info['access_token']

@app.route('/')
def index():
    """Render the main page"""
    # Generate a random state value for OAuth security
    state = secrets.token_urlsafe(16)
    session['state'] = state
    
    # Get the authorization URL
    auth_manager = get_spotify_auth()
    auth_url = auth_manager.get_authorize_url(state=state)
    
    # Check if user is already authenticated
    token = check_token()
    is_authenticated = token is not None
    
    return render_template('index.html', 
                         auth_url=auth_url,
                         is_authenticated=is_authenticated)

@app.route('/callback')
def callback():
    """Handle the Spotify OAuth callback"""
    # Verify state parameter
    if request.args.get('state') != session.get('state'):
        return redirect(url_for('index'))
    
    # Get the authorization code
    code = request.args.get('code')
    if not code:
        return redirect(url_for('index'))
    
    # Exchange code for token
    auth_manager = get_spotify_auth()
    token_info = auth_manager.get_access_token(code)
    
    # Store token in session
    session['token_info'] = token_info
    
    # Get user info
    sp = SpotifyClient(access_token=token_info['access_token'])
    user_info = sp.get_current_user_info()
    session['user_info'] = user_info
    
    return redirect(url_for('index'))

@app.route('/check_auth')
def check_auth():
    """Check if the user is authenticated with Spotify"""
    token = check_token()
    if not token:
        return jsonify({'authenticated': False})
    
    user_info = session.get('user_info')
    if not user_info:
        sp = SpotifyClient(access_token=token)
        user_info = sp.get_current_user_info()
        session['user_info'] = user_info
    
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
    
    user_info = session.get('user_info')
    if not user_info:
        return jsonify({'error': 'User info not found'}), 401
    
    # Create a new job
    job_id = job_manager.create_job(
        user_id=user_info['id'],
        job_type='import_playlist',
        params={
            'lastfm_username': lastfm_username,
            'track_limit': track_limit
        }
    )
    
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
            job_manager.update_job(job_id, 
                status='failed',
                error='Not authenticated with Spotify'
            )
            return
        
        # Create the converter with the user's token
        converter = PlaylistConverter(spotify_access_token=token)
        
        # Update job status
        job_manager.update_job(job_id,
            status='running',
            message=f'Fetching data for {lastfm_username}...'
        )
        
        # Convert the tracks
        result = converter.convert_top_tracks(
            lastfm_username,
            period='overall',
            limit=track_limit
        )
        
        # Update job status
        job_manager.update_job(job_id,
            status='completed',
            progress=100,
            message='Import completed successfully!',
            result=result
        )
        
    except Exception as e:
        job_manager.update_job(job_id,
            status='failed',
            error=str(e)
        )

@app.route('/check_status/<job_id>')
def check_status(job_id):
    """Check the status of an import job"""
    job = job_manager.get_job(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify({
        'status': job['status'],
        'progress': job['progress'],
        'message': job['message'],
        'error': job.get('error'),
        'result': job.get('result')
    })

@app.route('/job_history')
def job_history():
    """Get the user's job history"""
    # Check if user is authenticated
    token = check_token()
    if not token:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_info = session.get('user_info')
    if not user_info:
        return jsonify({'error': 'User info not found'}), 401
    
    # Get user's jobs
    jobs = job_manager.get_user_jobs(user_info['id'])
    
    return jsonify({
        'jobs': jobs
    })

@app.route('/job_status_stream/<job_id>')
def job_status_stream(job_id):
    """Stream job status updates using Server-Sent Events"""
    def generate():
        while True:
            job = job_manager.get_job(job_id)
            if not job:
                yield f"data: {json.dumps({'error': 'Job not found'})}\n\n"
                break
            
            yield f"data: {json.dumps(job)}\n\n"
            
            if job['status'] in ['completed', 'failed']:
                break
            
            time.sleep(1)
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True) 