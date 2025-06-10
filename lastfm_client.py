import requests
import time
from typing import List, Dict, Optional
from config import LASTFM_API_KEY, LASTFM_BASE_URL, RATE_LIMIT_DELAY


class LastFmClient:
    """Client for interacting with Last.fm API"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or LASTFM_API_KEY
        self.base_url = LASTFM_BASE_URL
        self.session = requests.Session()
    
    def _make_request(self, method: str, params: Dict) -> Dict:
        """Make a request to Last.fm API with rate limiting"""
        default_params = {
            'api_key': self.api_key,
            'method': method,
            'format': 'json'
        }
        default_params.update(params)
        
        try:
            time.sleep(RATE_LIMIT_DELAY)  # Rate limiting
            response = self.session.get(self.base_url, params=default_params)
            response.raise_for_status()
            data = response.json()
            
            if 'error' in data:
                raise Exception(f"Last.fm API error: {data['message']}")
            
            return data
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {str(e)}")
    
    def get_user_top_tracks(self, username: str, period: str = 'overall', 
                           limit: int = 50, page: int = 1) -> List[Dict]:
        """Get user's top tracks for a given time period"""
        params = {
            'user': username,
            'period': period,
            'limit': limit,
            'page': page
        }
        
        data = self._make_request('user.gettoptracks', params)
        
        if 'toptracks' not in data or 'track' not in data['toptracks']:
            return []
        
        tracks = data['toptracks']['track']
        # Handle case where only one track is returned (not in a list)
        if isinstance(tracks, dict):
            tracks = [tracks]
        
        return tracks
    
    def get_user_recent_tracks(self, username: str, limit: int = 50, 
                              page: int = 1, from_timestamp: int = None) -> List[Dict]:
        """Get user's recent tracks"""
        params = {
            'user': username,
            'limit': limit,
            'page': page
        }
        
        if from_timestamp:
            params['from'] = from_timestamp
        
        data = self._make_request('user.getrecenttracks', params)
        
        if 'recenttracks' not in data or 'track' not in data['recenttracks']:
            return []
        
        tracks = data['recenttracks']['track']
        if isinstance(tracks, dict):
            tracks = [tracks]
        
        return tracks
    
    def get_user_loved_tracks(self, username: str, limit: int = 50, 
                             page: int = 1) -> List[Dict]:
        """Get user's loved tracks"""
        params = {
            'user': username,
            'limit': limit,
            'page': page
        }
        
        data = self._make_request('user.getlovedtracks', params)
        
        if 'lovedtracks' not in data or 'track' not in data['lovedtracks']:
            return []
        
        tracks = data['lovedtracks']['track']
        if isinstance(tracks, dict):
            tracks = [tracks]
        
        return tracks
    
    def get_user_info(self, username: str) -> Dict:
        """Get basic user information"""
        params = {'user': username}
        data = self._make_request('user.getinfo', params)
        return data.get('user', {})
    
    def search_track(self, track: str, artist: str = None, limit: int = 10) -> List[Dict]:
        """Search for tracks"""
        query = track
        if artist:
            query = f"{artist} {track}"
        
        params = {
            'track': query,
            'limit': limit
        }
        
        data = self._make_request('track.search', params)
        
        if 'results' not in data or 'trackmatches' not in data['results']:
            return []
        
        tracks = data['results']['trackmatches'].get('track', [])
        if isinstance(tracks, dict):
            tracks = [tracks]
        
        return tracks
    
    def normalize_track_data(self, track: Dict) -> Dict:
        """Normalize track data from different Last.fm endpoints"""
        # Handle different response formats from different endpoints
        artist_name = ""
        track_name = ""
        playcount = 0
        
        if isinstance(track.get('artist'), dict):
            artist_name = track['artist'].get('name', '')
        elif isinstance(track.get('artist'), str):
            artist_name = track['artist']
        else:
            artist_name = track.get('artist', {}).get('#text', '') if isinstance(track.get('artist'), dict) else str(track.get('artist', ''))
        
        track_name = track.get('name', '')
        
        # Try different playcount fields
        playcount = (track.get('playcount') or 
                    track.get('count') or 
                    track.get('@attr', {}).get('rank', 0))
        
        try:
            playcount = int(playcount) if playcount else 0
        except (ValueError, TypeError):
            playcount = 0
        
        return {
            'artist': artist_name.strip(),
            'track': track_name.strip(),
            'playcount': playcount,
            'url': track.get('url', ''),
            'mbid': track.get('mbid', '')
        } 