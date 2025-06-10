# Cloud Run Deployment with vibe-coding.rocks Integration

This guide explains how to deploy the LastFM to Spotify Converter to Google Cloud Run and integrate it with vibe-coding.rocks.

## Overview

This deployment consists of two parts:
1. The main application runs on Google Cloud Run
2. A simple index.html file on vibe-coding.rocks/lastfm-to-spotify-importer/ that embeds the Cloud Run app

## Prerequisites

1. Google Cloud SDK installed
2. Docker installed
3. Access to the Google Cloud project "true-shuffle-radio"
4. Spotify API credentials (Client ID and Secret)
5. LastFM API key
6. Access to upload files to vibe-coding.rocks

## Step 1: Set Up Google Cloud Secret Manager

First, make sure your API keys are stored in Secret Manager:

```bash
# Enable the Secret Manager API if not already enabled
gcloud services enable secretmanager.googleapis.com --project true-shuffle-radio

# Create secrets for API credentials if they don't already exist
gcloud secrets create lastfm-api-key --project true-shuffle-radio
gcloud secrets create spotify-client-id --project true-shuffle-radio
gcloud secrets create spotify-client-secret --project true-shuffle-radio
gcloud secrets create flask-secret-key --project true-shuffle-radio

# Add the secret values if needed
gcloud secrets versions add lastfm-api-key --data-file=- --project true-shuffle-radio
# Enter your LastFM API Key and press Ctrl+D

gcloud secrets versions add spotify-client-id --data-file=- --project true-shuffle-radio
# Enter your Spotify Client ID and press Ctrl+D

gcloud secrets versions add spotify-client-secret --data-file=- --project true-shuffle-radio
# Enter your Spotify Client Secret and press Ctrl+D

gcloud secrets versions add flask-secret-key --data-file=- --project true-shuffle-radio
# Enter a random secure string and press Ctrl+D
```

## Step 2: Deploy to Cloud Run

Run the deployment script:

```bash
./deploy.sh
```

The first time you run this, it will:
1. Build and push a Docker image to Google Container Registry
2. Deploy the application to Cloud Run
3. Provide you with the Cloud Run URL
4. Show instructions for updating the SERVICE_URL

After the first deployment, follow the instructions to update the SERVICE_URL:

```bash
# Update the SERVICE_URL in deploy.sh for future deployments

# Update the Cloud Run service with the correct SERVICE_URL
gcloud run services update lastfm-spotify-converter \
  --platform managed \
  --region us-central1 \
  --project true-shuffle-radio \
  --set-env-vars="SERVICE_URL=YOUR_CLOUD_RUN_URL"
```

## Step 3: Update Spotify Developer Dashboard

Add these redirect URIs to your Spotify Developer Dashboard:

1. `YOUR_CLOUD_RUN_URL/callback` (for direct access)
2. `https://vibe-coding.rocks/lastfm-to-spotify-importer/callback` (for embedded access)

## Step 4: Prepare the index.html for vibe-coding.rocks

Update the index.html with your Cloud Run URL:

```bash
./update_index.sh YOUR_CLOUD_RUN_URL
```

This will replace the placeholder in index.html with your actual Cloud Run URL.

## Step 5: Upload to vibe-coding.rocks

Upload the updated index.html to vibe-coding.rocks/lastfm-to-spotify-importer/ using Cyberduck or your preferred FTP client.

## Testing

1. Visit your Cloud Run URL directly to ensure the app works
2. Visit https://vibe-coding.rocks/lastfm-to-spotify-importer/ to verify the embedded version works
3. Test the authentication flow from both the direct and embedded versions

## Environment Variables in Cloud Run

Your Cloud Run service should have these environment variables:

| Variable | Value | Source |
|----------|-------|--------|
| ENVIRONMENT | production | --set-env-vars |
| SERVICE_URL | YOUR_CLOUD_RUN_URL | --set-env-vars |
| APP_BASE_PATH | /lastfm-to-spotify-importer | --set-env-vars |
| LASTFM_API_KEY | [Your LastFM API Key] | Secret Manager |
| SPOTIFY_CLIENT_ID | [Your Spotify Client ID] | Secret Manager |
| SPOTIFY_CLIENT_SECRET | [Your Spotify Client Secret] | Secret Manager |
| FLASK_SECRET_KEY | [Your Flask Secret Key] | Secret Manager |

## Troubleshooting

- **Authentication Issues**: Verify that both redirect URIs are correctly set in the Spotify Developer Dashboard
- **Embedding Issues**: Check for Content Security Policy (CSP) restrictions on vibe-coding.rocks
- **Cloud Run Errors**: Check the logs in Google Cloud Console:
  ```bash
  gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=lastfm-spotify-converter" --limit 50
  ```

## Updating the Application

To update the application after making changes:

1. Make your code changes
2. Run the deployment script again:
   ```bash
   ./deploy.sh
   ```

The script will build a new container image and update the Cloud Run service with the new version. 