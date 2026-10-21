"""
High-Frequency Residual Visualization
--------------------------------------
A Gaussian blur is subtracted from the original image to isolate the
high-frequency components (fine edges, textures, noise).

AI-generated images sometimes show unusual patterns in high-frequency
content — tiling artefacts, spectral peaks, or unnaturally smooth regions.

LIMITATION: Unusual high-frequency patterns are NOT proof of a deepfake.
Natural photographs can also show strong texture signals. This is an
exploratory forensic aid, not a validated classifier.
"""

import cv2
import numpy as np
from PIL import Image


def generate_highfreq(image: Image.Image, blur_radius: int = 2) -> Image.Image:
    """
    Generate a high-frequency residual visualization.

    Parameters
    ----------
    image       : PIL.Image  – the uploaded image
    blur_radius : int        – Gaussian blur radius used for low-pass (default 2)

    Returns
    -------
    hf_image : PIL.Image  – residual image scaled for visibility (grayscale)
    """
    # Convert to grayscale numpy array
    gray = np.array(image.convert("L"), dtype=np.float32)

    # Low-pass: Gaussian blur
    ksize = blur_radius * 4 + 1          # must be odd
    blurred = cv2.GaussianBlur(gray, (ksize, ksize), sigmaX=blur_radius)

    # High-pass residual
    residual = gray - blurred            # can be negative

    # Shift to [0, 255] for display (128 = zero residual)
    residual_shifted = np.clip(residual + 128.0, 0, 255).astype(np.uint8)

    hf_image = Image.fromarray(residual_shifted, mode="L").convert("RGB")
    return hf_image


def highfreq_summary(hf_image: Image.Image) -> dict:
    """
    Return basic descriptive statistics for the high-frequency image.
    Descriptive only — not a validated deepfake score.
    """
    arr = np.array(hf_image.convert("L"), dtype=np.float32)
    # Deviation from neutral (128) indicates signal strength
    deviation = np.abs(arr - 128.0)
    return {
        "mean_deviation_from_neutral": float(np.mean(deviation)),
        "max_deviation_from_neutral": float(np.max(deviation)),
        "std_deviation": float(np.std(arr)),
    }
