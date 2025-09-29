#!/bin/bash

# De Palma Deployment Script
# Usage: ./scripts/deploy.sh [dev|prod]

set -e

ENVIRONMENT=${1:-dev}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🚀 Deploying De Palma to $ENVIRONMENT environment"

# Check prerequisites
if ! command -v sam &> /dev/null; then
    echo "❌ AWS SAM CLI is not installed. Please install it first."
    echo "   https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "❌ Node.js/npm is not installed."
    exit 1
fi

# Check if AWS credentials are configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured. Run 'aws configure' first."
    exit 1
fi

echo "✅ Prerequisites check passed"

# Navigate to project root
cd "$PROJECT_ROOT"

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Run linting and tests
echo "🔍 Running linting..."
npm run lint

echo "🧪 Running tests..."
npm test

# Build TypeScript
echo "🏗️  Building TypeScript..."
npm run build

# Build SAM application
echo "🏗️  Building SAM application..."
sam build

# Deploy with SAM
echo "🚀 Deploying to $ENVIRONMENT..."

if [ "$ENVIRONMENT" = "dev" ]; then
    sam deploy --config-env dev
elif [ "$ENVIRONMENT" = "prod" ]; then
    echo "⚠️  Deploying to PRODUCTION. Are you sure? (y/N)"
    read -r confirmation
    if [[ $confirmation =~ ^[Yy]$ ]]; then
        sam deploy --config-env prod
    else
        echo "❌ Deployment cancelled"
        exit 1
    fi
else
    echo "❌ Invalid environment: $ENVIRONMENT. Use 'dev' or 'prod'"
    exit 1
fi

echo "✅ Deployment completed successfully!"

# Get the API URL
API_URL=$(aws cloudformation describe-stacks \
    --stack-name "de-palma-$ENVIRONMENT" \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
    --output text 2>/dev/null || echo "Unable to retrieve API URL")

if [ "$API_URL" != "Unable to retrieve API URL" ]; then
    echo "🌐 API URL: $API_URL"
    echo "🩺 Health check: ${API_URL}health"
fi

echo ""
echo "🎉 De Palma is now deployed to $ENVIRONMENT!"
echo ""
echo "Next steps:"
echo "1. Configure your email domain in AWS SES"
echo "2. Set up your Google Sheets with team data"
echo "3. Test the health check endpoint"
echo "4. Send a test email to louie@your-domain.com"