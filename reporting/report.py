"""
Report generation for FAIR
---------------------------
Produces a structured forensic report as JSON and plain-text (TXT).

The report is designed to be reproducible: another analyst should be able
to read the report and understand exactly which methods were run, with what
settings, and what each output means.
"""

import json
import uuid
from datetime import datetime, timezone


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_report(
    metadata: dict,
    detector_result: dict,
    ela_stats: dict,
    hf_stats: dict,
    analysis_id: str | None = None,
) -> dict:
    """
    Assemble the full forensic report as a Python dict.

    Parameters
    ----------
    metadata        : output of forensics.integrity.extract_metadata()
    detector_result : output of detector.univfd.run_inference()
    ela_stats       : output of forensics.ela.ela_summary()
    hf_stats        : output of forensics.highfreq.highfreq_summary()
    analysis_id     : optional UUID string; generated if None
    """
    if analysis_id is None:
        analysis_id = str(uuid.uuid4())

    report = {
        "fair_report": {
            "version": "1.0",
            "analysis_id": analysis_id,
            "timestamp_utc": _now_iso(),
            "tool": "FAIR — Forensic AI Image Reviewer",
            "disclaimer": (
                "This report is produced for research and educational purposes only. "
                "Findings are investigative indicators, not legal conclusions. "
                "No single method in this report definitively proves an image is fake or real."
            ),
        },
        "input_file": {
            "filename": metadata.get("filename"),
            "file_size_bytes": metadata.get("file_size_bytes"),
            "file_size_kb": metadata.get("file_size_kb"),
            "dimensions": f"{metadata.get('width_px')} x {metadata.get('height_px')} px",
            "colour_mode": metadata.get("colour_mode"),
            "detected_format": metadata.get("detected_format"),
            "exif_present": metadata.get("exif_present"),
            "sha256_digest": metadata.get("sha256"),
            "sha256_note": (
                "SHA-256 verifies file identity (detects byte-level changes). "
                "It does NOT indicate whether image content is authentic."
            ),
        },
        "ai_detector": _format_detector(detector_result),
        "forensic_methods": {
            "error_level_analysis": {
                "method": "ELA — JPEG recompression difference",
                "quality_setting": 90,
                "amplification": 15,
                "statistics": ela_stats,
                "interpretation": (
                    "ELA highlights regions that respond differently to JPEG recompression. "
                    "Brighter regions may indicate editing, format conversion, or high-detail content. "
                    "ELA is NOT proof of manipulation."
                ),
                "limitation": "ELA is affected by previous compression history and image content, not only by editing.",
            },
            "high_frequency_residual": {
                "method": "Gaussian high-pass residual",
                "blur_radius": 2,
                "statistics": hf_stats,
                "interpretation": (
                    "Subtracts a Gaussian-blurred version from the original to isolate fine textures and edges. "
                    "Unusual patterns may appear in AI-generated images but also occur in natural photographs. "
                    "This is an exploratory forensic aid, not a classifier."
                ),
                "limitation": "High-frequency anomalies are not proof of a deepfake.",
            },
        },
        "overall_assessment": _overall_assessment(detector_result),
        "reproducibility": {
            "methods_executed": [
                "SHA-256 integrity digest (hashlib)",
                "Error Level Analysis (PIL JPEG recompression, quality=90, amplify=15)",
                "Gaussian high-pass residual (OpenCV GaussianBlur, radius=2)",
                f"AI detector: {detector_result.get('detector', 'N/A')} — status: {detector_result.get('status', 'unknown')}",
            ],
            "note": (
                "Re-running these methods on the same file (verified by SHA-256) "
                "with the same settings should produce identical visualizations."
            ),
        },
    }
    return report


def _format_detector(result: dict) -> dict:
    status = result.get("status", "unknown")
    if status == "success":
        return {
            "detector": result.get("detector"),
            "backbone": result.get("backbone"),
            "checkpoint": result.get("checkpoint"),
            "status": "success",
            "raw_logit": result.get("raw_logit"),
            "label": result.get("label"),
            "confidence_tier": result.get("confidence"),
            "message": result.get("message"),
            "limitations": result.get("limitations", []),
        }
    else:
        return {
            "detector": "UniversalFakeDetect (UnivFD)",
            "status": status,
            "message": result.get("message", "No message available."),
            "limitations": result.get("limitations", []),
        }


def _overall_assessment(detector_result: dict) -> dict:
    status = detector_result.get("status")
    if status == "success":
        label = detector_result.get("label", "unknown")
        confidence = detector_result.get("confidence", "unknown")
        verdict = "INCONCLUSIVE" if "inconclusive" in confidence.lower() else "SEE FINDINGS"
        return {
            "verdict": verdict,
            "summary": (
                f"AI detector indicates: {label} (confidence: {confidence}). "
                "This result should be considered alongside ELA and high-frequency findings. "
                "No single indicator is conclusive."
            ),
            "responsible_use_note": (
                "Do not use this report to make accusations against any individual. "
                "Seek expert forensic review for consequential decisions."
            ),
        }
    else:
        return {
            "verdict": "INCONCLUSIVE — AI detector unavailable",
            "summary": (
                "The AI detector could not be run. Forensic visualizations (ELA, high-frequency) "
                "are available for human review but do not independently determine authenticity."
            ),
            "responsible_use_note": (
                "Do not use this report to make accusations against any individual. "
                "Seek expert forensic review for consequential decisions."
            ),
        }


def report_to_json(report: dict) -> str:
    """Serialize the report dict to a formatted JSON string."""
    return json.dumps(report, indent=2, ensure_ascii=False)


def report_to_txt(report: dict) -> str:
    """Produce a human-readable plain-text version of the report."""
    r = report
    fr = r["fair_report"]
    inp = r["input_file"]
    det = r["ai_detector"]
    ela = r["forensic_methods"]["error_level_analysis"]
    hf = r["forensic_methods"]["high_frequency_residual"]
    oa = r["overall_assessment"]
    repro = r["reproducibility"]

    lines = [
        "=" * 70,
        "  FAIR — Forensic AI Image Reviewer",
        "  Forensic Analysis Report",
        "=" * 70,
        "",
        f"Analysis ID  : {fr['analysis_id']}",
        f"Timestamp    : {fr['timestamp_utc']}",
        f"Tool version : {fr['version']}",
        "",
        "DISCLAIMER",
        "-" * 70,
        fr["disclaimer"],
        "",
        "INPUT FILE",
        "-" * 70,
        f"Filename     : {inp['filename']}",
        f"Size         : {inp['file_size_kb']} KB ({inp['file_size_bytes']} bytes)",
        f"Dimensions   : {inp['dimensions']}",
        f"Colour mode  : {inp['colour_mode']}",
        f"Format       : {inp['detected_format']}",
        f"EXIF present : {inp['exif_present']}",
        f"SHA-256      : {inp['sha256_digest']}",
        f"SHA-256 note : {inp['sha256_note']}",
        "",
        "AI DETECTOR",
        "-" * 70,
        f"Detector     : {det.get('detector', 'N/A')}",
        f"Status       : {det['status']}",
    ]

    if det["status"] == "success":
        lines += [
            f"Backbone     : {det.get('backbone')}",
            f"Raw logit    : {det.get('raw_logit')}",
            f"Label        : {det.get('label')}",
            f"Confidence   : {det.get('confidence_tier')}",
            f"Message      : {det.get('message')}",
        ]
    else:
        lines.append(f"Message      : {det.get('message')}")

    lines += [
        "",
        "Detector limitations:",
    ]
    for lim in det.get("limitations", []):
        lines.append(f"  • {lim}")

    lines += [
        "",
        "ERROR LEVEL ANALYSIS (ELA)",
        "-" * 70,
        f"Method       : {ela['method']}",
        f"Quality      : {ela['quality_setting']}  |  Amplification: {ela['amplification']}",
        f"Statistics   : mean={ela['statistics'].get('mean_intensity', 'N/A'):.2f}, "
        f"max={ela['statistics'].get('max_intensity', 'N/A'):.2f}, "
        f"std={ela['statistics'].get('std_intensity', 'N/A'):.2f}",
        f"Interpretation: {ela['interpretation']}",
        f"Limitation   : {ela['limitation']}",
        "",
        "HIGH-FREQUENCY RESIDUAL",
        "-" * 70,
        f"Method       : {hf['method']}",
        f"Blur radius  : {hf['blur_radius']}",
        f"Statistics   : mean_dev={hf['statistics'].get('mean_deviation_from_neutral', 'N/A'):.2f}, "
        f"max_dev={hf['statistics'].get('max_deviation_from_neutral', 'N/A'):.2f}, "
        f"std={hf['statistics'].get('std_deviation', 'N/A'):.2f}",
        f"Interpretation: {hf['interpretation']}",
        f"Limitation   : {hf['limitation']}",
        "",
        "OVERALL ASSESSMENT",
        "-" * 70,
        f"Verdict      : {oa['verdict']}",
        f"Summary      : {oa['summary']}",
        f"Responsible use: {oa['responsible_use_note']}",
        "",
        "REPRODUCIBILITY",
        "-" * 70,
        "Methods executed:",
    ]
    for m in repro["methods_executed"]:
        lines.append(f"  • {m}")
    lines += [
        "",
        repro["note"],
        "",
        "=" * 70,
        "  End of FAIR Forensic Report",
        "=" * 70,
    ]

    return "\n".join(lines)
