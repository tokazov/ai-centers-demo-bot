#!/bin/bash

# Quick Deploy Script for Railway
# Автоматический деплой если есть доступ к Railway CLI

set -e

echo "🚀 AI Centers Demo Bot - Quick Deploy"
echo "======================================"

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    npm install -g @railway/cli
fi

echo "📦 Linking to Railway project..."
railway link fe9eead2-e606-4dd8-8820-a45687dcb36e || echo "⚠️  Already linked or needs manual login"

echo "🔧 Setting environment variables..."
railway variables set BOT_TOKEN=8672975647:AAHpWG5xTxLRv0IKKy6tvl_VlAn_FfL99vM
railway variables set GEMINI_API_KEY=AIzaSyDRJLp8JGpKid1pTJBRVgeumPdObveAXwY

echo "🚢 Deploying to Railway..."
railway up

echo ""
echo "✅ Deployment complete!"
echo "📱 Bot: https://t.me/TestCargoAsist_bot"
echo "📊 Railway: https://railway.app/project/fe9eead2-e606-4dd8-8820-a45687dcb36e"
echo ""
echo "Test the bot with /start command!"
