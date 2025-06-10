import spotipy
from spotipy.oauth2 import SpotifyOAuth
from typing import List, Dict, Optional, Tuple
import time
import re
from config import (
    SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI,
    MAX_TRACKS_PER_PLAYLIST, RATE_LIMIT_DELAY
)


class SpotifyClient:
    """Client for interacting with Spotify API"""
    
    def __init__(self, client_id: str = None, client_secret: str = None, 
                 redirect_uri: str = None, access_token: str = None):
        self.client_id = client_id or SPOTIFY_CLIENT_ID
        self.client_secret = client_secret or SPOTIFY_CLIENT_SECRET
        self.redirect_uri = redirect_uri or SPOTIFY_REDIRECT_URI
        
        if access_token:
            # Use provided access token directly (don't use auth_manager)
            print(f"Initializing Spotify client with provided token: {access_token[:15]}...")
            self.sp = spotipy.Spotify(auth=access_token)
            self.auth_method = "token"
        else:
            # Set up auth manager for OAuth flow
            self.auth_manager = SpotifyOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope="user-read-private playlist-modify-public playlist-modify-private"
            )
            
            # Create authenticated Spotify client
            self.sp = spotipy.Spotify(auth_manager=self.auth_manager)
            self.auth_method = "oauth"
        
        # Test the connection to make sure it's working
        try:
            self.current_user_info = self.sp.current_user()
            print(f"✅ Successfully connected to Spotify API as: {self.current_user_info['display_name']} ({self.current_user_info['id']})")
        except Exception as e:
            raise Exception(f"Failed to connect to Spotify API: {e}")
    
    def _truncate_search_query(self, artist: str, track: str) -> Tuple[str, str]:
        """Truncate search query to fit within Spotify's 250 character limit"""
        # Start with just the artist name
        query = f"artist:{artist}"
        
        # If adding the track name would exceed the limit, truncate the track name
        max_track_length = 250 - len(query) - 10  # Leave some room for "track:" and spaces
        if len(track) > max_track_length:
            # Try to truncate at a word boundary
            truncated_track = track[:max_track_length].rsplit(' ', 1)[0]
            return artist, truncated_track
        
        return artist, track

    def search_track(self, artist: str, track: str, limit: int = 10) -> List[Dict]:
        """Search for a track on Spotify"""
        try:
            # Truncate the search query if needed
            artist, track = self._truncate_search_query(artist, track)
            
            # Construct the search query
            query = f"artist:{artist} track:{track}"
            
            # Search for the track
            results = self.sp.search(query, limit=limit, type='track')
            
            if not results['tracks']['items']:
                return []
            
            return results['tracks']['items']
        except Exception as e:
            print(f"Error searching for track: {e}")
            return []
    
    def search_track_fuzzy(self, artist: str, track: str) -> List[Dict]:
        """Perform a less strict search for tracks on Spotify"""
        # Remove special characters and some common modifiers
        artist = re.sub(r'[^\w\s]', '', artist)
        track = re.sub(r'[^\w\s]', '', track)
        
        # Remove common additions like "(feat. XYZ)" or "[remix]"
        track = re.sub(r'\([^\)]*\)|\[[^\]]*\]', '', track)
        
        query = f"{artist} {track}"
        results = self.sp.search(q=query, type='track', limit=10)
        
        return results.get('tracks', {}).get('items', [])
    
    def find_best_match(self, lastfm_track: Dict, spotify_results: List[Dict]) -> Optional[Dict]:
        """Find the best matching track from Spotify search results"""
        if not spotify_results:
            return None
        
        lastfm_artist = lastfm_track['artist'].lower()
        lastfm_track_name = lastfm_track['track'].lower()
        
        # Try to find an exact match first
        for result in spotify_results:
            spotify_artist = result['artists'][0]['name'].lower()
            spotify_track = result['name'].lower()
            
            # Exact match
            if spotify_artist == lastfm_artist and spotify_track == lastfm_track_name:
                return {
                    'id': result['id'],
                    'uri': result['uri'],
                    'name': result['name'],
                    'artist': result['artists'][0]['name'],
                    'album': result['album']['name'],
                    'popularity': result['popularity'],
                    'url': result['external_urls']['spotify']
                }
        
        # If no exact match, try fuzzy matching
        for result in spotify_results:
            spotify_artist = result['artists'][0]['name'].lower()
            spotify_track = result['name'].lower()
            
            # Check if artist name is similar and track name is similar
            if self._similar_strings(spotify_artist, lastfm_artist) and \
               self._similar_strings(spotify_track, lastfm_track_name):
                return {
                    'id': result['id'],
                    'uri': result['uri'],
                    'name': result['name'],
                    'artist': result['artists'][0]['name'],
                    'album': result['album']['name'],
                    'popularity': result['popularity'],
                    'url': result['external_urls']['spotify']
                }
        
        # If still no match, just take the first result
        result = spotify_results[0]
        return {
            'id': result['id'],
            'uri': result['uri'],
            'name': result['name'],
            'artist': result['artists'][0]['name'],
            'album': result['album']['name'],
            'popularity': result['popularity'],
            'url': result['external_urls']['spotify']
        }
    
    def _similar_strings(self, str1: str, str2: str) -> bool:
        """Simple check for string similarity"""
        # Clean strings for comparison
        s1 = re.sub(r'[^\w\s]', '', str1.lower()).strip()
        s2 = re.sub(r'[^\w\s]', '', str2.lower()).strip()
        
        # Check if one is contained in the other
        return s1 in s2 or s2 in s1
    
    def create_playlist(self, name: str, description: str = "", public: bool = True) -> Dict:
        """Create a new Spotify playlist"""
        # Make sure we use the current authenticated user
        user_id = self.current_user_info['id']
        print(f"Creating playlist in account: {user_id} ({self.current_user_info['display_name']})")
        
        try:
            # Force using the token approach to create playlist in the user's account
            if self.auth_method == "token":
                # Re-check who we're authenticated as
                current_user = self.sp.current_user()
                print(f"Verified current user: {current_user['id']} ({current_user['display_name']})")
                
                # Use specific endpoint for this user
                playlist = self.sp.user_playlist_create(
                    user=current_user['id'],
                    name=name,
                    public=public,
                    description=description
                )
            else:
                playlist = self.sp.user_playlist_create(
                    user=user_id,
                    name=name,
                    public=public,
                    description=description
                )
            
            print(f"Playlist created successfully with ID: {playlist['id']}")
            print(f"Playlist owner: {playlist['owner']['id']} ({playlist['owner']['display_name']})")
            
            return {
                'id': playlist['id'],
                'url': playlist['external_urls']['spotify'],
                'name': playlist['name'],
                'public': playlist['public'],
                'tracks_url': playlist['tracks']['href'],
                'owner': playlist['owner']['id'],
                'owner_name': playlist['owner']['display_name']
            }
        except Exception as e:
            print(f"Error creating playlist: {str(e)}")
            raise Exception(f"Failed to create playlist: {e}")
    
    def add_tracks_to_playlist(self, playlist_id: str, track_uris: List[str]) -> bool:
        """Add tracks to a Spotify playlist"""
        try:
            # Get playlist info to double-check ownership
            playlist_info = self.sp.playlist(playlist_id)
            print(f"Adding tracks to playlist owned by: {playlist_info['owner']['id']} ({playlist_info['owner']['display_name']})")
            
            # Spotify API can only handle 100 tracks at a time
            chunk_size = 100
            for i in range(0, len(track_uris), chunk_size):
                chunk = track_uris[i:i + chunk_size]
                self.sp.playlist_add_items(playlist_id, chunk)
                print(f"Added {len(chunk)} tracks (chunk {i//chunk_size + 1})")
                
                # Be nice to the API
                if i + chunk_size < len(track_uris):
                    time.sleep(1)
            
            return True
        except Exception as e:
            print(f"Error adding tracks: {str(e)}")
            raise Exception(f"Failed to add tracks to playlist: {e}")
    
    def get_audio_features(self, track_id: str) -> Dict:
        """Get audio features for a track"""
        try:
            return self.sp.audio_features(track_id)[0]
        except Exception as e:
            print(f"Failed to get audio features: {e}")
            return {}
    
    def get_current_user_info(self) -> Dict:
        """Get information about the current authenticated user"""
        try:
            user = self.sp.current_user()
            return {
                'id': user['id'],
                'name': user['display_name'],
                'email': user.get('email', 'N/A'),
                'image': user['images'][0]['url'] if user.get('images') and len(user['images']) > 0 else None,
                'url': user['external_urls']['spotify']
            }
        except Exception as e:
            raise Exception(f"Failed to get current user info: {e}") 