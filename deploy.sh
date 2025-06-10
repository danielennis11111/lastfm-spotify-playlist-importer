#!/bin/bash
set -e

# Configuration variables
PROJECT_ID="true-shuffle-radio"
REGION="us-central1"
SERVICE_NAME="lastfm-spotify-converter"
SERVICE_URL="https://lastfm-spotify-converter-v5nw64kyda-uc.a.run.app"
REDIRECT_URL_PATH="/callback"

# Build the Docker image
echo "Building Docker image..."
docker build --platform linux/amd64 -t "gcr.io/$PROJECT_ID/$SERVICE_NAME" .

# Push the image to Google Container Registry
echo "Pushing image to Google Container Registry..."
docker push "gcr.io/$PROJECT_ID/$SERVICE_NAME"

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image "gcr.io/$PROJECT_ID/$SERVICE_NAME" \
  --platform managed \
  --region $REGION \
  --project $PROJECT_ID \
  --allow-unauthenticated \
  --update-secrets=LASTFM_API_KEY=LASTFM_API_KEY:latest,SPOTIFY_CLIENT_ID=SPOTIFY_CLIENT_ID:latest,SPOTIFY_CLIENT_SECRET=SPOTIFY_CLIENT_SECRET:latest,FLASK_SECRET_KEY=flask-secret-key:latest \
  --set-env-vars=ENVIRONMENT=production,SERVICE_URL=$SERVICE_URL,APP_BASE_PATH="" \
  --timeout=600 \
  --memory=512Mi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=10

echo ""
echo "DEPLOYMENT COMPLETE!"
echo ""
echo "IMPORTANT: Make sure your Spotify Developer Dashboard has this redirect URI:"
echo "$SERVICE_URL$REDIRECT_URL_PATH"
echo "" 