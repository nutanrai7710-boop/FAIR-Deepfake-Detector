# Windows PowerShell setup script for FAIR
# Run from inside the fair_project/ folder with your venv activated.
# Usage: .\setup.ps1

Write-Host "=== FAIR — Environment Setup ===" -ForegroundColor Cyan

# 1. Core dependencies
Write-Host "`n[1/3] Installing core dependencies..." -ForegroundColor Yellow
pip install streamlit pillow opencv-python numpy ftfy regex tqdm

# 2. CLIP (required for UnivFD — may take a few minutes)
Write-Host "`n[2/3] Installing OpenAI CLIP..." -ForegroundColor Yellow
pip install git+https://github.com/openai/CLIP.git

# 3. PyTorch CPU (required for UnivFD inference)
Write-Host "`n[3/3] Installing PyTorch (CPU)..." -ForegroundColor Yellow
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

Write-Host "`n=== Verification ===" -ForegroundColor Cyan
python -c "import streamlit, PIL, cv2, numpy; print('[OK] Core deps')"
python -c "import clip; print('[OK] CLIP')"
python -c "import torch; print('[OK] PyTorch', torch.__version__)"

Write-Host "`n=== Setup complete ===" -ForegroundColor Green
Write-Host "Run the app with:  streamlit run app.py" -ForegroundColor Green
