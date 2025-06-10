from typing import List, Dict, Tuple, Optional
from tqdm import tqdm
import time
from datetime import datetime

from lastfm_client import LastFmClient
from spotify_client import SpotifyClient
from config import MAX_TRACKS_PER_PLAYLIST, LASTFM_PERIODS


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
    
    def convert_top_tracks(self, lastfm_username: str, period: str = 'overall', 
                          limit: int = 50, playlist_name: str = None, 
                          playlist_description: str = None, public: bool = True) -> Dict:
        """Convert Last.fm top tracks to a Spotify playlist"""
        
        if period not in LASTFM_PERIODS:
            raise ValueError(f"Invalid period. Choose from: {list(LASTFM_PERIODS.keys())}")
        
        print(f"\n🎵 Fetching top tracks for {lastfm_username} ({period})...")
        
        # Fetch Last.fm data
        lastfm_tracks = self._fetch_all_tracks(
            self.lastfm.get_user_top_tracks, 
            lastfm_username, 
            period=period, 
            limit=limit
        )
        
        if not lastfm_tracks:
            raise Exception("No tracks found on Last.fm")
        
        # Generate playlist name if not provided
        if not playlist_name:
            user_info = self.lastfm.get_user_info(lastfm_username)
            display_name = user_info.get('realname') or user_info.get('name') or lastfm_username
            period_name = period.replace('month', ' months').replace('day', ' days')
            playlist_name = f"{display_name}'s Top Tracks ({period_name})"
        
        if not playlist_description:
            playlist_description = f"Top tracks from Last.fm user {lastfm_username} for period: {period}"
        
        return self._create_spotify_playlist(
            lastfm_tracks, playlist_name, playlist_description, public
        )
    
    def convert_recent_tracks(self, lastfm_username: str, limit: int = 50,
                             playlist_name: str = None, playlist_description: str = None, 
                             public: bool = True) -> Dict:
        """Convert Last.fm recent tracks to a Spotify playlist"""
        
        print(f"\n🎵 Fetching recent tracks for {lastfm_username}...")
        
        # Fetch Last.fm data
        lastfm_tracks = self._fetch_all_tracks(
            self.lastfm.get_user_recent_tracks,
            lastfm_username,
            limit=limit
        )
        
        if not lastfm_tracks:
            raise Exception("No recent tracks found on Last.fm")
        
        # Generate playlist name if not provided
        if not playlist_name:
            user_info = self.lastfm.get_user_info(lastfm_username)
            display_name = user_info.get('realname') or user_info.get('name') or lastfm_username
            playlist_name = f"{display_name}'s Recent Tracks"
        
        if not playlist_description:
            playlist_description = f"Recent tracks from Last.fm user {lastfm_username}"
        
        return self._create_spotify_playlist(
            lastfm_tracks, playlist_name, playlist_description, public
        )
    
    def convert_loved_tracks(self, lastfm_username: str, limit: int = 50,
                            playlist_name: str = None, playlist_description: str = None,
                            public: bool = True) -> Dict:
        """Convert Last.fm loved tracks to a Spotify playlist"""
        
        print(f"\n❤️ Fetching loved tracks for {lastfm_username}...")
        
        # Fetch Last.fm data
        lastfm_tracks = self._fetch_all_tracks(
            self.lastfm.get_user_loved_tracks,
            lastfm_username,
            limit=limit
        )
        
        if not lastfm_tracks:
            raise Exception("No loved tracks found on Last.fm")
        
        # Generate playlist name if not provided
        if not playlist_name:
            user_info = self.lastfm.get_user_info(lastfm_username)
            display_name = user_info.get('realname') or user_info.get('name') or lastfm_username
            playlist_name = f"{display_name}'s Loved Tracks"
        
        if not playlist_description:
            playlist_description = f"Loved tracks from Last.fm user {lastfm_username}"
        
        return self._create_spotify_playlist(
            lastfm_tracks, playlist_name, playlist_description, public
        )
    
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