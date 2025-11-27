# How to Get Your Valorant API Key

To enable the bot to fetch real-time Valorant stats (Rank, K/D, Match History), you need a free API key from HenrikDev (Unofficial Valorant API).

## Step 1: Get the Key
1. Go to the **HenrikDev Dashboard**: [https://api.henrikdev.xyz/dashboard](https://api.henrikdev.xyz/dashboard)
2. Click **"Login with Discord"** and authorize the application.
3. Once logged in, you will see your **API Key** on the dashboard.
   - It usually starts with `HDEV-`.
4. Click the **Copy** button to copy the key to your clipboard.

## Step 2: Add Key to Bot Configuration
1. Open the `app` folder in your project.
2. Open the `.env` file.
3. Find the line that looks like this:
   ```env
   HENRIK_DEV_API_KEY=
   ```
4. Paste your key after the equals sign. It should look like this:
   ```env
   HENRIK_DEV_API_KEY=HDEV-12345678-abcd-efgh-ijkl-1234567890ab
   ```
5. **Save the file** (Ctrl+S).

## Step 3: Restart the Bot
1. If the bot is running, stop it by pressing `Ctrl+C` in the terminal.
2. Run the bot again:
   ```bash
   python run_youtube_bot.py
   ```
3. When asked, enter your **Valorant ID** (e.g., `Loki#1234`) so the bot knows which player's stats to fetch when viewers ask "What is your rank?".

## Troubleshooting
- **401 Unauthorized Error:** This means the key is missing, incorrect, or has extra spaces. Double-check the `.env` file.
- **404 Not Found:** This usually means the Valorant Name or Tag is incorrect. Make sure you entered it exactly as it appears in-game (e.g., `Loki#1234`).
