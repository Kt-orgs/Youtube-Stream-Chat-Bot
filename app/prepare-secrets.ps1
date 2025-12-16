#!/usr/bin/env pwsh
# Helper script to prepare secrets for GitHub Actions
# Run this BEFORE pushing to GitHub

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "GitHub Secrets Preparation Helper" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

$secretsFile = "github-secrets.txt"

# Check if files exist
$missingFiles = @()

if (!(Test-Path "token.pickle")) {
    $missingFiles += "token.pickle"
}
if (!(Test-Path "client_secret.json")) {
    $missingFiles += "client_secret.json"
}
if (!(Test-Path ".env")) {
    $missingFiles += ".env"
}

if ($missingFiles.Count -gt 0) {
    Write-Host "WARNING: Missing required files:" -ForegroundColor Yellow
    foreach ($file in $missingFiles) {
        Write-Host "   - $file" -ForegroundColor Red
    }
    Write-Host ""
    
    if ($missingFiles -contains "token.pickle") {
        Write-Host "To generate token.pickle:" -ForegroundColor Yellow
        Write-Host "  python run_youtube_bot.py" -ForegroundColor White
        Write-Host ""
    }
    
    if ($missingFiles -contains "client_secret.json") {
        Write-Host "To get client_secret.json:" -ForegroundColor Yellow
        Write-Host "  1. Go to: https://console.cloud.google.com/apis/credentials" -ForegroundColor White
        Write-Host "  2. Create OAuth 2.0 Client ID (Desktop app)" -ForegroundColor White
        Write-Host "  3. Download as client_secret.json" -ForegroundColor White
        Write-Host ""
    }
    
    $continue = Read-Host "Continue anyway? (y/N)"
    if ($continue -ne 'y' -and $continue -ne 'Y') {
        exit 1
    }
}

# Create secrets file
Write-Host "Generating secrets file: $secretsFile" -ForegroundColor Cyan
Write-Host ""

$secrets = ""
$secrets += "================================================`n"
$secrets += "GITHUB SECRETS FOR ACTIONS`n"
$secrets += "================================================`n`n"
$secrets += "Copy each secret below to GitHub:`n"
$secrets += "Go to: https://github.com/YOUR_USERNAME/youtube-chat-bot/settings/secrets/actions`n`n"
$secrets += "================================================`n"
$secrets += "1. YOUTUBE_TOKEN_BASE64`n"
$secrets += "================================================`n"

# Convert token.pickle to base64
if (Test-Path "token.pickle") {
    $tokenBase64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes("token.pickle"))
    $secrets += $tokenBase64
    $secrets += "`n`n"
    Write-Host "YOUTUBE_TOKEN_BASE64 generated" -ForegroundColor Green
} else {
    $secrets += "[FILE NOT FOUND - Run: python run_youtube_bot.py]`n`n"
    Write-Host "token.pickle not found" -ForegroundColor Yellow
}

$secrets += "================================================`n"
$secrets += "2. CLIENT_SECRET_JSON`n"
$secrets += "================================================`n"

# Get client_secret.json content
if (Test-Path "client_secret.json") {
    $clientSecret = Get-Content "client_secret.json" -Raw
    $secrets += $clientSecret
    $secrets += "`n`n"
    Write-Host "CLIENT_SECRET_JSON prepared" -ForegroundColor Green
} else {
    $secrets += "[FILE NOT FOUND]`n`n"
    Write-Host "client_secret.json not found" -ForegroundColor Yellow
}

$secrets += "================================================`n"
$secrets += "3. GOOGLE_API_KEY`n"
$secrets += "================================================`n"

# Get API keys from .env
if (Test-Path ".env") {
    $envContent = Get-Content ".env"
    
    $googleApiKey = ($envContent | Select-String "GOOGLE_API_KEY=(.+)").Matches.Groups[1].Value
    if ($googleApiKey) {
        $secrets += $googleApiKey
        $secrets += "`n`n"
        Write-Host "GOOGLE_API_KEY found" -ForegroundColor Green
    } else {
        $secrets += "[NOT FOUND IN .env]`n`n"
        Write-Host "GOOGLE_API_KEY not found in .env" -ForegroundColor Yellow
    }
    
    $secrets += "================================================`n"
    $secrets += "4. YOUTUBE_API_KEY`n"
    $secrets += "================================================`n"
    
    $youtubeApiKey = ($envContent | Select-String "YOUTUBE_API_KEY=(.+)").Matches.Groups[1].Value
    if ($youtubeApiKey) {
        $secrets += $youtubeApiKey
        $secrets += "`n`n"
        Write-Host "YOUTUBE_API_KEY found" -ForegroundColor Green
    } else {
        $secrets += "[NOT FOUND IN .env]`n`n"
        Write-Host "YOUTUBE_API_KEY not found in .env" -ForegroundColor Yellow
    }
    
    $secrets += "================================================`n"
    $secrets += "5. HENRIK_DEV_API_KEY (Optional - for Valorant)`n"
    $secrets += "================================================`n"
    
    $henrikApiKey = ($envContent | Select-String "HENRIK_DEV_API_KEY=(.+)").Matches.Groups[1].Value
    if ($henrikApiKey) {
        $secrets += $henrikApiKey
        $secrets += "`n`n"
        Write-Host "HENRIK_DEV_API_KEY found" -ForegroundColor Green
    } else {
        $secrets += "[OPTIONAL - NOT FOUND]`n`n"
        Write-Host "HENRIK_DEV_API_KEY not found (optional)" -ForegroundColor Gray
    }
} else {
    $secrets += "[.env FILE NOT FOUND]`n`n"
    Write-Host ".env file not found" -ForegroundColor Yellow
}

# Optional: streamer profile
if (Test-Path "streamer_profile.json") {
    $secrets += "================================================`n"
    $secrets += "6. STREAMER_PROFILE_JSON (Optional)`n"
    $secrets += "================================================`n"
    $streamerProfile = Get-Content "streamer_profile.json" -Raw
    $secrets += $streamerProfile
    $secrets += "`n`n"
    Write-Host "STREAMER_PROFILE_JSON prepared" -ForegroundColor Green
}

$secrets += "================================================`n"
$secrets += "NEXT STEPS:`n"
$secrets += "================================================`n"
$secrets += "1. Create GitHub repository (public)`n"
$secrets += "2. Add each secret above to:`n"
$secrets += "   https://github.com/YOUR_USERNAME/REPO_NAME/settings/secrets/actions`n"
$secrets += "3. Push code: git push -u origin main`n"
$secrets += "4. Enable GitHub Actions`n"
$secrets += "5. Done! Bot will auto-start when you stream`n`n"
$secrets += "See GITHUB_ACTIONS_SETUP.md for detailed instructions.`n"
$secrets += "================================================`n"

# Save to file
$secrets | Out-File -FilePath $secretsFile -Encoding UTF8

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "Secrets file created: $secretsFile" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Open this file and copy each secret to GitHub." -ForegroundColor Yellow
Write-Host ""
Write-Host "IMPORTANT: Delete $secretsFile after use!" -ForegroundColor Red
Write-Host "It contains sensitive information!" -ForegroundColor Red
Write-Host ""

# Offer to open the file
$openFile = Read-Host "Open $secretsFile now? (Y/n)"
if ($openFile -ne 'n' -and $openFile -ne 'N') {
    notepad $secretsFile
}
