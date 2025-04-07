#!/bin/bash

# === HoundTheCult Twitter Bot Installation Script ===
# This script sets up the bot environment, installs dependencies,
# and prepares the necessary configuration files.

set -e  # Exit on any error

# Print colorful header
echo -e "\e[1;34m==================================================\e[0m"
echo -e "\e[1;34m  HoundTheCult Twitter Bot - Installation Script  \e[0m"
echo -e "\e[1;34m==================================================\e[0m"

# Create directory structure
echo -e "\n\e[1;33m[1/5] Creating directory structure...\e[0m"
mkdir -p data logs config/

# Check for Python 3
echo -e "\n\e[1;33m[2/5] Checking Python installation...\e[0m"
if command -v python3 &>/dev/null; then
    echo "✅ Python 3 is installed"
    PYTHON_CMD="python3"
elif command -v python &>/dev/null && [[ $(python --version 2>&1) == *"Python 3"* ]]; then
    echo "✅ Python 3 is installed as 'python'"
    PYTHON_CMD="python"
else
    echo "❌ Python 3 is required but not installed. Please install Python 3.7 or higher."
    exit 1
fi

# Install dependencies
echo -e "\n\e[1;33m[3/5] Installing Python dependencies...\e[0m"
if command -v pip3 &>/dev/null; then
    pip3 install tweepy
    pip3 install -r requirements.txt 2>/dev/null || echo "⚠️  No requirements.txt found, installing only essential packages"
elif command -v pip &>/dev/null; then
    pip install tweepy
    pip install -r requirements.txt 2>/dev/null || echo "⚠️  No requirements.txt found, installing only essential packages"
else
    echo "❌ pip is not installed. Please install pip to continue."
    exit 1
fi

# Create configuration template
echo -e "\n\e[1;33m[4/5] Setting up configuration...\e[0m"
if [ ! -f "config/config.json.example" ]; then
    echo "Creating config template..."
    cat > config/config.json.example << EOL
{
    "twitter_api": {
        "API_KEY": "your-api-key-here",
        "API_SECRET": "your-api-secret-here",
        "ACCESS_TOKEN": "your-access-token-here",
        "ACCESS_SECRET": "your-access-secret-here",
        "BEARER_TOKEN": "your-bearer-token-here"
    }
}
EOL
    echo "✅ Created config template at config/config.json.example"
    
    if [ ! -f "config/config.json" ]; then
        cp config/config.json.example config/config.json
        echo "✅ Created initial config.json (you'll need to edit this with your API keys)"
    fi
else
    echo "✅ Configuration template already exists"
fi

# Set file permissions
echo -e "\n\e[1;33m[5/5] Setting file permissions...\e[0m"
chmod +x scripts/deploy.sh 2>/dev/null || echo "⚠️  deploy.sh not found or couldn't set permissions"
chmod +x main.py 2>/dev/null || echo "⚠️  main.py not found or couldn't set permissions"

# Final instructions
echo -e "\n\e[1;32m========================================\e[0m"
echo -e "\e[1;32m  Installation completed successfully!  \e[0m"
echo -e "\e[1;32m========================================\e[0m"
echo -e "\n\e[1mNext steps:\e[0m"
echo "1. Edit config/config.json with your Twitter API credentials"
echo "2. Run the bot with: python3 main.py"
echo "3. To deploy to a server, use: scripts/deploy.sh"
echo -e "\nThank you for installing HoundTheCult Twitter Bot!\n"
