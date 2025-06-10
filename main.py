#!/usr/bin/env python3

import click
import json
import os
from typing import Dict, List
from playlist_converter import PlaylistConverter
from config import LASTFM_PERIODS


@click.group()
@click.version_option(version='1.0.0')
def cli():
    """
    🎵 Last.fm to Spotify Playlist Converter
    
    Convert your Last.fm listening data into Spotify playlists!
    
    Before using this tool, you need to set up API credentials:
    
    1. Last.fm API Key:
       - Visit: https://www.last.fm/api/account/create
       - Create an API account and get your API key
    
    2. Spotify App Credentials:
       - Visit: https://developer.spotify.com/dashboard
       - Create a new app and get your Client ID and Client Secret
       - Set redirect URI to: http://127.0.0.1:8000/callback
    
    Set these in a .env file or as environment variables:
    - LASTFM_API_KEY=your_lastfm_api_key
    - SPOTIFY_CLIENT_ID=your_spotify_client_id
    - SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
    """
    pass


@cli.command()
@click.argument('username')
@click.option('--period', '-p', default='overall', 
              type=click.Choice(list(LASTFM_PERIODS.keys())), 
              help='Time period for top tracks')
@click.option('--limit', '-l', default=50, help='Number of tracks to import')
@click.option('--name', '-n', help='Custom playlist name')
@click.option('--description', '-d', help='Custom playlist description')
@click.option('--private', is_flag=True, help='Make playlist private')
@click.option('--preview', is_flag=True, help='Preview tracks without creating playlist')
def top(username: str, period: str, limit: int, name: str, description: str, 
        private: bool, preview: bool):
    """Convert Last.fm top tracks to Spotify playlist"""
    
    try:
        converter = PlaylistConverter()
        
        if preview:
            print(f"\n🔍 Previewing top {limit} tracks for {username} ({period})...")
            tracks = converter.preview_tracks(username, 'top', period, limit)
            
            if not tracks:
                click.echo("❌ No tracks found")
                return
            
            click.echo(f"\n📋 Preview ({len(tracks)} tracks):")
            for i, track in enumerate(tracks, 1):
                playcount = f" ({track['playcount']} plays)" if track['playcount'] else ""
                click.echo(f"{i:3d}. {track['artist']} - {track['track']}{playcount}")
            
            if click.confirm(f"\nCreate playlist with these {len(tracks)} tracks?"):
                preview = False
            else:
                return
        
        if not preview:
            result = converter.convert_top_tracks(
                username, period, limit, name, description, not private
            )
            _display_result(result)
            
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)


@cli.command()
@click.argument('username')
@click.option('--limit', '-l', default=50, help='Number of tracks to import')
@click.option('--name', '-n', help='Custom playlist name')
@click.option('--description', '-d', help='Custom playlist description')
@click.option('--private', is_flag=True, help='Make playlist private')
@click.option('--preview', is_flag=True, help='Preview tracks without creating playlist')
def recent(username: str, limit: int, name: str, description: str, 
           private: bool, preview: bool):
    """Convert Last.fm recent tracks to Spotify playlist"""
    
    try:
        converter = PlaylistConverter()
        
        if preview:
            print(f"\n🔍 Previewing recent {limit} tracks for {username}...")
            tracks = converter.preview_tracks(username, 'recent', limit=limit)
            
            if not tracks:
                click.echo("❌ No tracks found")
                return
            
            click.echo(f"\n📋 Preview ({len(tracks)} tracks):")
            for i, track in enumerate(tracks, 1):
                click.echo(f"{i:3d}. {track['artist']} - {track['track']}")
            
            if click.confirm(f"\nCreate playlist with these {len(tracks)} tracks?"):
                preview = False
            else:
                return
        
        if not preview:
            result = converter.convert_recent_tracks(
                username, limit, name, description, not private
            )
            _display_result(result)
            
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)


@cli.command()
@click.argument('username')
@click.option('--limit', '-l', default=50, help='Number of tracks to import')
@click.option('--name', '-n', help='Custom playlist name')
@click.option('--description', '-d', help='Custom playlist description')
@click.option('--private', is_flag=True, help='Make playlist private')
@click.option('--preview', is_flag=True, help='Preview tracks without creating playlist')
def loved(username: str, limit: int, name: str, description: str, 
          private: bool, preview: bool):
    """Convert Last.fm loved tracks to Spotify playlist"""
    
    try:
        converter = PlaylistConverter()
        
        if preview:
            print(f"\n🔍 Previewing loved tracks for {username}...")
            tracks = converter.preview_tracks(username, 'loved', limit=limit)
            
            if not tracks:
                click.echo("❌ No tracks found")
                return
            
            click.echo(f"\n📋 Preview ({len(tracks)} tracks):")
            for i, track in enumerate(tracks, 1):
                click.echo(f"{i:3d}. {track['artist']} - {track['track']}")
            
            if click.confirm(f"\nCreate playlist with these {len(tracks)} tracks?"):
                preview = False
            else:
                return
        
        if not preview:
            result = converter.convert_loved_tracks(
                username, limit, name, description, not private
            )
            _display_result(result)
            
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)


@cli.command()
@click.argument('username')
def info(username: str):
    """Get Last.fm user information"""
    
    try:
        converter = PlaylistConverter()
        user_info = converter.get_user_info(username)
        
        if not user_info:
            click.echo("❌ User not found")
            return
        
        click.echo(f"\n👤 Last.fm User: {username}")
        click.echo(f"   Real Name: {user_info.get('realname', 'N/A')}")
        click.echo(f"   Country: {user_info.get('country', 'N/A')}")
        click.echo(f"   Playcount: {user_info.get('playcount', 'N/A'):,}")
        click.echo(f"   Registered: {user_info.get('registered', {}).get('#text', 'N/A')}")
        click.echo(f"   Profile URL: {user_info.get('url', 'N/A')}")
        
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)


@cli.command()
def periods():
    """List available time periods for top tracks"""
    
    click.echo("\n📅 Available time periods for top tracks:")
    for period, description in LASTFM_PERIODS.items():
        display_name = period.replace('month', ' months').replace('day', ' days')
        click.echo(f"   {period:<8} - {display_name}")


@cli.command()
def setup():
    """Interactive setup for API credentials"""
    
    click.echo("\n🔧 API Credentials Setup")
    click.echo("=" * 50)
    
    # Check current .env file
    env_file = '.env'
    existing_vars = {}
    
    if os.path.exists(env_file):
        click.echo("Found existing .env file")
        with open(env_file, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    existing_vars[key] = value
    
    # Last.fm API Key
    click.echo("\n1. Last.fm API Key")
    click.echo("   Visit: https://www.last.fm/api/account/create")
    
    current_lastfm = existing_vars.get('LASTFM_API_KEY', '')
    if current_lastfm:
        click.echo(f"   Current: {current_lastfm[:8]}...")
    
    lastfm_key = click.prompt("   Enter Last.fm API Key", default=current_lastfm, hide_input=True)
    
    # Spotify Credentials
    click.echo("\n2. Spotify App Credentials")
    click.echo("   Visit: https://developer.spotify.com/dashboard")
    click.echo("   Set redirect URI to: http://127.0.0.1:8000/callback")
    
    current_spotify_id = existing_vars.get('SPOTIFY_CLIENT_ID', '')
    if current_spotify_id:
        click.echo(f"   Current Client ID: {current_spotify_id[:8]}...")
    
    spotify_id = click.prompt("   Enter Spotify Client ID", default=current_spotify_id)
    
    current_spotify_secret = existing_vars.get('SPOTIFY_CLIENT_SECRET', '')
    if current_spotify_secret:
        click.echo(f"   Current Client Secret: {current_spotify_secret[:8]}...")
    
    spotify_secret = click.prompt("   Enter Spotify Client Secret", default=current_spotify_secret, hide_input=True)
    
    # Save to .env file
    env_content = f"""# Last.fm API Configuration
LASTFM_API_KEY={lastfm_key}

# Spotify API Configuration
SPOTIFY_CLIENT_ID={spotify_id}
SPOTIFY_CLIENT_SECRET={spotify_secret}
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8000/callback
"""
    
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    click.echo(f"\n✅ Configuration saved to {env_file}")
    click.echo("You can now use the playlist converter!")


def _display_result(result: Dict):
    """Display conversion result"""
    playlist = result['playlist']
    
    click.echo("\n🎉 Conversion Complete!")
    click.echo("=" * 50)
    click.echo(f"📝 Playlist: {playlist['name']}")
    click.echo(f"🔗 URL: {playlist['url']}")
    click.echo(f"📊 Statistics:")
    click.echo(f"   Last.fm tracks: {result['total_lastfm_tracks']}")
    click.echo(f"   Found on Spotify: {result['matched_tracks']}")
    click.echo(f"   Added to playlist: {result['added_tracks']}")
    click.echo(f"   Match rate: {result['match_rate']:.1f}%")
    
    if result['unmatched_tracks']:
        click.echo(f"\n❌ Tracks not found on Spotify ({len(result['unmatched_tracks'])}):")
        for track in result['unmatched_tracks'][:10]:  # Show first 10
            click.echo(f"   • {track['artist']} - {track['track']}")
        
        if len(result['unmatched_tracks']) > 10:
            click.echo(f"   ... and {len(result['unmatched_tracks']) - 10} more")


if __name__ == '__main__':
    cli() 