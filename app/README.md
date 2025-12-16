# YouTube Live Chat Bot

An intelligent AI-powered chat bot for YouTube live streams that automatically detects when you go live and interacts with your viewers.

## ✨ Features

- 🤖 **AI-Powered Responses**: Uses Google Gemini for intelligent chat interactions
- 🎮 **Gaming Support**: Special features for Valorant players (stats, agent info, maps)
- 👋 **Greeting System**: Welcomes new viewers automatically
- 📊 **Analytics**: Track viewer engagement and bot performance
- 🎯 **Command System**: Built-in commands for viewers (!help, !ping, !stats, etc.)
- 🔄 **Auto-Detection**: Automatically finds and connects to your live streams
- ☁️ **Cloud-Ready**: Runs on GitHub Actions (100% free)

## 🚀 Quick Start

### 1. Run Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Run the bot
python run_youtube_bot.py
```

### 2. Deploy to GitHub Actions (FREE)

See [GITHUB_ACTIONS_SETUP.md](GITHUB_ACTIONS_SETUP.md) for detailed instructions.

**Summary**:
1. Push code to GitHub (public repo)
2. Add secrets (API keys, OAuth token)
3. Enable GitHub Actions
4. Bot automatically starts when you go live!

## 📋 Requirements

- Python 3.11+
- Google Gemini API key
- YouTube Data API key
- YouTube OAuth credentials (client_secret.json)
- (Optional) Valorant API key for gaming features

## 🔧 Configuration

### Environment Variables

Create a `.env` file with:

```env
GOOGLE_API_KEY=your_gemini_api_key
YOUTUBE_API_KEY=your_youtube_api_key
HENRIK_DEV_API_KEY=your_valorant_api_key  # Optional
AGENT_NAME=youtube_chat_advanced
```

### Streamer Profile

On first run, the bot will ask you to create a streamer profile with:
- Your name/channel name
- Gaming or non-gaming stream
- Game details (if gaming)
- System specs, location, etc.

This personalizes the bot's responses to your channel.

## 💰 Cost

- **GitHub Actions**: FREE (2,000 minutes/month)
- **Your Usage**: ~120-150 minutes/month (3-4 hours daily)
- **Total Cost**: $0.00 forever

## 📖 Documentation

- [GitHub Actions Setup Guide](GITHUB_ACTIONS_SETUP.md) - Deploy to cloud for free
- [Valorant API Setup](VALORANT_API_SETUP.md) - Enable gaming features

## 🎮 Available Commands

Viewers can use these commands in chat:

- `!help` - Show available commands
- `!ping` - Check if bot is responsive
- `!status` - Show stream status
- `!socials` - Get your social media links
- `!stats` - Valorant statistics (if configured)
- `!agent <name>` - Valorant agent information
- `!map <name>` - Valorant map information
- `!viewers` - Current viewer count
- `!leaderboard` - Top chatters

## 🔒 Security

- All sensitive files are excluded via `.gitignore`
- API keys stored as GitHub Secrets (encrypted)
- OAuth tokens never committed to repo
- Safe to make repository public

## 📊 How It Works

```
GitHub Actions (Every 10 minutes)
    ↓
Check for active live stream
    ↓
If stream found → Start bot
    ↓
Bot connects to live chat
    ↓
Responds to messages using AI + Skills
    ↓
Runs for up to 4 hours
    ↓
Automatically stops
```

## 🤝 Contributing

Contributions welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests

## 📝 License

MIT License - feel free to use for your own streams!

## ⚠️ Important Notes

- Bot requires active YouTube live stream
- Works with public, unlisted, and private streams
- Respects YouTube API quotas
- Auto-detects streams (no manual video ID needed)

## 🆘 Support

If you encounter issues:
1. Check [GITHUB_ACTIONS_SETUP.md](GITHUB_ACTIONS_SETUP.md)
2. Review GitHub Actions logs
3. Verify all secrets are configured
4. Ensure OAuth token is valid

---

Made with ❤️ for content creators
