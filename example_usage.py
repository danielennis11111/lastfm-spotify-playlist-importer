#!/usr/bin/env python3
"""
Example usage of the Last.fm to Spotify Playlist Converter

This script demonstrates how to use the PlaylistConverter class programmatically.
Make sure you have set up your API credentials in a .env file before running.
"""

from playlist_converter import PlaylistConverter
from pprint import pprint


def example_basic_usage():
    """Basic usage example"""
    print("🎵 Basic Usage Example")
    print("=" * 50)
    
    # Initialize the converter
    # (It will automatically load credentials from .env file)
    converter = PlaylistConverter()
    
    # Example Last.fm username (replace with a real one)
    username = "rj"  # This is a demo user from Last.fm
    
    # Get user info first
    print(f"\n👤 Getting info for user: {username}")
    user_info = converter.get_user_info(username)
    print(f"Real name: {user_info.get('realname', 'N/A')}")
    print(f"Total plays: {user_info.get('playcount', 'N/A'):,}")
    
    # Preview some tracks
    print(f"\n🔍 Preview: Top 10 tracks (overall)")
    tracks = converter.preview_tracks(username, 'top', 'overall', 10)
    
    for i, track in enumerate(tracks, 1):
        playcount = f" ({track['playcount']} plays)" if track['playcount'] else ""
        print(f"{i:2d}. {track['artist']} - {track['track']}{playcount}")


def example_create_playlist():
    """Example of creating an actual playlist"""
    print("\n🎵 Creating Playlist Example")
    print("=" * 50)
    
    converter = PlaylistConverter()
    username = "rj"  # Replace with your Last.fm username
    
    try:
        # Create a playlist from top tracks of the last 3 months
        result = converter.convert_top_tracks(
            lastfm_username=username,
            period='3month',
            limit=25,
            playlist_name="My Top 25 (Last 3 Months)",
            playlist_description="Generated from Last.fm data",
            public=False  # Make it private
        )
        
        print("\n✅ Playlist created successfully!")
        print(f"Playlist URL: {result['playlist']['url']}")
        print(f"Total tracks added: {result['added_tracks']}")
        print(f"Match rate: {result['match_rate']:.1f}%")
        
        return result
        
    except Exception as e:
        print(f"❌ Error creating playlist: {e}")
        return None


def example_recent_tracks():
    """Example of converting recent tracks"""
    print("\n🎵 Recent Tracks Example")
    print("=" * 50)
    
    converter = PlaylistConverter()
    username = "rj"  # Replace with your Last.fm username
    
    try:
        result = converter.convert_recent_tracks(
            lastfm_username=username,
            limit=20,
            playlist_name="My Recent Listens",
            public=True
        )
        
        print("\n✅ Recent tracks playlist created!")
        print(f"Playlist URL: {result['playlist']['url']}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def example_loved_tracks():
    """Example of converting loved tracks"""
    print("\n❤️ Loved Tracks Example")
    print("=" * 50)
    
    converter = PlaylistConverter()
    username = "rj"  # Replace with your Last.fm username
    
    try:
        result = converter.convert_loved_tracks(
            lastfm_username=username,
            limit=30,
            playlist_name="My Loved Songs",
            public=True
        )
        
        print("\n✅ Loved tracks playlist created!")
        print(f"Playlist URL: {result['playlist']['url']}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def example_custom_configuration():
    """Example with custom API credentials"""
    print("\n🔧 Custom Configuration Example")
    print("=" * 50)
    
    # You can also initialize with custom credentials
    # instead of using .env file
    
    # converter = PlaylistConverter(
    #     lastfm_api_key="your_lastfm_api_key",
    #     spotify_client_id="your_spotify_client_id", 
    #     spotify_client_secret="your_spotify_client_secret",
    #     spotify_redirect_uri="http://127.0.0.1:8000/callback"
    # )
    
    print("This example shows how to pass custom credentials")
    print("Uncomment the code above to use custom credentials")


def main():
    """Main function to run examples"""
    print("🎵 Last.fm to Spotify Playlist Converter - Examples")
    print("=" * 60)
    
    # Check if credentials are set up
    try:
        from config import LASTFM_API_KEY, SPOTIFY_CLIENT_ID
        
        if not LASTFM_API_KEY or not SPOTIFY_CLIENT_ID:
            print("⚠️ API credentials not found!")
            print("Please run: python3 main.py setup")
            print("Or create a .env file with your credentials")
            return
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        print("Please set up your API credentials first")
        return
    
    # Run examples
    try:
        # Basic usage - just preview data
        example_basic_usage()
        
        # Ask user if they want to create actual playlists
        print("\n" + "=" * 60)
        response = input("Do you want to create actual playlists? (y/N): ").strip().lower()
        
        if response in ['y', 'yes']:
            print("\n🚀 Creating actual playlists...")
            print("Note: This will create playlists in your Spotify account")
            
            # Uncomment the examples you want to run:
            # example_create_playlist()
            # example_recent_tracks()  
            # example_loved_tracks()
            
            print("\nUncomment the desired examples in the code to create playlists")
        else:
            print("\n✅ Demo completed! No playlists were created.")
            
    except KeyboardInterrupt:
        print("\n\n👋 Demo cancelled by user")
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")


if __name__ == "__main__":
    main() 