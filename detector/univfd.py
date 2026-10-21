"""
UnivFD (UniversalFakeDetect) integration
-----------------------------------------
This module attempts to load and run the official UnivFD pretrained detector.

If the model or its checkpoint is unavailable the module degrades gracefully:
all public functions return a dict with status="unavailable" and a clear
human-readable reason.  The rest of the FAIR application continues normally.

Repository  : https://github.com/Yuheng-Li/UniversalFakeDetect
Paper       : "Towards Universal Fake Image Detection Exploiting Vision-Language Models"
              (Ojha et al., CVPR 2023)

What UnivFD does
----------------
1. Encodes the input image with a pretrained CLIP ViT-L/14 vision encoder.
2. Passes the resulting feature vector through a lightweight linear classifier
   trained to separate real images from AI-generated ones.
3. Returns a raw logit (not a calibrated probability).

LIMITATIONS (important to communicate honestly)
-----------------------------------------------
- Designed primarily for detecting fully AI-generated images, not every face
  swap or photograph retouching.
- Performance may degrade on image types not present in its training set.
- The raw logit is NOT a calibrated probability; do not display it as "X% fake".
- A single model score is not proof of authenticity or fabrication.
"""

import os
import sys
import importlib
from io import BytesIO

# ── paths ──────────────────────────────────────────────────────────────────────
UNIVFD_DIR = os.path.join(os.path.dirname(__file__), "..", "UniversalFakeDetect")
UNIVFD_DIR = os.path.normpath(UNIVFD_DIR)

# Expected checkpoint location (user must download this manually — see README)
CHECKPOINT_PATH = os.path.join(UNIVFD_DIR, "pretrained_weights", "fc_weights.pth")

# ── lazy model cache ───────────────────────────────────────────────────────────
_model_cache = None
_clip_preprocess = None
_device = None


def _try_import_clip():
    try:
        import clip as openai_clip
        return openai_clip
    except ImportError:
        return None


def _try_load_model():
    """
    Attempt to load the UnivFD classifier and CLIP encoder.
    Returns (model, preprocess, device) or raises RuntimeError with a clear message.
    """
    # Check cheap prerequisites BEFORE importing torch (avoids misleading ImportError)
    clip = _try_import_clip()
    if clip is None:
        raise RuntimeError(
            "openai/clip is not installed. "
            "Run: pip install git+https://github.com/openai/CLIP.git"
        )

    if not os.path.isdir(UNIVFD_DIR):
        raise RuntimeError(
            f"UniversalFakeDetect repository not found at {UNIVFD_DIR}. "
            "Clone it with: git clone https://github.com/Yuheng-Li/UniversalFakeDetect"
        )

    if not os.path.isfile(CHECKPOINT_PATH):
        raise RuntimeError(
            f"UnivFD checkpoint not found at {CHECKPOINT_PATH}. "
            "Download fc_weights.pth from the repository releases and place it in "
            f"{os.path.dirname(CHECKPOINT_PATH)}"
        )

    # Now import torch (heavy; only reached when all prerequisites are satisfied)
    try:
        import torch
    except ImportError:
        raise RuntimeError(
            "PyTorch is not installed. "
            "Run: pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu"
        )

    # Add UnivFD to the Python path so we can import its modules
    if UNIVFD_DIR not in sys.path:
        sys.path.insert(0, UNIVFD_DIR)

    try:
        import warnings
        # UnivFD uses CLIP ViT-L/14 as the backbone
        device = "cuda" if torch.cuda.is_available() else "cpu"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            clip_model, preprocess = clip.load("ViT-L/14", device=device)
        clip_model.eval()

        # UnivFD's linear classifier head
        # The FC layer maps 768-dim CLIP features → 1 logit
        fc = torch.nn.Linear(768, 1)
        # weights_only=False required for PyTorch 2.x with legacy checkpoints
        state = torch.load(CHECKPOINT_PATH, map_location=device, weights_only=False)

        # Checkpoint structure confirmed: {"weight": [1,768], "bias": [1]}
        if isinstance(state, dict) and "weight" in state:
            fc.load_state_dict(state)
        elif isinstance(state, dict) and "fc.weight" in state:
            fc.load_state_dict({"weight": state["fc.weight"], "bias": state["fc.bias"]})
        else:
            fc.load_state_dict(state)

        fc = fc.to(device)
        fc.eval()

        return clip_model, fc, preprocess, device

    except Exception as exc:
        raise RuntimeError(f"Failed to load UnivFD model: {exc}") from exc


def load_model():
    """
    Load and cache the UnivFD model.  Returns a status dict.
    Call this once at startup; subsequent calls return the cached result.
    """
    global _model_cache, _clip_preprocess, _device

    if _model_cache is not None:
        return {"status": "loaded", "device": _device, "message": "UnivFD model ready."}

    try:
        clip_model, fc, preprocess, device = _try_load_model()
        _model_cache = (clip_model, fc)
        _clip_preprocess = preprocess
        _device = device
        return {
            "status": "loaded",
            "device": device,
            "message": f"UnivFD loaded successfully on {device.upper()}.",
        }
    except RuntimeError as exc:
        return {"status": "unavailable", "message": str(exc)}


def run_inference(image) -> dict:
    """
    Run UnivFD inference on a PIL image.

    Returns
    -------
    dict with keys:
      status       : "success" | "unavailable" | "error"
      raw_logit    : float (only when status=="success")
      label        : "likely synthetic" | "likely real" (only when status=="success")
      confidence   : "high" | "moderate" | "low" — based on logit magnitude
      message      : human-readable explanation
      limitations  : list of limitation strings
    """
    if _model_cache is None:
        load_status = load_model()
        if load_status["status"] != "loaded":
            return {
                "status": "unavailable",
                "message": load_status["message"],
                "limitations": _limitations(),
            }

    clip_model, fc = _model_cache

    try:
        import torch  # already installed if model loaded successfully
        img_tensor = _clip_preprocess(image).unsqueeze(0).to(_device)

        with torch.no_grad():
            features = clip_model.encode_image(img_tensor).float()
            logit = fc(features).item()

        label = "likely synthetic" if logit > 0 else "likely real"

        # Rough confidence tier based on distance from decision boundary
        abs_logit = abs(logit)
        if abs_logit > 1.5:
            confidence = "high"
        elif abs_logit > 0.5:
            confidence = "moderate"
        else:
            confidence = "low — result is near the decision boundary (inconclusive)"

        return {
            "status": "success",
            "detector": "UniversalFakeDetect (UnivFD)",
            "backbone": "CLIP ViT-L/14",
            "checkpoint": CHECKPOINT_PATH,
            "raw_logit": round(logit, 4),
            "label": label,
            "confidence": confidence,
            "message": (
                f"The model returned a raw logit of {logit:.4f}. "
                f"Values above 0 indicate synthetic; below 0 indicate real. "
                f"This is NOT a calibrated probability."
            ),
            "limitations": _limitations(),
        }

    except Exception as exc:
        return {
            "status": "error",
            "message": f"Inference failed: {exc}",
            "limitations": _limitations(),
        }


def _limitations() -> list:
    return [
        "UnivFD targets fully AI-generated images; it may not reliably detect face swaps or subtle retouching.",
        "The raw logit is not a calibrated probability — do not interpret it as '% fake'.",
        "Performance may degrade on image types outside its training distribution.",
        "A single model score is not proof of authenticity or fabrication.",
        "Results should always be considered alongside other forensic evidence.",
    ]
