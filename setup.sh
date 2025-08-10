#!/bin/bash

echo "🚀 Setting up PMID Preprocessor..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📚 Installing Python dependencies..."
pip install -r requirements.txt

# Force upgrade OpenAI to latest version to avoid compatibility issues
echo "🔄 Upgrading OpenAI library..."
pip install --upgrade openai

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  Creating .env file from example..."
    cp example.env .env
    echo "📝 Please edit .env and add your OPENAI_API_KEY"
else
    echo "✅ .env file already exists"
fi

# Test OpenAI connection
echo "🧪 Testing OpenAI connection..."
python test_openai.py

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your OPENAI_API_KEY"
echo "2. Start backend: cd backend && source ../venv/bin/activate && source ../.env && python app.py"
echo "3. Start frontend: cd frontend && npm start"
echo ""