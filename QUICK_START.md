# 🚀 Quick Start Guide - Local Testing

**Status:** Ready to run!  
**Date:** December 5, 2025

---

## ✅ Pre-Flight Checklist

### Configuration Files
- ✅ `.env` file exists with API keys
- ✅ `client_secret.json` (YouTube OAuth) present
- ✅ `streamer_profile.json` configured
- ✅ All dependencies installed

### API Keys Configured
- ✅ `GOOGLE_API_KEY` (Gemini AI)
- ✅ `YOUTUBE_API_KEY` (YouTube Data API)
- ✅ `HENRIK_DEV_API_KEY` (Valorant stats)
- ✅ `YOUTUBE_VIDEO_ID` (currently: vsFddngpUMc)

### Bot Profile
- **Name:** Loki
- **Valorant ID:** LOKI#6461
- **Region:** EU
- **System:** Intel i7-11800H

---

## 🎬 How to Start Your Unlisted Stream

### Step 1: Start Your Stream
1. Open **YouTube Studio** (https://studio.youtube.com)
2. Click **"Create"** → **"Go Live"**
3. Set visibility to **"Unlisted"** (for testing)
4. Configure your stream settings
5. Click **"Go Live"**

### Step 2: Get Your Video ID
Once stream is live, the URL will look like:
```
https://www.youtube.com/watch?v=VIDEO_ID_HERE
```

Copy the `VIDEO_ID_HERE` part (the string after `v=`)

### Step 3: Update Video ID (Optional)
If your video ID changed, update it:

**Option A: In .env file**
```bash
# Edit app/.env
YOUTUBE_VIDEO_ID=YOUR_NEW_VIDEO_ID
```

**Option B: Pass as argument**
```bash
python run_youtube_bot.py YOUR_VIDEO_ID
```

### Step 4: Start the Bot

**From project root:**
```powershell
cd "c:\Users\ktyag\Documents\Live-chat-bot-testing\Youtube-Streaming-Chat-Bot"
python app/run_youtube_bot.py
```

**Or specify video ID directly:**
```powershell
python app/run_youtube_bot.py YOUR_VIDEO_ID
```

---

## 📊 What to Expect

### Startup Sequence
```
Starting YouTube Chat Bridge for video YOUR_VIDEO_ID
✅ Configuration validation passed
✅ YOUTUBE_API_KEY found
✅ Gemini API key found
✅ HENRIK_DEV_API_KEY found
Successfully authenticated with YouTube API
Registered 7 skills
Registered 8 commands
Chat bridge started successfully!
Monitoring chat for messages...
```

### Bot Behavior
- **Reads all chat messages** from your stream
- **Processes commands** (messages starting with `!`)
- **Responds via skills** (greetings, hype, gaming questions)
- **Uses AI agent** for complex questions
- **Logs everything** to `./logs/bot_TIMESTAMP.log`

---

## 🎮 Testing Commands

Once the bot is running, test these commands in your stream chat:

### Built-in Commands
```
!help          → Shows available commands
!ping          → Checks if bot is alive
!uptime        → Shows stream duration
!socials       → Displays your social links
!status        → Shows current game
```

### Valorant Commands
```
!val LOKI#6461        → Your Valorant stats
!agent jett           → Jett agent info
!map ascent           → Ascent map info
```

### Natural Language
```
"hello bot"           → Greeting response
"what are your specs" → System specs
"great stream!"       → Community engagement
"good game!"          → Hype response
```

---

## 📝 Monitoring Logs

### View Logs in Real-Time
```powershell
# In a second terminal
cd "c:\Users\ktyag\Documents\Live-chat-bot-testing\Youtube-Streaming-Chat-Bot"
Get-Content -Wait "logs\bot_*.log" | Select-Object -Last 50
```

### Check for Errors
```powershell
Select-String "ERROR|CRITICAL" logs\*.log
```

### View Latest Messages
```powershell
Get-Content "logs\bot_*.log" | Select-Object -Last 20
```

---

## 🔧 Troubleshooting

### Bot Not Responding

**Check 1: Is the bot running?**
```powershell
# Should see python process
Get-Process python
```

**Check 2: Is chat enabled on stream?**
- Go to YouTube Studio
- Check if chat is enabled for your stream
- Make sure it's not restricted

**Check 3: Check logs for errors**
```powershell
Get-Content logs\bot_*.log | Select-String "ERROR"
```

### Authentication Issues

**Error: "Could not authenticate with YouTube API"**
- Check `client_secret.json` exists
- Delete `token.pickle` and re-authenticate
- Verify YouTube Data API is enabled in Google Cloud Console

**Error: "Invalid credentials"**
```powershell
# Remove cached token
Remove-Item app\token.pickle
# Restart bot - it will re-authenticate
```

### Commands Not Working

**Check 1: Command format**
- Commands must start with `!`
- Example: `!help` (not `help` or `! help`)

**Check 2: Rate limiting**
- Wait 2-3 seconds between commands
- Bot limits responses to prevent spam

**Check 3: View command logs**
```powershell
Get-Content logs\bot_*.log | Select-String "command"
```

### Bot Not Seeing Messages

**Issue: Bot processes old messages**
- Bot skips already-processed messages
- This is normal behavior

**Issue: No messages appearing**
- Check if stream chat is active
- Send test message in chat
- Check logs for "New message from" entries

---

## 🛑 Stopping the Bot

**Graceful shutdown:**
```
Press Ctrl+C in the terminal
```

The bot will:
1. Stop monitoring chat
2. Save processed message IDs
3. Close connections gracefully
4. Exit cleanly

---

## 📊 What Gets Logged

### Message Processing
```
INFO - New message from Username: message text
DEBUG - Checking if command...
DEBUG - Executing command for Username: !help
DEBUG - Command response: Available commands...
INFO - Posted response to chat
```

### Command Usage
```
INFO - Valorant stats query from Username: LOKI#6461 (summary)
DEBUG - Registered command: !help
DEBUG - Found command by name
```

### API Interactions
```
INFO - Successfully authenticated with YouTube API
DEBUG - Fetching messages from live chat...
DEBUG - Processing 5 new messages
```

---

## 🎯 Testing Checklist

Once bot is running, test these scenarios:

### Basic Functionality
- [ ] Bot starts without errors
- [ ] Bot connects to YouTube chat
- [ ] Bot reads new messages
- [ ] Logs are being created

### Command System
- [ ] `!help` shows command list
- [ ] `!ping` responds with "Pong!"
- [ ] `!socials` shows your links
- [ ] `!val LOKI#6461` attempts stats query

### Natural Language
- [ ] Send "hello" → Bot greets back
- [ ] Send "specs?" → Bot shares system specs
- [ ] Send "gg!" → Bot responds to hype

### Rate Limiting
- [ ] Send `!ping` twice quickly → Second blocked
- [ ] Wait 3 seconds → `!ping` works again

### Spam Detection
- [ ] Send same message 4+ times → Flagged as spam
- [ ] Different messages → Not flagged

---

## 💡 Pro Tips

### Multiple Monitors
- **Monitor 1:** Your game/content
- **Monitor 2:** Stream chat + bot terminal
- **Monitor 3:** OBS + YouTube Studio

### Chat Testing
- Use a second account or phone to test
- Send variety of messages and commands
- Verify bot responses appear in chat

### Log Analysis
Keep logs open in separate terminal:
```powershell
Get-Content -Wait logs\bot_*.log
```

### Performance
- Bot uses ~50-100MB RAM
- CPU usage <5% when idle
- Minimal impact on streaming

---

## 🚀 Ready to Go!

Your bot is configured and ready. Here's what to do:

1. **Start your unlisted YouTube stream**
2. **Note the video ID** from the URL
3. **Run the bot:** `python app/run_youtube_bot.py [VIDEO_ID]`
4. **Monitor logs** in separate terminal
5. **Test commands** in stream chat
6. **Verify responses** appear in chat

---

## 📞 Quick Reference

### Start Bot
```powershell
python app/run_youtube_bot.py
```

### Stop Bot
```
Ctrl+C
```

### View Logs
```powershell
Get-Content -Wait logs\bot_*.log
```

### Check Errors
```powershell
Select-String "ERROR" logs\*.log
```

---

## Next Steps After Testing

Once you've tested locally:

1. **Validate all features work**
2. **Test edge cases** (spam, rate limits, invalid commands)
3. **Monitor performance** during 15-30 minute stream
4. **Review logs** for any issues
5. **Proceed to Phase 3** (Valorant API integration)

---

**Current Status:** ✅ Ready to launch!  
**Estimated Setup Time:** 2-3 minutes  
**Testing Duration:** 15-30 minutes recommended

Good luck with your stream! 🎮🚀
