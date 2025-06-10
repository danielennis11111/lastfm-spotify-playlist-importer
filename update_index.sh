#!/bin/bash

# Check if a Cloud Run URL was provided
if [ -z "$1" ]; then
  echo "Usage: $0 <cloud_run_url>"
  echo "Example: $0 https://lastfm-spotify-converter-abcdef-uc.a.run.app"
  exit 1
fi

CLOUD_RUN_URL=$1

# Update the index.html file with the Cloud Run URL
echo "Updating index.html with Cloud Run URL: $CLOUD_RUN_URL"
sed -i.bak "s|CLOUD_RUN_URL_HERE|$CLOUD_RUN_URL|g" index.html

# Check if the update was successful
if grep -q "$CLOUD_RUN_URL" index.html; then
  echo "✅ index.html updated successfully!"
  echo "Now you can upload it to vibe-coding.rocks/lastfm-to-spotify-importer/"
else
  echo "❌ Failed to update index.html"
  exit 1
fi

# Reminder about Spotify Developer Dashboard
echo ""
echo "REMINDER: Make sure your Spotify Developer Dashboard has these redirect URIs:"
echo "1. $CLOUD_RUN_URL/callback (for direct access)"
echo "2. https://vibe-coding.rocks/lastfm-to-spotify-importer/callback (for embedded access)"
echo "" 