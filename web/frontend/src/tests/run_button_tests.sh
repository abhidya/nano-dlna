#!/bin/bash

# Run Button and Link Tests for nano-dlna Frontend
# This script executes the comprehensive button testing suite

echo "🧪 Running Button and Link Tests..."
echo "=================================="

# Navigate to frontend directory
cd "$(dirname "$0")/../.." || exit 1

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Run the button tests specifically
echo ""
echo "🔘 Testing all buttons and links..."
npm test -- buttons_and_links.test.js --verbose --coverage

# Generate coverage report for button-related code
echo ""
echo "📊 Generating coverage report..."
npm test -- buttons_and_links.test.js --coverage --coverageReporters=html --coverageDirectory=coverage/buttons

echo ""
echo "✅ Button testing complete!"
echo ""
echo "📄 View detailed results:"
echo "   - Coverage report: coverage/buttons/index.html"
echo "   - Test output above"
echo ""

# Optional: Run in watch mode for development
if [ "$1" = "--watch" ]; then
    echo "👀 Running in watch mode..."
    npm test -- buttons_and_links.test.js --watch
fi