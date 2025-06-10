#!/usr/bin/env python3
"""
Test script for Last.fm API connectivity

This script tests the Last.fm API without requiring Spotify credentials.
You only need to set up your Last.fm API key to run this test.
"""

import os
from lastfm_client import LastFmClient


def test_lastfm_api():
    """Test Last.fm API connectivity and data fetching"""
    
    print("🔍 Testing Last.fm API Connection")
    print("=" * 50)
    
    # Check if API key is available
    from config import LASTFM_API_KEY
    
    if not LASTFM_API_KEY:
        print("❌ LASTFM_API_KEY not found!")
        print("Please set it in a .env file or run: python3 main.py setup")
        return False
    
    print(f"✅ Found Last.fm API key: {LASTFM_API_KEY[:8]}...")
    
    # Initialize client
    try:
        client = LastFmClient()
        print("✅ Last.fm client initialized")
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        return False
    
    # Test with a known user
    test_username = "rj"  # Official Last.fm test user
    
    print(f"\n👤 Testing with user: {test_username}")
    
    # Test user info
    try:
        user_info = client.get_user_info(test_username)
        
        if user_info:
            print("✅ User info retrieved:")
            print(f"   Real name: {user_info.get('realname', 'N/A')}")
            print(f"   Country: {user_info.get('country', 'N/A')}")
            print(f"   Total plays: {user_info.get('playcount', 'N/A'):,}")
            print(f"   Registered: {user_info.get('registered', {}).get('#text', 'N/A')}")
        else:
            print("❌ No user info returned")
            return False
            
    except Exception as e:
        print(f"❌ Failed to get user info: {e}")
        return False
    
    # Test top tracks
    try:
        print(f"\n🎵 Testing top tracks (last 7 days)...")
        tracks = client.get_user_top_tracks(test_username, period='7day', limit=5)
        
        if tracks:
            print(f"✅ Retrieved {len(tracks)} top tracks:")
            for i, track in enumerate(tracks, 1):
                normalized = client.normalize_track_data(track)
                playcount = f" ({normalized['playcount']} plays)" if normalized['playcount'] else ""
                print(f"   {i}. {normalized['artist']} - {normalized['track']}{playcount}")
        else:
            print("⚠️ No top tracks found (this is normal for some users)")
            
    except Exception as e:
        print(f"❌ Failed to get top tracks: {e}")
        return False
    
    # Test recent tracks
    try:
        print(f"\n🕒 Testing recent tracks...")
        tracks = client.get_user_recent_tracks(test_username, limit=5)
        
        if tracks:
            print(f"✅ Retrieved {len(tracks)} recent tracks:")
            for i, track in enumerate(tracks, 1):
                normalized = client.normalize_track_data(track)
                print(f"   {i}. {normalized['artist']} - {normalized['track']}")
        else:
            print("⚠️ No recent tracks found")
            
    except Exception as e:
        print(f"❌ Failed to get recent tracks: {e}")
        return False
    
    # Test loved tracks
    try:
        print(f"\n❤️ Testing loved tracks...")
        tracks = client.get_user_loved_tracks(test_username, limit=3)
        
        if tracks:
            print(f"✅ Retrieved {len(tracks)} loved tracks:")
            for i, track in enumerate(tracks, 1):
                normalized = client.normalize_track_data(track)
                print(f"   {i}. {normalized['artist']} - {normalized['track']}")
        else:
            print("⚠️ No loved tracks found (this is normal)")
            
    except Exception as e:
        print(f"❌ Failed to get loved tracks: {e}")
        return False
    
    print(f"\n✅ All Last.fm API tests passed!")
    print("🎉 Your Last.fm API connection is working correctly!")
    
    return True


def test_your_username():
    """Test with user-provided username"""
    
    username = input("\nEnter your Last.fm username to test (or press Enter to skip): ").strip()
    
    if not username:
        print("Skipping personal username test")
        return
    
    print(f"\n🔍 Testing with your username: {username}")
    print("=" * 50)
    
    try:
        client = LastFmClient()
        
        # Get user info
        user_info = client.get_user_info(username)
        
        if not user_info:
            print("❌ User not found or profile is private")
            return
        
        print("✅ Your Last.fm profile:")
        print(f"   Username: {username}")
        print(f"   Real name: {user_info.get('realname', 'N/A')}")
        print(f"   Total plays: {user_info.get('playcount', 'N/A'):,}")
        
        # Preview some tracks
        tracks = client.get_user_top_tracks(username, period='overall', limit=5)
        
        if tracks:
            print(f"\n🎵 Your top 5 tracks (overall):")
            for i, track in enumerate(tracks, 1):
                normalized = client.normalize_track_data(track)
                playcount = f" ({normalized['playcount']} plays)" if normalized['playcount'] else ""
                print(f"   {i}. {normalized['artist']} - {normalized['track']}{playcount}")
        else:
            print("⚠️ No top tracks found. Your profile might be private or new.")
        
        print(f"\n✅ Ready to create playlists from {username}'s Last.fm data!")
        
    except Exception as e:
        print(f"❌ Error testing your username: {e}")


if __name__ == "__main__":
    print("🎵 Last.fm API Test Script")
    print("=" * 60)
    
    # Test API connection
    if test_lastfm_api():
        # Test with user's own username
        test_your_username()
        
        print(f"\n🚀 Next steps:")
        print("1. Run: python3 main.py setup  (to configure Spotify)")
        print("2. Run: python3 main.py top YOUR_USERNAME  (to create playlist)")
        
    else:
        print(f"\n❌ Last.fm API test failed!")
        print("Please check your API key and internet connection.") 