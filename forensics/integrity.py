"""
File integrity utilities
------------------------
SHA-256 digest and basic file metadata extraction.

NOTE: SHA-256 verifies *file identity* — it confirms that a file has not
been altered since a trusted digest was recorded. It does NOT indicate
whether the image content is authentic or synthetically generated.
"""

import hashlib
import os
from PIL import Image


def sha256_digest(file_bytes: bytes) -> str:
    """Return the hex-encoded SHA-256 digest of the raw file bytes."""
    return hashlib.sha256(file_bytes).hexdigest()


def extract_metadata(file_bytes: bytes, filename: str) -> dict:
    """
    Extract displayable metadata from an uploaded image file.

    Returns a dict with:
      filename, file_size_bytes, file_size_kb, width, height,
      mode (colour space), format (if detectable), sha256
    """
    from io import BytesIO

    digest = sha256_digest(file_bytes)
    size_bytes = len(file_bytes)
    size_kb = round(size_bytes / 1024, 2)

    img = Image.open(BytesIO(file_bytes))
    width, height = img.size
    mode = img.mode
    fmt = img.format if img.format else "unknown"

    # Basic EXIF check (not all images have EXIF)
    exif_present = False
    try:
        exif_data = img._getexif()
        exif_present = exif_data is not None
    except Exception:
        exif_present = False

    return {
        "filename": filename,
        "file_size_bytes": size_bytes,
        "file_size_kb": size_kb,
        "width_px": width,
        "height_px": height,
        "colour_mode": mode,
        "detected_format": fmt,
        "exif_present": exif_present,
        "sha256": digest,
    }
