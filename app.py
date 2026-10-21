"""
FAIR — Forensic AI Image Reviewer
===================================
Streamlit application entry point.

Run with:
    streamlit run app.py

Architecture
------------
Image Upload
  → Validation & Metadata (forensics/integrity.py)
  → SHA-256 digest
  → [A] UnivFD AI Detector  (detector/univfd.py)      ← graceful fallback
  → [B] ELA Visualization   (forensics/ela.py)
  → [C] High-Freq Residual  (forensics/highfreq.py)
  → Evidence Summary
  → Downloadable Report     (reporting/report.py)
"""

import sys
import os
import io
import uuid
from PIL import Image
import streamlit as st

# ── resolve project root so sub-packages import correctly ─────────────────────
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from forensics.integrity import extract_metadata
from forensics.ela import generate_ela, ela_summary
from forensics.highfreq import generate_highfreq, highfreq_summary
from reporting.report import build_report, report_to_json, report_to_txt

# ── page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FAIR — Forensic AI Image Reviewer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── custom CSS (cybersecurity dark theme) ─────────────────────────────────────
st.markdown(
    """
    <style>
    /* ── global background ── */
    .stApp { background-color: #0d1117; color: #c9d1d9; }

    /* ── sidebar ── */
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }

    /* ── section cards ── */
    .fair-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 1.2rem 1.4rem;
        margin-bottom: 1.2rem;
    }

    /* ── status badges ── */
    .badge-success { color: #3fb950; font-weight: 700; }
    .badge-warn    { color: #d29922; font-weight: 700; }
    .badge-fail    { color: #f85149; font-weight: 700; }
    .badge-info    { color: #58a6ff; font-weight: 700; }

    /* ── metric labels ── */
    .metric-label { font-size: 0.75rem; color: #8b949e; text-transform: uppercase; letter-spacing: 0.05em; }
    .metric-value { font-size: 1.0rem;  color: #e6edf3; font-family: monospace; }

    /* ── hash display ── */
    .hash-box {
        font-family: monospace;
        font-size: 0.78rem;
        background: #0d1117;
        border: 1px solid #30363d;
        border-radius: 4px;
        padding: 0.5rem 0.8rem;
        word-break: break-all;
        color: #79c0ff;
    }

    /* ── limitation text ── */
    .limitation { font-size: 0.82rem; color: #8b949e; font-style: italic; }

    /* ── section headers ── */
    h2, h3 { color: #e6edf3 !important; }

    /* ── download buttons ── */
    .stDownloadButton > button {
        background-color: #21262d;
        border: 1px solid #30363d;
        color: #c9d1d9;
        border-radius: 6px;
    }
    .stDownloadButton > button:hover {
        background-color: #30363d;
        border-color: #58a6ff;
        color: #58a6ff;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🔍 FAIR")
    st.markdown("**Forensic AI Image Reviewer**")
    st.markdown("---")
    st.markdown(
        """
        **What this tool does**
        - Computes SHA-256 file integrity digest
        - Runs UnivFD AI detector *(if available)*
        - Generates Error Level Analysis (ELA)
        - Generates High-Frequency Residual
        - Produces a downloadable forensic report

        **What this tool does NOT do**
        - Provide definitive proof an image is fake
        - Detect video or audio deepfakes
        - Produce calibrated probabilities
        """
    )
    st.markdown("---")
    st.markdown(
        """
        <div class='limitation'>
        ⚠️ For research & educational use only.<br>
        No single indicator proves authenticity or fabrication.<br>
        Do not use findings to make accusations.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("---")

    # AI Model status in sidebar
    st.markdown("**AI Detector Status**")
    try:
        from detector.univfd import load_model
        model_status = load_model()
        if model_status["status"] == "loaded":
            st.markdown(
                f"<span class='badge-success'>✅ UnivFD loaded ({model_status.get('device','').upper()})</span>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<span class='badge-warn'>⚠️ UnivFD unavailable</span>",
                unsafe_allow_html=True,
            )
            st.caption(model_status.get("message", ""))
    except Exception as e:
        model_status = {"status": "unavailable", "message": str(e)}
        st.markdown(
            "<span class='badge-warn'>⚠️ Detector module not loaded</span>",
            unsafe_allow_html=True,
        )


# ══════════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(
    """
    <h1 style='color:#58a6ff; margin-bottom:0;'>🔍 FAIR</h1>
    <p style='color:#8b949e; margin-top:0; font-size:1.05rem;'>
        Forensic AI Image Reviewer &nbsp;|&nbsp; Explainable Deepfake Detection Platform
    </p>
    <hr style='border-color:#30363d;'>
    """,
    unsafe_allow_html=True,
)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION A — IMAGE UPLOAD
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## 📁 Upload Image for Analysis")

uploaded_file = st.file_uploader(
    "Upload a JPG, JPEG, or PNG image",
    type=["jpg", "jpeg", "png"],
    help="Only image files are accepted. Images are processed locally and not transmitted to any external service.",
)

if uploaded_file is None:
    st.markdown(
        """
        <div class='fair-card'>
        <span class='badge-info'>ℹ️ Awaiting image upload.</span><br><br>
        Upload a JPG, JPEG, or PNG file above to begin the forensic analysis.<br>
        All processing happens locally on your machine.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

# ── Read file bytes once ──────────────────────────────────────────────────────
file_bytes = uploaded_file.read()
if len(file_bytes) == 0:
    st.error("❌ The uploaded file is empty. Please upload a valid image.")
    st.stop()

try:
    image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
except Exception as e:
    st.error(f"❌ Could not open the uploaded file as an image: {e}")
    st.stop()

# Generate a unique ID for this analysis session
analysis_id = str(uuid.uuid4())

# ── Extract metadata ──────────────────────────────────────────────────────────
metadata = extract_metadata(file_bytes, uploaded_file.name)

# ── Display image + metadata ──────────────────────────────────────────────────
col_img, col_meta = st.columns([1, 1])

with col_img:
    st.markdown("### Original Image")
    st.image(image, use_container_width=True)

with col_meta:
    st.markdown("### File Metadata")
    st.markdown(
        f"""
        <div class='fair-card'>
        <p><span class='metric-label'>Filename</span><br>
           <span class='metric-value'>{metadata['filename']}</span></p>

        <p><span class='metric-label'>Dimensions</span><br>
           <span class='metric-value'>{metadata['width_px']} × {metadata['height_px']} px</span></p>

        <p><span class='metric-label'>File Size</span><br>
           <span class='metric-value'>{metadata['file_size_kb']} KB ({metadata['file_size_bytes']:,} bytes)</span></p>

        <p><span class='metric-label'>Colour Mode</span><br>
           <span class='metric-value'>{metadata['colour_mode']}</span></p>

        <p><span class='metric-label'>Detected Format</span><br>
           <span class='metric-value'>{metadata['detected_format']}</span></p>

        <p><span class='metric-label'>EXIF Data Present</span><br>
           <span class='metric-value'>{'Yes' if metadata['exif_present'] else 'No'}</span></p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### SHA-256 Integrity Digest")
    st.markdown(
        f"""
        <div class='fair-card'>
        <div class='hash-box'>{metadata['sha256']}</div>
        <br>
        <span class='limitation'>
        SHA-256 verifies that this exact file has not been byte-modified since the digest was recorded.
        It does <strong>not</strong> indicate whether the image content is authentic or AI-generated.
        </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("---")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION B — AI DETECTOR
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## 🤖 AI Detector — UniversalFakeDetect (UnivFD)")

with st.spinner("Running AI detector..."):
    try:
        from detector.univfd import run_inference
        detector_result = run_inference(image)
    except Exception as e:
        detector_result = {
            "status": "unavailable",
            "message": f"Detector module could not be loaded: {e}",
            "limitations": [
                "UnivFD targets fully AI-generated images; it may not reliably detect face swaps.",
                "The raw logit is not a calibrated probability.",
                "A single model score is not proof of authenticity or fabrication.",
            ],
        }

det_status = detector_result.get("status", "unknown")

with st.container():
    if det_status == "success":
        label = detector_result.get("label", "unknown")
        logit = detector_result.get("raw_logit", 0)
        confidence = detector_result.get("confidence", "unknown")

        badge_color = "badge-fail" if "synthetic" in label else "badge-success"
        badge_icon  = "⚠️" if "synthetic" in label else "✅"

        st.markdown(
            f"""
            <div class='fair-card'>
            <span class='{badge_color}'>{badge_icon} Detector output: <em>{label.upper()}</em></span>
            <br><br>
            <span class='metric-label'>Raw logit</span>
            <span class='metric-value'> {logit}</span>
            &nbsp;&nbsp;&nbsp;
            <span class='metric-label'>Confidence tier</span>
            <span class='metric-value'> {confidence}</span>
            <br><br>
            <span class='limitation'>{detector_result.get('message','')}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.expander("ℹ️ What does this output mean?"):
            st.markdown(
                """
                **UnivFD** extracts visual features using a pretrained CLIP ViT-L/14 vision encoder,
                then passes them through a trained linear classifier.

                - **Raw logit > 0** → model leans toward *synthetic*
                - **Raw logit < 0** → model leans toward *real*
                - **Near 0** → result is near the decision boundary (inconclusive)

                The raw logit is **not a calibrated probability**. Do not interpret it as
                "X% chance of being fake." It is one piece of evidence among several.
                """
            )

    elif det_status == "unavailable":
        st.markdown(
            f"""
            <div class='fair-card'>
            <span class='badge-warn'>⚠️ AI Detector Unavailable</span>
            <br><br>
            <span class='limitation'>{detector_result.get('message','')}</span>
            <br><br>
            The forensic visualizations below (ELA and high-frequency analysis) are fully
            functional and do not depend on the AI model.
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.expander("🔧 How to enable the AI detector"):
            st.markdown(
                """
                **Step 1 — Clone the repository:**
                ```bash
                git clone https://github.com/Yuheng-Li/UniversalFakeDetect
                ```
                Place the cloned folder at `fair_project/UniversalFakeDetect/`

                **Step 2 — Install CLIP:**
                ```bash
                pip install git+https://github.com/openai/CLIP.git
                ```

                **Step 3 — Download the checkpoint:**
                - Get `fc_weights.pth` from the UnivFD releases page
                - Place it at: `fair_project/UniversalFakeDetect/pretrained_weights/fc_weights.pth`

                **Step 4 — Restart this app:**
                ```bash
                streamlit run app.py
                ```
                """
            )
    else:
        st.error(f"Detector error: {detector_result.get('message','')}")

# Detector limitations (always shown)
with st.expander("📋 AI Detector Limitations"):
    for lim in detector_result.get("limitations", []):
        st.markdown(f"- {lim}")

st.markdown("---")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION C — ELA VISUALIZATION
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## 🔬 Error Level Analysis (ELA)")

with st.spinner("Generating ELA visualization..."):
    ela_image = generate_ela(image, quality=90, amplify=15)
    ela_stats_data = ela_summary(ela_image)

col_orig_ela, col_ela = st.columns(2)
with col_orig_ela:
    st.markdown("**Original Image**")
    st.image(image, use_container_width=True)

with col_ela:
    st.markdown("**ELA Visualization** (quality=90, amplify=15)")
    st.image(ela_image, use_container_width=True)

st.markdown(
    f"""
    <div class='fair-card'>
    <span class='metric-label'>ELA Statistics (descriptive only)</span><br>
    <span class='metric-value'>
    Mean intensity: {ela_stats_data['mean_intensity']:.2f} &nbsp;|&nbsp;
    Max intensity: {ela_stats_data['max_intensity']:.2f} &nbsp;|&nbsp;
    Std deviation: {ela_stats_data['std_intensity']:.2f}
    </span>
    <br><br>
    <span class='limitation'>
    ⚠️ <strong>What ELA shows:</strong> Brighter or more uneven regions responded more
    strongly to JPEG recompression. This <em>can</em> result from editing, format conversion,
    or simply from high-detail image content (eyes, text, sharp edges).<br><br>
    <strong>What ELA does NOT prove:</strong> ELA is not a validated deepfake classifier.
    It does not identify the specific manipulated region. Previous compression history
    significantly affects the visualization. These statistics have no validated threshold
    for distinguishing real from fake images.
    </span>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.expander("ℹ️ How ELA works"):
    st.markdown(
        """
        **Procedure:**
        1. The original image is re-saved as a JPEG at quality=90.
        2. The pixel-wise absolute difference between original and re-saved is computed.
        3. Differences are amplified (×15) so they are visible to the human eye.

        **Why it matters in forensics:**
        Regions that have been edited and then re-saved at a different quality level
        sometimes show elevated ELA intensity compared to untouched regions.
        However, this pattern also appears in natural images with sharp edges, text,
        and fine textures — and in images that have been compressed multiple times.

        **Reference:** Krawetz, N. (2007). *A picture's worth: Digital image analysis and forensics.*
        """
    )

st.markdown("---")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION D — HIGH-FREQUENCY RESIDUAL
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## 📡 High-Frequency Residual Analysis")

with st.spinner("Generating high-frequency visualization..."):
    hf_image = generate_highfreq(image, blur_radius=2)
    hf_stats_data = highfreq_summary(hf_image)

col_orig_hf, col_hf = st.columns(2)
with col_orig_hf:
    st.markdown("**Original Image**")
    st.image(image, use_container_width=True)

with col_hf:
    st.markdown("**High-Frequency Residual** (Gaussian blur_radius=2, grayscale)")
    st.image(hf_image, use_container_width=True)

st.markdown(
    f"""
    <div class='fair-card'>
    <span class='metric-label'>High-Frequency Statistics (descriptive only)</span><br>
    <span class='metric-value'>
    Mean deviation from neutral: {hf_stats_data['mean_deviation_from_neutral']:.2f} &nbsp;|&nbsp;
    Max deviation: {hf_stats_data['max_deviation_from_neutral']:.2f} &nbsp;|&nbsp;
    Std deviation: {hf_stats_data['std_deviation']:.2f}
    </span>
    <br><br>
    <span class='limitation'>
    ⚠️ <strong>What high-frequency residual shows:</strong> Fine textures, edges, and
    noise-like patterns isolated from the low-frequency content.<br><br>
    <strong>What it does NOT prove:</strong> High-frequency anomalies are NOT proof of a
    deepfake. AI-generated images <em>sometimes</em> show unusual texture patterns (tiling,
    spectral peaks), but so do natural photographs with fine detail. This visualization
    is an exploratory forensic aid, not a validated classifier.
    </span>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.expander("ℹ️ How high-frequency analysis works"):
    st.markdown(
        """
        **Procedure:**
        1. The image is converted to grayscale.
        2. A Gaussian blur (radius=2) produces a low-pass (smooth) version.
        3. The blurred version is subtracted from the original: `residual = original − blurred`.
        4. The result is shifted to [0, 255] so that 128 = zero residual.

        **Why it matters in forensics:**
        AI image generators sometimes introduce characteristic noise or texture patterns
        in high-frequency components — for example, from upsampling, spectral peaks, or
        GAN-specific artefacts. Analysts use residual visualizations to look for these patterns.

        **Limitation:** Natural photographs with fine hair, fabric, or foliage also produce
        strong high-frequency signals. This method cannot independently classify an image.
        """
    )

st.markdown("---")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION E — EVIDENCE SUMMARY
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## 📊 Evidence Summary")

# Determine overall status
all_inconclusive = det_status in ("unavailable", "error")
if det_status == "success":
    label = detector_result.get("label", "")
    confidence = detector_result.get("confidence", "")
    if "inconclusive" in confidence.lower():
        all_inconclusive = True

if all_inconclusive:
    verdict_html = "<span class='badge-warn'>⚠️ INCONCLUSIVE — insufficient evidence for a definitive finding</span>"
elif "synthetic" in detector_result.get("label", ""):
    verdict_html = "<span class='badge-fail'>⚠️ SUSPICIOUS — AI detector indicates likely synthetic</span>"
else:
    verdict_html = "<span class='badge-success'>✅ AI DETECTOR: likely real — but forensic review advised</span>"

st.markdown(
    f"""
    <div class='fair-card'>
    {verdict_html}
    <br><br>

    <table style='width:100%; border-collapse:collapse;'>
      <tr style='border-bottom:1px solid #30363d;'>
        <td style='padding:0.5rem; color:#8b949e; width:30%;'>AI Detector (UnivFD)</td>
        <td style='padding:0.5rem;'>
          {'<span class="badge-warn">Unavailable</span>' if det_status != 'success'
           else f'<span class="metric-value">{detector_result.get("label","").upper()} — logit: {detector_result.get("raw_logit","N/A")}</span>'}
        </td>
      </tr>
      <tr style='border-bottom:1px solid #30363d;'>
        <td style='padding:0.5rem; color:#8b949e;'>ELA Visualization</td>
        <td style='padding:0.5rem;'>
          <span class='metric-value'>Generated</span>
          &nbsp;<span class='limitation'>— mean={ela_stats_data['mean_intensity']:.1f}, max={ela_stats_data['max_intensity']:.1f}</span>
        </td>
      </tr>
      <tr style='border-bottom:1px solid #30363d;'>
        <td style='padding:0.5rem; color:#8b949e;'>High-Freq Residual</td>
        <td style='padding:0.5rem;'>
          <span class='metric-value'>Generated</span>
          &nbsp;<span class='limitation'>— mean_dev={hf_stats_data['mean_deviation_from_neutral']:.1f}</span>
        </td>
      </tr>
      <tr>
        <td style='padding:0.5rem; color:#8b949e;'>SHA-256 Digest</td>
        <td style='padding:0.5rem;'>
          <span class='metric-value' style='font-size:0.75rem;'>{metadata['sha256'][:32]}…</span>
        </td>
      </tr>
    </table>
    </div>

    <div class='fair-card'>
    <strong style='color:#d29922;'>⚠️ Important Caveats</strong><br><br>
    <ul class='limitation'>
      <li>No single method in this analysis definitively proves or disproves that an image is fake.</li>
      <li>ELA and high-frequency visualizations are exploratory aids, not validated deepfake classifiers.</li>
      <li>The AI detector's logit is not a calibrated probability.</li>
      <li>SHA-256 confirms file integrity, not content authenticity.</li>
      <li>This tool targets image forensics only. Video and audio deepfake detection are not implemented.</li>
      <li>Do not use these findings to make accusations. Seek qualified expert review for consequential decisions.</li>
    </ul>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("---")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION F — FORENSIC REPORT
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## 📄 Forensic Report")

report_dict = build_report(
    metadata=metadata,
    detector_result=detector_result,
    ela_stats=ela_stats_data,
    hf_stats=hf_stats_data,
    analysis_id=analysis_id,
)

report_json_str = report_to_json(report_dict)
report_txt_str  = report_to_txt(report_dict)

col_dl1, col_dl2 = st.columns(2)

with col_dl1:
    st.download_button(
        label="⬇️ Download JSON Report",
        data=report_json_str.encode("utf-8"),
        file_name=f"FAIR_report_{analysis_id[:8]}.json",
        mime="application/json",
        use_container_width=True,
    )

with col_dl2:
    st.download_button(
        label="⬇️ Download TXT Report",
        data=report_txt_str.encode("utf-8"),
        file_name=f"FAIR_report_{analysis_id[:8]}.txt",
        mime="text/plain",
        use_container_width=True,
    )

with st.expander("👁️ Preview JSON Report"):
    st.code(report_json_str, language="json")

with st.expander("👁️ Preview TXT Report"):
    st.code(report_txt_str, language="text")

st.markdown("---")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div style='text-align:center; color:#8b949e; font-size:0.78rem; padding: 1rem 0;'>
        FAIR — Forensic AI Image Reviewer &nbsp;|&nbsp;
        Analysis ID: <code style='color:#79c0ff;'>{analysis_id}</code><br>
        For research and educational purposes only.
        All processing is performed locally. No data is transmitted externally.
    </div>
    """,
    unsafe_allow_html=True,
)
