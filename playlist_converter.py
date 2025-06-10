from typing import List, Dict, Tuple, Optional, Any
from tqdm import tqdm
import time
from datetime import datetime
import requests
import logging

from lastfm_client import LastFmClient
from spotify_client import SpotifyClient
from config import MAX_TRACKS_PER_PLAYLIST, LASTFM_PERIODS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PlaylistConverter:
    """Main class for converting Last.fm data to Spotify playlists"""
    
    def __init__(self, lastfm_api_key: str = None, spotify_client_id: str = None, 
                 spotify_client_secret: str = None, spotify_redirect_uri: str = None,
                 spotify_access_token: str = None):
        
        print("Initializing Last.fm client...")
        self.lastfm = LastFmClient(lastfm_api_key)
        
        print("Initializing Spotify client...")
        if spotify_access_token:
            # Use provided access token
            print(f"Using provided Spotify access token: {spotify_access_token[:10]}...")
            self.spotify = SpotifyClient(access_token=spotify_access_token)
            # Get current user info to verify
            user_info = self.spotify.get_current_user_info()
            print(f"Authenticated as Spotify user: {user_info['name']} (ID: {user_info['id']})")
        else:
            # Use default OAuth flow
            print("Using default OAuth flow for Spotify")
            self.spotify = SpotifyClient(
                spotify_client_id, 
                spotify_client_secret, 
                spotify_redirect_uri
            )
        
        print("✅ Initialization complete!")
    
    def convert_top_tracks(self, username: str, period: str = 'overall', limit: int = 50) -> Dict[str, Any]:
        """Convert Last.fm top tracks to Spotify playlist with better error handling"""
        try:
            # Get tracks from Last.fm
            tracks = self.get_lastfm_tracks(username, 'top', period, limit)
            if not tracks:
                raise Exception("No tracks found")
            
            # Search tracks on Spotify with progress tracking
            spotify_tracks = []
            failed_tracks = []
            
            for i, track in enumerate(tracks):
                try:
                    spotify_track = self.search_spotify_track(track)
                    if spotify_track:
                        spotify_tracks.append(spotify_track)
                    else:
                        failed_tracks.append(track)
                except Exception as e:
                    logger.error(f"Error processing track {track.get('name', 'unknown')}: {str(e)}")
                    failed_tracks.append(track)
                    continue
            
            if not spotify_tracks:
                raise Exception("No matching tracks found on Spotify")
            
            # Create playlist
            playlist = self.create_spotify_playlist(
                f"Last.fm Top Tracks - {period}",
                spotify_tracks
            )
            
            return {
                'playlist': playlist,
                'total_tracks': len(tracks),
                'matched_tracks': len(spotify_tracks),
                'failed_tracks': len(failed_tracks),
                'failed_track_details': failed_tracks
            }
            
        except Exception as e:
            logger.error(f"Error converting top tracks: {str(e)}")
            raise
    
    def convert_recent_tracks(self, username: str, limit: int = 50) -> Dict[str, Any]:
        """Convert Last.fm recent tracks to Spotify playlist with better error handling"""
        try:
            # Get tracks from Last.fm
            tracks = self.get_lastfm_tracks(username, 'recent', limit=limit)
            if not tracks:
                raise Exception("No tracks found")
            
            # Search tracks on Spotify with progress tracking
            spotify_tracks = []
            failed_tracks = []
            
            for i, track in enumerate(tracks):
                try:
                    spotify_track = self.search_spotify_track(track)
                    if spotify_track:
                        spotify_tracks.append(spotify_track)
                    else:
                        failed_tracks.append(track)
                except Exception as e:
                    logger.error(f"Error processing track {track.get('name', 'unknown')}: {str(e)}")
                    failed_tracks.append(track)
                    continue
            
            if not spotify_tracks:
                raise Exception("No matching tracks found on Spotify")
            
            # Create playlist
            playlist = self.create_spotify_playlist(
                f"Last.fm Recent Tracks",
                spotify_tracks
            )
            
            return {
                'playlist': playlist,
                'total_tracks': len(tracks),
                'matched_tracks': len(spotify_tracks),
                'failed_tracks': len(failed_tracks),
                'failed_track_details': failed_tracks
            }
            
        except Exception as e:
            logger.error(f"Error converting recent tracks: {str(e)}")
            raise
    
    def convert_loved_tracks(self, username: str, limit: int = 50) -> Dict[str, Any]:
        """Convert Last.fm loved tracks to Spotify playlist with better error handling"""
        try:
            # Get tracks from Last.fm
            tracks = self.get_lastfm_tracks(username, 'loved', limit=limit)
            if not tracks:
                raise Exception("No tracks found")
            
            # Search tracks on Spotify with progress tracking
            spotify_tracks = []
            failed_tracks = []
            
            for i, track in enumerate(tracks):
                try:
                    spotify_track = self.search_spotify_track(track)
                    if spotify_track:
                        spotify_tracks.append(spotify_track)
                    else:
                        failed_tracks.append(track)
                except Exception as e:
                    logger.error(f"Error processing track {track.get('name', 'unknown')}: {str(e)}")
                    failed_tracks.append(track)
                    continue
            
            if not spotify_tracks:
                raise Exception("No matching tracks found on Spotify")
            
            # Create playlist
            playlist = self.create_spotify_playlist(
                f"Last.fm Loved Tracks",
                spotify_tracks
            )
            
            return {
                'playlist': playlist,
                'total_tracks': len(tracks),
                'matched_tracks': len(spotify_tracks),
                'failed_tracks': len(failed_tracks),
                'failed_track_details': failed_tracks
            }
            
        except Exception as e:
            logger.error(f"Error converting loved tracks: {str(e)}")
            raise
    
    def _fetch_all_tracks(self, fetch_func, username: str, limit: int, **kwargs) -> List[Dict]:
        """Fetch all tracks using pagination"""
        all_tracks = []
        page = 1
        tracks_per_page = min(50, limit)  # Last.fm max is 50 per page
        
        with tqdm(desc="Fetching tracks", unit="tracks") as pbar:
            while len(all_tracks) < limit:
                remaining = limit - len(all_tracks)
                current_limit = min(tracks_per_page, remaining)
                
                tracks = fetch_func(username, limit=current_limit, page=page, **kwargs)
                
                if not tracks:
                    break
                
                # Normalize track data
                normalized_tracks = [self.lastfm.normalize_track_data(track) for track in tracks]
                all_tracks.extend(normalized_tracks)
                
                pbar.update(len(normalized_tracks))
                page += 1
                
                # Break if we got fewer tracks than requested (end of data)
                if len(tracks) < current_limit:
                    break
        
        return all_tracks[:limit]
    
    def _create_spotify_playlist(self, lastfm_tracks: List[Dict], name: str, 
                                description: str, public: bool) -> Dict:
        """Create Spotify playlist from Last.fm tracks"""
        
        print(f"\n🔍 Searching Spotify for {len(lastfm_tracks)} tracks...")
        
        # Verify Spotify user again
        user_info = self.spotify.get_current_user_info()
        print(f"Creating playlist as Spotify user: {user_info['name']} (ID: {user_info['id']})")
        
        # Search for tracks on Spotify
        matched_tracks = []
        unmatched_tracks = []
        
        with tqdm(lastfm_tracks, desc="Searching tracks") as pbar:
            for track in pbar:
                pbar.set_postfix_str(f"{track['artist']} - {track['track']}")
                
                # Search on Spotify
                spotify_results = self.spotify.search_track(track['artist'], track['track'])
                
                if not spotify_results:
                    # Try fuzzy search
                    spotify_results = self.spotify.search_track_fuzzy(track['artist'], track['track'])
                
                best_match = self.spotify.find_best_match(track, spotify_results)
                
                if best_match:
                    matched_tracks.append({
                        'lastfm': track,
                        'spotify': best_match
                    })
                else:
                    unmatched_tracks.append(track)
        
        match_rate = len(matched_tracks) / len(lastfm_tracks) * 100 if lastfm_tracks else 0
        print(f"\n📊 Match Results:")
        print(f"   ✅ Found: {len(matched_tracks)} tracks ({match_rate:.1f}%)")
        print(f"   ❌ Not found: {len(unmatched_tracks)} tracks")
        
        if not matched_tracks:
            raise Exception("No tracks could be found on Spotify")
        
        # Create playlist
        print(f"\n📝 Creating playlist: {name}")
        playlist = self.spotify.create_playlist(name, description, public)
        
        # Log playlist details
        print(f"Created playlist:")
        print(f"   ID: {playlist['id']}")
        print(f"   Owner: {playlist.get('owner', 'unknown')}")
        print(f"   URL: {playlist['url']}")
        
        # Add tracks to playlist
        track_uris = [match['spotify']['uri'] for match in matched_tracks]
        
        # Limit tracks per playlist
        if len(track_uris) > MAX_TRACKS_PER_PLAYLIST:
            print(f"⚠️ Limiting playlist to {MAX_TRACKS_PER_PLAYLIST} tracks")
            track_uris = track_uris[:MAX_TRACKS_PER_PLAYLIST]
        
        print(f"🎵 Adding {len(track_uris)} tracks to playlist...")
        success = self.spotify.add_tracks_to_playlist(playlist['id'], track_uris)
        
        if not success:
            raise Exception("Failed to add tracks to playlist")
        
        # Prepare summary
        result = {
            'playlist': playlist,
            'total_lastfm_tracks': len(lastfm_tracks),
            'matched_tracks': len(matched_tracks),
            'added_tracks': len(track_uris),
            'unmatched_tracks': unmatched_tracks,
            'match_rate': match_rate,
            'created_at': datetime.now().isoformat()
        }
        
        print(f"\n✅ Playlist created successfully!")
        print(f"   🔗 URL: {playlist['url']}")
        print(f"   📊 Added {len(track_uris)} out of {len(lastfm_tracks)} tracks")
        
        return result
    
    def get_user_info(self, lastfm_username: str) -> Dict:
        """Get Last.fm user information"""
        return self.lastfm.get_user_info(lastfm_username)
    
    def list_available_periods(self) -> List[str]:
        """List available time periods for top tracks"""
        return list(LASTFM_PERIODS.keys())
    
    def preview_tracks(self, lastfm_username: str, data_type: str = 'top', 
                      period: str = 'overall', limit: int = 10) -> List[Dict]:
        """Preview tracks that would be imported"""
        
        if data_type == 'top':
            tracks = self.lastfm.get_user_top_tracks(lastfm_username, period, limit)
        elif data_type == 'recent':
            tracks = self.lastfm.get_user_recent_tracks(lastfm_username, limit)
        elif data_type == 'loved':
            tracks = self.lastfm.get_user_loved_tracks(lastfm_username, limit)
        else:
            raise ValueError("data_type must be 'top', 'recent', or 'loved'")
        
        return [self.lastfm.normalize_track_data(track) for track in tracks]

    def get_lastfm_tracks(self, username: str, import_type: str, period: str, limit: int) -> List[Dict]:
        """Get tracks from Last.fm with rate limiting and error handling"""
        try:
            params = {
                'method': f'user.get{import_type.title()}',
                'user': username,
                'api_key': self.lastfm_api_key,
                'format': 'json',
                'limit': limit
            }
            
            if import_type != 'loved':
                params['period'] = period
                
            response = requests.get(self.lastfm_base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            tracks = []
            
            if import_type == 'loved':
                tracks = data['lovedtracks']['track']
            else:
                tracks = data['toptracks']['track']
                
            # Truncate track names to 200 characters
            for track in tracks:
                track['name'] = track['name'][:200]
                track['artist']['name'] = track['artist']['name'][:200]
                
            return tracks
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching Last.fm tracks: {str(e)}")
            raise Exception(f"Failed to fetch tracks from Last.fm: {str(e)}")
            
    def search_spotify_track(self, track: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Search for a track on Spotify with better error handling and retries"""
        try:
            # Truncate track name to 200 characters to avoid API limits
            track_name = track['name'][:200]
            artist_name = track['artist']
            
            # Try exact match first
            query = f"track:{track_name} artist:{artist_name}"
            results = self.spotify.search(query, limit=1, type='track')
            
            if results['tracks']['items']:
                return results['tracks']['items'][0]
            
            # If no exact match, try with just the track name
            results = self.spotify.search(track_name, limit=1, type='track')
            if results['tracks']['items']:
                return results['tracks']['items'][0]
            
            logger.warning(f"No match found for track: {track_name} by {artist_name}")
            return None
            
        except Exception as e:
            logger.error(f"Error searching for track {track.get('name', 'unknown')}: {str(e)}")
            return None

    def create_spotify_playlist(self, token: str, name: str, tracks: List[Dict]) -> Dict:
        """Create a Spotify playlist with error handling"""
        try:
            headers = {
                'Authorization': f"Bearer {token}",
                'Content-Type': 'application/json'
            }
            
            # Get user profile
            response = requests.get(f"{self.spotify_base_url}/me", headers=headers)
            response.raise_for_status()
            user_id = response.json()['id']
            
            # Create playlist
            response = requests.post(
                f"{self.spotify_base_url}/users/{user_id}/playlists",
                headers=headers,
                json={'name': name, 'public': False}
            )
            response.raise_for_status()
            playlist = response.json()
            
            # Add tracks in chunks of 100 (Spotify's limit)
            track_uris = [track['uri'] for track in tracks]
            for i in range(0, len(track_uris), 100):
                chunk = track_uris[i:i + 100]
                response = requests.post(
                    f"{self.spotify_base_url}/playlists/{playlist['id']}/tracks",
                    headers=headers,
                    json={'uris': chunk}
                )
                response.raise_for_status()
                
            return playlist
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating Spotify playlist: {str(e)}")
            raise Exception(f"Failed to create Spotify playlist: {str(e)}") 