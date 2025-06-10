#!/usr/bin/env python3

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from lastfm_client import LastFmClient
from spotify_client import SpotifyClient
from playlist_converter import PlaylistConverter
from tqdm import tqdm
import time

def find_existing_playlist(spotify_client, playlist_name):
    """Find an existing playlist by name"""
    try:
        user = spotify_client.sp.current_user()
        playlists = spotify_client.sp.user_playlists(user['id'])
        
        for playlist in playlists['items']:
            if playlist['name'] == playlist_name:
                return playlist
        return None
    except Exception as e:
        print(f"Error finding playlist: {e}")
        return None

def get_playlist_tracks(spotify_client, playlist_id):
    """Get all current tracks in a playlist"""
    try:
        tracks = []
        results = spotify_client.sp.playlist_tracks(playlist_id)
        tracks.extend(results['items'])
        
        while results['next']:
            results = spotify_client.sp.next(results)
            tracks.extend(results['items'])
        
        return tracks
    except Exception as e:
        print(f"Error getting playlist tracks: {e}")
        return []

def main():
    print("🎵 Adding More Tracks to Existing Playlist")
    print("=" * 60)
    
    # Initialize clients
    print("Initializing clients...")
    lastfm = LastFmClient()
    spotify = SpotifyClient()
    
    # Find the existing playlist
    playlist_name = "cassetteand45's Complete Music Library"
    print(f"🔍 Looking for playlist: {playlist_name}")
    
    existing_playlist = find_existing_playlist(spotify, playlist_name)
    if not existing_playlist:
        print(f"❌ Playlist '{playlist_name}' not found!")
        return
    
    playlist_id = existing_playlist['id']
    playlist_url = existing_playlist['external_urls']['spotify']
    print(f"✅ Found playlist: {playlist_url}")
    
    # Get current tracks in playlist
    print("📋 Getting current playlist tracks...")
    current_tracks = get_playlist_tracks(spotify, playlist_id)
    current_track_count = len(current_tracks)
    print(f"📊 Current playlist has {current_track_count} tracks")
    
    # Calculate how many more we can add
    max_tracks = 10000
    tracks_needed = max_tracks - current_track_count
    print(f"🎯 Can add {tracks_needed} more tracks to reach {max_tracks} limit")
    
    if tracks_needed <= 0:
        print("✅ Playlist is already at or near the limit!")
        return
    
    # Get existing track URIs to avoid duplicates
    existing_uris = set()
    for track_item in current_tracks:
        if track_item['track'] and track_item['track']['uri']:
            existing_uris.add(track_item['track']['uri'])
    
    print(f"🔍 Tracking {len(existing_uris)} existing URIs to avoid duplicates")
    
    # Fetch more tracks from Last.fm (starting after our previous 2000)
    print(f"\n🎵 Fetching more tracks from cassetteand45's Last.fm...")
    
    # We'll fetch in batches to get more tracks beyond our previous 2000
    all_new_tracks = []
    batch_size = 1000
    max_total_fetch = min(tracks_needed + 1000, 10000)  # Fetch extra in case of duplicates
    
    for offset in range(2000, min(12475, max_total_fetch + 2000), batch_size):
        remaining_needed = tracks_needed - len(all_new_tracks)
        if remaining_needed <= 0:
            break
            
        print(f"📥 Fetching tracks {offset+1} to {offset+batch_size}...")
        try:
            # Get tracks with pagination
            batch_tracks = []
            page = (offset // 50) + 1  # Last.fm uses 50 tracks per page
            
            for p in range(page, page + (batch_size // 50)):
                tracks = lastfm.get_user_top_tracks('cassetteand45', 'overall', 50, p)
                if not tracks:
                    break
                batch_tracks.extend(tracks)
                time.sleep(0.1)  # Rate limiting
            
            all_new_tracks.extend(batch_tracks)
            print(f"✅ Got {len(batch_tracks)} tracks (total: {len(all_new_tracks)})")
            
        except Exception as e:
            print(f"⚠️ Error fetching batch: {e}")
            break
    
    print(f"\n🔍 Searching Spotify for {len(all_new_tracks)} additional tracks...")
    
    # Search for tracks on Spotify and filter out duplicates
    new_spotify_tracks = []
    
    with tqdm(total=len(all_new_tracks), desc="Searching tracks") as pbar:
        for lastfm_track in all_new_tracks:
            try:
                # Normalize track data
                normalized = lastfm.normalize_track_data(lastfm_track)
                artist = normalized['artist']
                track = normalized['track']
                
                # Search on Spotify
                results = spotify.search_track(artist, track, limit=5)
                
                if results:
                    best_match = spotify.find_best_match(normalized, results)
                    if best_match and best_match['uri'] not in existing_uris:
                        new_spotify_tracks.append(best_match)
                        existing_uris.add(best_match['uri'])  # Add to set to avoid future duplicates
                
                pbar.set_postfix_str(f"{artist} - {track}")
                pbar.update(1)
                
                # Stop if we have enough tracks
                if len(new_spotify_tracks) >= tracks_needed:
                    break
                    
            except Exception as e:
                pbar.update(1)
                continue
    
    print(f"\n📊 Found {len(new_spotify_tracks)} new unique tracks to add")
    
    if not new_spotify_tracks:
        print("❌ No new tracks to add!")
        return
    
    # Add tracks to playlist in batches
    print(f"🎵 Adding {len(new_spotify_tracks)} tracks to playlist...")
    
    track_uris = [track['uri'] for track in new_spotify_tracks]
    success = spotify.add_tracks_to_playlist(playlist_id, track_uris)
    
    if success:
        final_count = current_track_count + len(new_spotify_tracks)
        print(f"\n🎉 SUCCESS!")
        print(f"📝 Playlist: {playlist_name}")
        print(f"🔗 URL: {playlist_url}")
        print(f"📊 Total tracks: {final_count}")
        print(f"✅ Added: {len(new_spotify_tracks)} new tracks")
        print(f"🎯 Progress: {final_count}/10,000 ({final_count/100:.1f}%)")
    else:
        print("❌ Failed to add tracks to playlist!")

if __name__ == "__main__":
    main() 