# FAIR Project - GitHub Upload Script
# =====================================
# HOW TO USE:
# 1. Revoke your exposed tokens at: https://github.com/settings/tokens
# 2. Generate a NEW token at: https://github.com/settings/tokens/new
#    (tick only "repo" scope, 7 days expiry)
# 3. Paste your new token below where it says: PASTE_YOUR_NEW_TOKEN_HERE
# 4. Save this file
# 5. Run it: .\upload_to_github.ps1

# ======================================================
# PASTE YOUR NEW TOKEN ON THE LINE BELOW (between quotes)
# ======================================================
$TOKEN = "PASTE_YOUR_NEW_TOKEN_HERE"
# ======================================================

$GITHUB_USERNAME = "nutanrai7710-boop"
$REPO_NAME       = "FAIR-Deepfake-Detector"
$COMMIT_MESSAGE  = "FAIR Forensic AI Image Reviewer v1.0 - Full project upload"

# --- Validate token was set ---
if ($TOKEN -eq "PASTE_YOUR_NEW_TOKEN_HERE") {
    Write-Host ""
    Write-Host "ERROR: You must paste your GitHub token into this script first." -ForegroundColor Red
    Write-Host "Open upload_to_github.ps1 and replace PASTE_YOUR_NEW_TOKEN_HERE with your token." -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

# --- Check Git is installed ---
Write-Host ""
Write-Host "Checking Git installation..." -ForegroundColor Cyan
try {
    $gitVersion = git --version 2>&1
    Write-Host "Found: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "Git is not installed." -ForegroundColor Red
    Write-Host "Download and install Git from: https://git-scm.com/download/win" -ForegroundColor Yellow
    Write-Host "Then restart this terminal and run this script again." -ForegroundColor Yellow
    exit 1
}

# --- Remove old git setup if exists ---
if (Test-Path ".git") {
    Write-Host "Removing existing .git folder..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force ".git"
}

# --- Create .gitignore ---
Write-Host "Creating .gitignore..." -ForegroundColor Cyan
@"
# Python
__pycache__/
*.py[cod]
*.pyo
venv/
.venv/
*.egg-info/

# Virtual environment
venv/
env/

# Large model files (too big for GitHub)
*.pth
*.pt
*.bin
*.ckpt

# CLIP model cache
.cache/

# Streamlit
.streamlit/

# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/

# Temp files
*.tmp
*.log
"@ | Out-File -FilePath ".gitignore" -Encoding UTF8

Write-Host "Initialising Git repository..." -ForegroundColor Cyan
git init

Write-Host "Staging all files..." -ForegroundColor Cyan
git add .

Write-Host "Creating commit..." -ForegroundColor Cyan
git commit -m $COMMIT_MESSAGE

Write-Host "Setting branch to main..." -ForegroundColor Cyan
git branch -M main

$REMOTE_URL = "https://$($GITHUB_USERNAME):$($TOKEN)@github.com/$($GITHUB_USERNAME)/$($REPO_NAME).git"

Write-Host "Adding remote origin..." -ForegroundColor Cyan
git remote add origin $REMOTE_URL

Write-Host ""
Write-Host "Pushing to GitHub..." -ForegroundColor Cyan
git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Green
    Write-Host "  SUCCESS! Project uploaded to GitHub." -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Your project is live at:" -ForegroundColor Cyan
    Write-Host "https://github.com/$GITHUB_USERNAME/$REPO_NAME" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "Push failed. Common reasons:" -ForegroundColor Red
    Write-Host "  1. Token is wrong or expired - generate a new one" -ForegroundColor Yellow
    Write-Host "  2. Repository does not exist - create it at https://github.com/new" -ForegroundColor Yellow
    Write-Host "  3. Repository was initialised with a README - delete it and recreate empty" -ForegroundColor Yellow
    Write-Host ""
}
