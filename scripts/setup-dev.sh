#!/bin/bash

# De Palma Development Setup Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🛠️  Setting up De Palma development environment"

# Navigate to project root
cd "$PROJECT_ROOT"

# Check Node.js version
echo "📋 Checking Node.js version..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

NODE_VERSION=$(node --version | sed 's/v//')
REQUIRED_VERSION="18.0.0"

if ! node -p "process.version.slice(1).split('.').map(Number).join('') >= '${REQUIRED_VERSION}'.split('.').map(Number).join('')" &> /dev/null; then
    echo "❌ Node.js version $NODE_VERSION is too old. Please install Node.js 18+ ."
    exit 1
fi

echo "✅ Node.js version $NODE_VERSION is suitable"

# Install dependencies
echo "📦 Installing Node.js dependencies..."
npm install

# Install Python dependencies for MCP server
echo "🐍 Setting up Python MCP server..."
if command -v python3 &> /dev/null; then
    cd src/mcp-servers/task-scheduler
    echo "📦 Installing Python dependencies..."

    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi

    # Activate virtual environment and install dependencies
    source venv/bin/activate
    pip install -r requirements.txt
    deactivate

    cd "$PROJECT_ROOT"
    echo "✅ Python MCP server setup complete"
else
    echo "⚠️  Python3 not found. MCP server will need manual setup."
fi

# Copy environment template
if [ ! -f ".env" ]; then
    echo "📋 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your actual configuration values"
else
    echo "✅ .env file already exists"
fi

# Build TypeScript
echo "🏗️  Building TypeScript..."
npm run build

# Run tests
echo "🧪 Running tests..."
npm test

echo ""
echo "🎉 Development setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your configuration"
echo "2. Set up AWS credentials: aws configure"
echo "3. Install SAM CLI: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html"
echo "4. Run development server: npm run dev"
echo "5. Deploy to dev: ./scripts/deploy.sh dev"
echo ""
echo "📚 Documentation:"
echo "- README.md for project overview"
echo "- CLAUDE.md for detailed architecture"
echo "- src/lib/types/index.ts for type definitions"