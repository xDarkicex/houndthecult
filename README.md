# HoundTheCult Twitter Bot

A Twitter bot that automatically quotes tweets when mentioned, designed to mimic human behavior with random delays, occasional typos, and varied responses.

## Description

HoundTheCult is a Twitter bot that monitors mentions and quotes the tweets users are referring to. It uses the Twitter API v2 (free tier) to listen for @mentions and respond with one of many randomized snarky comments. The bot is built to act naturally by using human-like timing, occasional typos, and randomized behavior patterns.

## Features

- Twitter API v2 integration (free tier compatible)
- Rate limiting management with gradual backoff
- Human-like behavior simulation
- Opt-in/out system for users
- Secure state persistence using JSON
- Robust error handling and recovery

## Installation

### Prerequisites

- Python 3.8 or higher
- Twitter Developer account with API v2 access

### Setup

Clone the repository:

```bash
git clone https://github.com/xDarkicex/houndthecult.git
cd houndthecult
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create your configuration file:

```bash
cp config/config.json.example config/config.json
```

Edit `config/config.json` with your Twitter API credentials.

## Configuration

The bot requires a valid Twitter API configuration in `config/config.json`:

```json
{
    "twitter_api": {
        "API_KEY": "your-api-key",
        "API_SECRET": "your-api-secret",
        "ACCESS_TOKEN": "your-access-token",
        "ACCESS_SECRET": "your-access-secret",
        "BEARER_TOKEN": "your-bearer-token"
    },
    "snarky_comments": [
        "Found one!",
        "Another gem from the cult...",
        ... additional comments ...
    ]
}
```

## Usage

### Running the Bot

```bash
python main.py
```

### Deployment

Use the included deployment script to deploy to your server:

```bash
./scripts/deploy.sh
```

### User Commands

Users can opt out of being quoted by mentioning the bot with:

- `!optout` - The bot will no longer quote tweets when mentioned by this user
- `!optin` - Re-enable the bot to quote tweets when mentioned by this user

## Project Structure

```
houndthecult/
├── src/                   # Source code
├── config/                # Configuration files
├── data/                  # State data storage
├── logs/                  # Log files
├── scripts/               # Utility scripts
├── main.py                # Entry point
├── requirements.txt       # Dependencies
└── README.md              # This file
```

## Rate Limiting

The bot implements sophisticated rate limiting to stay within Twitter's API constraints:

- Rolling 15-minute window tracking
- Gradual backoff at different utilization thresholds
- Monthly usage limits for free tier

## License

[Insert your license information here]

## Acknowledgments

- Twitter API v2
- Tweepy Python library