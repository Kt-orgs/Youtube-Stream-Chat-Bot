# GitHub Actions Setup Guide

This guide will help you deploy your YouTube Chat Bot to run automatically using GitHub Actions (100% FREE forever).

## ✅ Why GitHub Actions?

- **Completely FREE**: 2,000 minutes/month (33+ hours)
- **Automatic**: Checks every 10 minutes for live streams
- **Zero maintenance**: Runs in the cloud
- **No credit card**: Never expires
- **Perfect for 3-4 hours daily usage**

## 📋 Prerequisites

1. **GitHub Account** (free)
   - Sign up at: https://github.com
2. **Your bot running locally once** (to generate `token.pickle`)

---

## 🚀 Setup Steps

### Step 1: Prepare Your Secrets

Before pushing to GitHub, you need to prepare several files as secrets:

#### 1.1: Generate OAuth Token (`token.pickle`)

Run the bot locally once to authenticate:

```powershell
cd c:\Users\ktyag\Documents\Live-chat-bot-testing\Youtube-Streaming-Chat-Bot\app
python run_youtube_bot.py
```

This will open a browser for OAuth authentication and create `token.pickle`.

#### 1.2: Convert Files to Base64

GitHub secrets need to be text, so we'll encode binary files:

```powershell
# Convert token.pickle to base64
[Convert]::ToBase64String([IO.File]::ReadAllBytes("token.pickle")) | Set-Clipboard
# Now the base64 string is in your clipboard - save it somewhere temporarily

# Get client_secret.json content (this stays as JSON)
Get-Content client_secret.json | Set-Clipboard
# Save this content somewhere temporarily

# Get streamer_profile.json (optional - bot can create it)
Get-Content streamer_profile.json | Set-Clipboard
# Save this content somewhere temporarily
```

---

### Step 2: Create GitHub Repository

#### 2.1: Initialize Git Locally

```powershell
cd c:\Users\ktyag\Documents\Live-chat-bot-testing\Youtube-Streaming-Chat-Bot\app

# Initialize git
git init

# Add all files (sensitive files are excluded by .gitignore)
git add .

# Create first commit
git commit -m "Initial commit - YouTube Chat Bot"
```

#### 2.2: Create GitHub Repository

1. Go to: https://github.com/new
2. Name: `youtube-chat-bot` (or your preferred name)
3. Visibility: **Public** (required for free Actions minutes)
4. **DO NOT** initialize with README, .gitignore, or license
5. Click "Create repository"

#### 2.3: Push to GitHub

```powershell
# Add remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/youtube-chat-bot.git

# Push code
git branch -M main
git push -u origin main
```

---

### Step 3: Configure GitHub Secrets

Go to your repository on GitHub:
`https://github.com/YOUR_USERNAME/youtube-chat-bot/settings/secrets/actions`

Click "New repository secret" and add each of the following:

#### Required Secrets:

| Secret Name | Value | How to Get |
|------------|-------|------------|
| `YOUTUBE_TOKEN_BASE64` | Base64 encoded `token.pickle` | From Step 1.2 above |
| `CLIENT_SECRET_JSON` | Content of `client_secret.json` | From Step 1.2 above |
| `GOOGLE_API_KEY` | Your Google Gemini API key | From your `.env` file |
| `YOUTUBE_API_KEY` | Your YouTube Data API key | From your `.env` file |

#### Optional Secrets:

| Secret Name | Value | Description |
|------------|-------|-------------|
| `HENRIK_DEV_API_KEY` | Your Valorant API key | Only if you use Valorant features |
| `STREAMER_PROFILE_JSON` | Content of `streamer_profile.json` | Bot can create this if missing |

#### Adding Secrets Step-by-Step:

1. **YOUTUBE_TOKEN_BASE64**:
   - Name: `YOUTUBE_TOKEN_BASE64`
   - Value: Paste the base64 string from Step 1.2
   - Click "Add secret"

2. **CLIENT_SECRET_JSON**:
   - Name: `CLIENT_SECRET_JSON`
   - Value: Paste the entire JSON content from `client_secret.json`
   - Click "Add secret"

3. **GOOGLE_API_KEY**:
   - Name: `GOOGLE_API_KEY`
   - Value: Your Gemini API key (e.g., `AIzaSy...`)
   - Click "Add secret"

4. **YOUTUBE_API_KEY**:
   - Name: `YOUTUBE_API_KEY`
   - Value: Your YouTube API key
   - Click "Add secret"

5. **HENRIK_DEV_API_KEY** (if using Valorant):
   - Name: `HENRIK_DEV_API_KEY`
   - Value: Your Valorant API key
   - Click "Add secret"

---

### Step 4: Enable GitHub Actions

1. Go to your repository on GitHub
2. Click the "Actions" tab
3. Click "I understand my workflows, go ahead and enable them"
4. You should see the workflow: "YouTube Chat Bot - Auto Stream Detection"

---

### Step 5: Test the Setup

#### Manual Test:

1. Go to: `https://github.com/YOUR_USERNAME/youtube-chat-bot/actions`
2. Click on "YouTube Chat Bot - Auto Stream Detection"
3. Click "Run workflow" → "Run workflow"
4. Watch the logs to see if it works

#### Automatic Test:

1. Start a YouTube live stream (can be unlisted)
2. Wait up to 10 minutes
3. Check GitHub Actions to see if bot auto-started
4. Check your stream chat for bot responses

---

## 📊 How It Works

```
┌─────────────────────────────────────────┐
│ GitHub Actions (Every 10 minutes)       │
├─────────────────────────────────────────┤
│ 1. Check for active live stream         │
│ 2. If found → Start bot                 │
│ 3. Bot runs for up to 4 hours           │
│ 4. Automatically stops when done        │
└─────────────────────────────────────────┘
```

**Schedule**: Checks every 10 minutes (customizable in `.github/workflows/youtube-bot.yml`)

**Auto-start**: When you go live, the next check (within 10 min) will detect it and start the bot

**Auto-stop**: Bot stops when:
- Stream ends (no more messages)
- 4-hour timeout reached
- Manual stop

---

## ⚙️ Configuration

### Change Check Interval

Edit `.github/workflows/youtube-bot.yml`:

```yaml
schedule:
  - cron: '*/10 * * * *'  # Every 10 minutes
  # Change to:
  - cron: '*/5 * * * *'   # Every 5 minutes (uses more minutes)
  - cron: '*/15 * * * *'  # Every 15 minutes (saves minutes)
```

### Manually Trigger Bot

1. Go to Actions tab
2. Select workflow
3. Click "Run workflow"
4. Optionally enter a specific video ID
5. Click "Run workflow"

---

## 🔍 Monitoring

### View Logs:

1. Go to: `https://github.com/YOUR_USERNAME/youtube-chat-bot/actions`
2. Click on a workflow run
3. Click on "check-and-run-bot"
4. View real-time logs

### Download Logs:

Logs are saved as artifacts for 7 days:
1. Go to completed workflow run
2. Scroll to "Artifacts"
3. Download "bot-logs-XXX"

### Check Usage:

Settings → Billing → Plans and usage
- See minutes used/remaining
- 2,000 minutes free every month

---

## 🐛 Troubleshooting

### Issue: "OAuth token not found"
**Solution**: Make sure you've added `YOUTUBE_TOKEN_BASE64` secret correctly (base64 encoded)

### Issue: "No active live stream found"
**Solution**: 
- Ensure your stream is actually live (not scheduled)
- Check that the OAuth token has proper scopes
- Try running manually with a specific video ID

### Issue: "Quota exceeded"
**Solution**: Your YouTube API quota is exhausted. Wait until it resets (daily) or request quota increase

### Issue: "Workflow doesn't trigger"
**Solution**: 
- GitHub Actions requires public repo for free tier
- Check if Actions are enabled in Settings → Actions
- Verify cron schedule is correct

### Issue: "Bot stops after 6 hours"
**Solution**: GitHub Actions has a 6-hour max runtime. Your bot is configured for 4 hours, which should be fine.

---

## 💰 Cost & Limits

- **GitHub Actions**: FREE (2,000 min/month)
- **Your usage**: ~120-150 min/month (3-4 hrs daily)
- **Cost**: $0.00 forever
- **No credit card needed**
- **No trial period** - it's permanently free

---

## 🔒 Security Notes

✅ **Safe to make repo public** because:
- All sensitive data is in GitHub Secrets
- `.gitignore` excludes `client_secret.json`, `token.pickle`, `.env`
- Secrets are encrypted and never exposed in logs

⚠️ **Never commit**:
- `client_secret.json`
- `token.pickle`
- `.env` file
- `streamer_profile.json` (has personal info)

---

## 🎯 Next Steps

1. ✅ Set up secrets (Step 3)
2. ✅ Push code to GitHub (Step 2)
3. ✅ Enable Actions (Step 4)
4. ✅ Test manually (Step 5)
5. 🚀 Start streaming and watch it work!

---

## 📞 Need Help?

If you encounter issues:
1. Check the workflow logs in GitHub Actions
2. Verify all secrets are set correctly
3. Ensure `token.pickle` was generated locally first
4. Make sure your repo is public (for free tier)

The bot will:
- ✅ Auto-detect your live streams
- ✅ Start within 10 minutes of going live
- ✅ Run for your entire stream (up to 4 hours)
- ✅ Stop automatically
- ✅ Cost you $0.00

Happy streaming! 🎮🎬
