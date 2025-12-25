# YouTube Live Chat Bot - Cloud Automated

An AI-powered YouTube Live Chat bot that automatically monitors your channel for live streams and engages with viewers in real-time. **Runs completely in the cloud** via GitHub Actions - no local setup required!

## 🌟 Features

- **🤖 Fully Automated**: Checks for live streams every 10 minutes and starts automatically
- **☁️ Cloud-Based**: Runs on GitHub Actions - your PC doesn't need to be on
- **🎮 Gaming Integration**: Valorant stats commands (!rank, !stats, !lastmatch)
- **💬 Smart Engagement**: 
  - Greets viewers when they join
  - Answers questions intelligently
  - Responds to commands (!help, !ping, !stats, !socials)
  - AI-powered conversation using Google Gemini
- **📊 Analytics**: Tracks viewer engagement, top chatters, and bot statistics
- **🔄 Auto-Resume**: Continues monitoring even after streams end
- **⚡ Quota Optimized**: Designed to run for 5-12 hours within YouTube API limits

---

## 🚀 Complete Setup Guide

### Step 1: Fork/Clone This Repository

1. Fork this repository to your GitHub account
2. Clone it to your local machine (optional, for testing)

### Step 2: Get Required API Keys

You need three API keys to run the bot:

#### 1️⃣ Google AI API Key (Gemini)

This powers the AI responses.

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Click **"Get API key"** in the top navigation
3. Click **"Create API key"**
4. Copy the key (starts with `AIza...`)

#### 2️⃣ YouTube API Credentials

You need **two things** for YouTube:

**A. OAuth 2.0 Client Secret (for posting messages)**

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable **YouTube Data API v3**:
   - Search for "YouTube Data API v3"
   - Click on it and click **Enable**
4. Go to **Credentials** (left sidebar)
5. Click **"Create Credentials"** → **"OAuth client ID"**
6. If prompted, configure OAuth consent screen:
   - User Type: **External**
   - App name: "YouTube Chat Bot"
   - Add your email
   - Add scope: `https://www.googleapis.com/auth/youtube.force-ssl`
   - Add yourself as a test user
7. Back to Create OAuth Client ID:
   - Application type: **Desktop app**
   - Name: "YouTube Bot"
   - Click **Create**
8. **Download** the JSON file
9. Copy the entire contents of this JSON file (you'll need it for GitHub secrets)

**B. YouTube Data API Key (for reading stream info)**

1. In the same Google Cloud Console project
2. Go to **Credentials**
3. Click **"Create Credentials"** → **"API Key"**
4. Copy the key
5. (Recommended) Click **"Restrict Key"**:
   - API restrictions: Select **YouTube Data API v3**
   - Save

#### 3️⃣ Valorant API Key (Optional)

Only needed if you want Valorant stats commands.

1. Go to [HenrikDev Dashboard](https://api.henrikdev.xyz/dashboard)
2. Sign in with Discord
3. Copy your API Key (starts with `HDEV-`)

### Step 3: Authenticate YouTube OAuth (One-Time)

You need to generate an OAuth token locally first, then upload it to GitHub.

1. **On your local machine**, navigate to the `app` folder
2. Create a file named `client_secret.json` with the OAuth JSON you downloaded
3. Run the authentication script:
   ```bash
   cd app
   python -c "from youtube_integration.youtube_api import YouTubeLiveChatAPI; api = YouTubeLiveChatAPI(); api.authenticate()"
   ```
4. A browser will open - **sign in with your YouTube channel account**
5. Grant permissions
6. After success, a file `token.pickle` is created in the `app` folder
7. **Keep this file** - you'll upload it to GitHub

### Step 4: Create Streamer Profile

Create a file named `streamer_profile.json` in the `app` folder:

```json
{
  "Name": "YourName",
  "Is Gaming": true,
  "Valorant ID": "YourName#TAG",
  "Valorant Region": "eu",
  "Location": "Your Location",
  "System Specs": "Your PC Specs",
  "Profession/Bio": "What you do",
  "Twitter": "@yourhandle",
  "Instagram": "@yourhandle",
  "Discord": "discord.gg/yourinvite",
  "Twitch": "twitch.tv/yourname"
}
```

**Notes:**
- Set `"Is Gaming": false` if you're not a gaming streamer
- Remove Valorant fields if you don't play Valorant
- Social media fields are optional

### Step 5: Configure GitHub Secrets

Go to your repository on GitHub → **Settings** → **Secrets and variables** → **Actions**

#### Add these SECRETS:

1. **`GOOGLE_API_KEY`**
   - Value: Your Google AI API key from Step 2.1
   
2. **`YOUTUBE_API_KEY`**
   - Value: Your YouTube Data API key from Step 2.2.B
   
3. **`CLIENT_SECRET_JSON`**
   - Value: The entire contents of your `client_secret.json` file (the OAuth credentials)
   - Just copy-paste the whole JSON
   
4. **`YOUTUBE_TOKEN_BASE64`**
   - This is your `token.pickle` file encoded in base64
   - **Windows PowerShell:**
     ```powershell
     [Convert]::ToBase64String([IO.File]::ReadAllBytes("app\token.pickle")) | Set-Clipboard
     ```
   - **Linux/Mac:**
     ```bash
     base64 -w 0 app/token.pickle | pbcopy  # or xclip for Linux
     ```
   - Paste the output as the secret value
   
5. **`STREAMER_PROFILE_JSON_B64`**
   - Your `streamer_profile.json` encoded in base64
   - **Windows PowerShell:**
     ```powershell
     [Convert]::ToBase64String([IO.File]::ReadAllBytes("app\streamer_profile.json")) | Set-Clipboard
     ```
   - **Linux/Mac:**
     ```bash
     base64 -w 0 app/streamer_profile.json | pbcopy
     ```
   - Paste the output as the secret value

6. **`HENRIK_DEV_API_KEY`** (Optional - only if using Valorant)
   - Value: Your Valorant API key from Step 2.3

#### GitHub VARIABLES (these match the workflow env block)

Go to **Settings** → **Secrets and variables** → **Actions** → **Variables** tab. These map directly to `.github/workflows/youtube-bot.yml`:

- `AGENT_NAME` – Defaults to `youtube_chat_advanced`
- `YOUTUBE_VIDEO_ID` – Usually left empty; workflow auto-detects live video, manual runs can override
- `STREAMER_NAME` – Defaults to `Streamer` if not set
- `VALORANT_ID` – Falls back to `secrets.VALORANT_ID` if you store it as a secret instead
- `VALORANT_REGION` – Defaults to `eu` when missing

Optional socials (safe to leave empty):

- `TWITTER_HANDLE`
- `INSTAGRAM_HANDLE`
- `DISCORD_INVITE`
- `TWITCH_URL`

If these variables are not set, the bot will rely on `STREAMER_PROFILE_JSON_B64` (or `STREAMER_PROFILE_JSON`) for profile data, so you can manage details either via variables or the profile JSON.

### Step 6: Enable GitHub Actions

1. Go to your repository → **Actions** tab
2. If prompted, click **"I understand my workflows, go ahead and enable them"**
3. The workflow `YouTube Chat Bot - Auto Stream Detection` should appear

### Step 7: Test It!

#### Option 1: Manual Test
1. Start a YouTube live stream
2. Go to **Actions** tab → **YouTube Chat Bot - Auto Stream Detection**
3. Click **"Run workflow"** → **"Run workflow"**
4. Wait a few seconds and click on the running workflow to see logs

#### Option 2: Automatic (Scheduled)
1. Start a YouTube live stream
2. Wait up to 10 minutes
3. The bot will automatically detect your stream and start!

---

## 🎯 How It Works

### Automatic Detection
- **Every 10 minutes**, GitHub Actions checks if you're live
- If a live stream is detected, the bot starts automatically
- Bot runs for up to **4 hours per session**
- Continues monitoring even after your stream ends
- Resumes automatically when you go live again

### What the Bot Does

1. **Posts intro message** after 60 seconds: "🤖 Bot by LOKI here! Ask me anything..."
2. **Greets viewers** when they join
3. **Answers questions** using AI
4. **Responds to commands**:
   - `!help` - List all commands
   - `!stats` - Current stream stats (viewers, likes, subs)
   - `!ping` - Check bot responsiveness
   - `!uptime` - How long bot has been running
   - `!socials` - Your social media links
   - `!rank` - Valorant rank (if configured)
   - `!leaderboard` - Top chatters
   - And more!

### Quota Management
- **Reading messages**: Uses pytchat (NO quota used) ✅
- **Posting responses**: Uses YouTube API (quota efficient)
- **Optimized**: Can run for 5-12 hours depending on chat activity
- Stats caching reduces API calls by 70%

---

## 📊 Monitoring & Logs

### View Live Logs
1. Go to **Actions** tab
2. Click on the running workflow
3. Click on the **"check-and-run-bot"** job
4. Expand **"Check for live stream and run bot"** to see real-time logs

### Download Logs
- After each run, logs are saved as artifacts
- Available in the workflow run page for 7 days

### Analytics Database
- Stored in `data/analytics.db`
- Automatically committed after each stream
- Tracks viewer engagement, commands used, top chatters

---

## 🔧 Customization

### Change Bot Behavior

Edit files in `app/youtube_integration/chat_bridge.py`:

- **Response delay**: Change `response_delay` parameter (default: 2 seconds)
- **Ignore moderators**: Set `ignore_moderators=True`
- **Ignore owner**: Set `ignore_owner=True`

### Add Custom Commands

Add new commands in `app/commands/builtins.py` or create new files in `app/commands/`

### Modify AI Personality

Edit the agent instructions in `app/youtube_chat_advanced/agent.py`

---

## ⚠️ Troubleshooting

### Bot doesn't start automatically
- Check if your stream is actually live
- Verify GitHub Actions is enabled in your repo
- Check the Actions tab for error messages

### "Quota exceeded" error
- Bot uses ~3,000-5,500 quota units per day
- YouTube API limit is 10,000/day
- Should handle 5-12 hours of streaming
- Quota resets at midnight Pacific Time

### Bot not responding in chat
- Verify `YOUTUBE_TOKEN_BASE64` is set correctly
- Check if token has expired (re-run Step 3)
- Ensure YouTube Data API v3 is enabled

### OAuth token expired
- Re-run Step 3 to generate new token
- Update `YOUTUBE_TOKEN_BASE64` secret in GitHub

---

## 📂 Project Structure

```
Youtube-Streaming-Chat-Bot/
├── .github/
│   └── workflows/
│       └── youtube-bot.yml          # GitHub Actions workflow
├── app/
│   ├── run_youtube_bot.py           # Main entry point
│   ├── youtube_integration/         # YouTube API handling
│   ├── youtube_chat_advanced/       # AI Agent logic
│   ├── commands/                    # Bot commands
│   ├── skills/                      # Bot skills (greetings, gaming, etc.)
│   ├── analytics/                   # Analytics tracking
│   └── tools/                       # Custom tools (Valorant, etc.)
├── data/
│   └── analytics.db                 # Analytics database
└── README.md                        # This file
```

---

## 🎮 Available Commands

| Command | Description |
|---------|-------------|
| `!help` | Show all available commands |
| `!ping` | Check if bot is responsive |
| `!uptime` | How long bot has been running |
| `!stats` | Current stream stats (viewers, likes, subs) |
| `!socials` | Your social media links |
| `!status` | Bot status and configuration |
| `!rank` | Valorant rank (if configured) |
| `!lastmatch` | Last Valorant game stats |
| `!leaderboard` | Top 10 chatters this stream |
| `!viewers` | Most active viewers |
| `!botstats` | Bot response statistics |

---

## 🔐 Security Notes

- ✅ Never commit `client_secret.json` or `token.pickle` to Git
- ✅ All secrets are stored securely in GitHub Secrets
- ✅ OAuth tokens are encrypted in GitHub Actions
- ✅ API keys are never exposed in logs

---

## 📈 Future Enhancements

- [ ] Multi-language support
- [ ] Custom command creator via chat
- [ ] Integration with other games (CS2, LoL, etc.)
- [ ] Advanced moderation features
- [ ] Twitch integration

---

## 🤝 Contributing

Feel free to open issues or submit pull requests!

---

## 📄 License

This project is open source. Use it, modify it, and make it yours!

---

**Made with ❤️ for streamers by streamers**

*Happy Streaming!* 🎥✨
