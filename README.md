# FAIR — Forensic AI Image Reviewer

> Explainable Deepfake Detection & AI Security Platform  
> MSc Cybersecurity Competition Prototype

---

## What FAIR Does

FAIR is an **image forensics platform** that presents multiple, independent lines of
forensic evidence in one interface.  It does **not** claim to definitively detect every
deepfake — it provides honest, explainable, reproducible analysis.

| Feature | Status |
|---|---|
| Image upload & validation | ✅ Working |
| File metadata extraction | ✅ Working |
| SHA-256 integrity digest | ✅ Working |
| Error Level Analysis (ELA) | ✅ Working |
| High-Frequency Residual | ✅ Working |
| UnivFD AI Detector | ⚠️ Requires manual setup (see below) |
| Forensic report (JSON + TXT) | ✅ Working |
| Video / audio deepfake detection | ❌ Not implemented (future work) |

---

## Folder Structure

```
fair_project/
├── app.py                      ← Main Streamlit application
├── requirements.txt            ← Python dependencies
├── setup.ps1                   ← Windows PowerShell setup script
├── forensics/
│   ├── __init__.py
│   ├── integrity.py            ← SHA-256 + metadata
│   ├── ela.py                  ← Error Level Analysis
│   └── highfreq.py             ← High-frequency residual
├── detector/
│   ├── __init__.py
│   └── univfd.py               ← UnivFD integration (graceful fallback)
├── reporting/
│   ├── __init__.py
│   └── report.py               ← JSON + TXT report generation
└── UniversalFakeDetect/        ← Clone here (see AI Detector Setup below)
    └── pretrained_weights/
        └── fc_weights.pth      ← Download checkpoint here
```

---

## Quick Start (Windows + VS Code)

### Step 1 — Create virtual environment

```powershell
cd fair_project
python -m venv venv
.\venv\Scripts\Activate.ps1
```

If you get an execution policy error:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Step 2 — Install dependencies

```powershell
pip install -r requirements.txt
```

For AI detector support, also run:
```powershell
pip install git+https://github.com/openai/CLIP.git
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

### Step 3 — Run the app

```powershell
streamlit run app.py
```

The app opens automatically at **http://localhost:8501**

---

## AI Detector Setup (UnivFD) — Optional

The app works fully without the AI detector.  To enable it:

### 1. Clone the repository

```powershell
git clone https://github.com/Yuheng-Li/UniversalFakeDetect
```

Place the cloned folder inside `fair_project/` so the path is:
```
fair_project/UniversalFakeDetect/
```

### 2. Download the checkpoint

- Visit: https://github.com/Yuheng-Li/UniversalFakeDetect
- Download `fc_weights.pth` from the repository's releases or model links
- Place it at:
  ```
  fair_project/UniversalFakeDetect/pretrained_weights/fc_weights.pth
  ```

### 3. Restart the app

```powershell
streamlit run app.py
```

The sidebar will show **✅ UnivFD loaded** when successful.

---

## Scientific Limitations (Read Before Demo)

- **UnivFD** targets fully AI-generated images. It may not reliably detect face swaps,
  subtle retouching, or novel generation methods outside its training distribution.
- **ELA** is not proof of manipulation. Previous compression history and high-detail
  content areas produce similar visual patterns.
- **High-frequency residual** is an exploratory aid. Natural photographs also show
  strong high-frequency signals.
- **SHA-256** confirms file identity — it does not detect whether content is fake.
- The **raw logit** from UnivFD is not a calibrated probability.
- No single indicator in FAIR is sufficient to declare an image definitively fake.
- FAIR does not implement video or audio deepfake detection.

---

## Competition Demo Script (2–3 minutes)

1. **Upload an image** → show filename, dimensions, SHA-256
2. **AI Detector** → explain what UnivFD does and what the logit means
3. **ELA** → point out bright regions, explain what they do and don't prove
4. **High-Frequency** → explain what the residual isolates
5. **Evidence Summary** → highlight that evidence lanes are independent
6. **Download Report** → show JSON structure — analysis ID, timestamp, methods list
7. **Close with limitations** → "FAIR shows inconclusive when evidence is insufficient,
   because responsible forensics requires honesty about uncertainty."

---

## Future Work

| Extension | Notes |
|---|---|
| Video deepfake detection | Could integrate FaceForensics++ or similar |
| Audio deepfake detection | Could integrate RawNet2 or AASIST |
| Additional image detectors | Ensemble of CNNForensics, Gragnaniello et al. |
| Calibrated probability output | Requires proper calibration dataset + isotonic regression |
| Batch image analysis | Process multiple images, produce comparison reports |

---

## References

- Ojha, U. et al. (2023). *Towards Universal Fake Image Detection Exploiting Vision-Language Models.* CVPR 2023.
- Radford, A. et al. (2021). *Learning Transferable Visual Models From Natural Language Supervision.* ICML 2021.
- Krawetz, N. (2007). *A Picture's Worth: Digital Image Analysis and Forensics.*
- Rossler, A. et al. (2019). *FaceForensics++: Learning to Detect Manipulated Facial Images.* ICCV 2019.

---

*FAIR is a research and educational prototype. It is not a production forensic tool.
Do not use it to make accusations against any individual.*
