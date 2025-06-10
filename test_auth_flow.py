#!/usr/bin/env python3

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI

print("🔧 Testing Spotify Authentication Flow")
print("=" * 50)

print(f"Client ID: {SPOTIFY_CLIENT_ID[:8]}...")
print(f"Client Secret: {SPOTIFY_CLIENT_SECRET[:8]}...")
print(f"Redirect URI: {SPOTIFY_REDIRECT_URI}")

print("\n📋 Step 1: Creating SpotifyOAuth object...")
try:
    auth_manager = SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope="user-read-private playlist-modify-public playlist-modify-private",
        open_browser=True,
        show_dialog=True  # Force showing the auth dialog
    )
    print("✅ SpotifyOAuth created successfully")
except Exception as e:
    print(f"❌ Error creating SpotifyOAuth: {e}")
    exit(1)

print("\n📋 Step 2: Getting authorization URL...")
try:
    auth_url = auth_manager.get_authorize_url()
    print(f"✅ Auth URL generated: {auth_url[:60]}...")
except Exception as e:
    print(f"❌ Error getting auth URL: {e}")
    exit(1)

print("\n📋 Step 3: Checking for cached token...")
try:
    token_info = auth_manager.get_cached_token()
    if token_info:
        print("✅ Found cached token")
        print(f"   Access token: {token_info.get('access_token', '')[:20]}...")
        print(f"   Expires at: {token_info.get('expires_at', 'Unknown')}")
    else:
        print("❌ No cached token found")
        print("\n🌐 Opening browser for authentication...")
        print("Please authorize the app in your browser...")
        
        # This should open a browser window
        token_info = auth_manager.get_access_token()
        
        if token_info:
            print("✅ Successfully got access token!")
        else:
            print("❌ Failed to get access token")
            exit(1)
            
except Exception as e:
    print(f"❌ Error during token exchange: {e}")
    exit(1)

print("\n📋 Step 4: Testing API call...")
try:
    sp = spotipy.Spotify(auth_manager=auth_manager)
    user_info = sp.current_user()
    print(f"✅ Successfully authenticated as: {user_info['display_name']}")
    print(f"   User ID: {user_info['id']}")
    print(f"   Country: {user_info.get('country', 'N/A')}")
    
except Exception as e:
    print(f"❌ Error calling Spotify API: {e}")

print("\n🎉 Authentication test complete!") 