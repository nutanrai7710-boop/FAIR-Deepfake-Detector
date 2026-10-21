"""
Error Level Analysis (ELA)
--------------------------
ELA works by re-saving a JPEG at a known quality level and then computing
the absolute difference between the original and the re-saved version.

LIMITATION: ELA is NOT proof of manipulation. Bright regions can arise from
any editing, format conversion, or simply from high-detail content. Treat
this visualization as an exploratory aid only.
"""

import io
import numpy as np
from PIL import Image, ImageEnhance


def generate_ela(image: Image.Image, quality: int = 90, amplify: int = 15) -> Image.Image:
    """
    Generate an ELA visualization for the given PIL image.

    Parameters
    ----------
    image   : PIL.Image  – the uploaded image (converted to RGB internally)
    quality : int        – JPEG re-save quality (default 90)
    amplify : int        – brightness multiplier to make differences visible

    Returns
    -------
    ela_image : PIL.Image  – amplified ELA difference image (RGB)
    """
    # Work on a clean RGB copy
    original = image.convert("RGB")

    # Re-save at lower quality into an in-memory buffer
    buffer = io.BytesIO()
    original.save(buffer, format="JPEG", quality=quality)
    buffer.seek(0)
    recompressed = Image.open(buffer).convert("RGB")

    # Compute per-pixel absolute difference
    orig_arr = np.array(original, dtype=np.float32)
    recomp_arr = np.array(recompressed, dtype=np.float32)
    diff = np.abs(orig_arr - recomp_arr)

    # Amplify so small differences become visible
    diff_amplified = np.clip(diff * amplify, 0, 255).astype(np.uint8)

    ela_image = Image.fromarray(diff_amplified, mode="RGB")
    return ela_image


def ela_summary(ela_image: Image.Image) -> dict:
    """
    Return basic descriptive statistics for the ELA image.
    These are descriptive only — not a validated anomaly score.
    """
    arr = np.array(ela_image, dtype=np.float32)
    return {
        "mean_intensity": float(np.mean(arr)),
        "max_intensity": float(np.max(arr)),
        "std_intensity": float(np.std(arr)),
    }
