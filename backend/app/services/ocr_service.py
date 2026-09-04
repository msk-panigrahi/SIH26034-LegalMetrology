"""
OCR Service — extracts raw text from inspection images using Tesseract OCR.

This module provides a clean interface for OCR processing, keeping
OCR logic separate from API routes. Designed to be replaced or extended
with AI/ML-based OCR in later phases.
"""

import logging
import shutil
import os
from pathlib import Path
from typing import Optional

import pytesseract
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Supported image formats for OCR
SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".webp", ".tiff", ".bmp"}


# ---------------------------------------------------------------------------
# Auto-detect Tesseract binary on Windows
# ---------------------------------------------------------------------------


def _find_tesseract_binary() -> Optional[str]:
    """
    Try to locate the tesseract binary.

    1. Check PATH (shutil.which)
    2. Check common Windows install locations
    """
    # 1. Check PATH
    found = shutil.which("tesseract")
    if found:
        logger.info(f"Tesseract found in PATH: {found}")
        return found

    # 2. Common Windows install locations
    common_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"C:\Tesseract-OCR\tesseract.exe",
        os.path.expanduser(r"~\AppData\Local\Tesseract-OCR\tesseract.exe"),
    ]
    for p in common_paths:
        if os.path.isfile(p):
            logger.info(f"Tesseract found at: {p}")
            return p

    logger.warning("Tesseract binary not found. OCR will fail.")
    return None


# Configure pytesseract at module load time
_tesseract_path = _find_tesseract_binary()
if _tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = _tesseract_path



# ---------------------------------------------------------------------------
# Image preprocessing
# ---------------------------------------------------------------------------


def _preprocess_image(image_path: Path) -> Image.Image:
    """
    Apply preprocessing to improve OCR accuracy.

    - Validate image dimensions
    - Convert to RGB (handles RGBA, grayscale, etc.)
    - Resize small images for better OCR
    - Normalize orientation (EXIF)
    - Enhance contrast
    - Enhance sharpness
    - Convert to grayscale for better text recognition
    - Apply mild noise reduction
    """
    img = Image.open(image_path)

    # Auto-rotate based on EXIF orientation
    try:
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass

    # Convert to RGB if necessary (handles PNG with alpha channel, palette mode, etc.)
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    elif img.mode == "L":
        # Already grayscale, convert to RGB for uniform processing
        img = img.convert("RGB")

    # Resize small images - Tesseract works best with 300+ DPI equivalent
    width, height = img.size
    if width < 1000 or height < 1000:
        # Scale up small images more aggressively
        scale = max(1000 / width, 1000 / height, 2.0)
        new_width = int(width * scale)
        new_height = int(height * scale)
        img = img.resize((new_width, new_height), Image.LANCZOS)
        logger.info(f"Resized image from {width}x{height} to {new_width}x{new_height}")

    # Enhance contrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.3)

    # Enhance sharpness
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(1.4)

    # Convert to grayscale for better OCR on text
    img = img.convert("L")

    # Mild noise reduction via median filter (preserve text edges)
    img = img.filter(ImageFilter.MedianFilter(size=3))

    return img


def _preprocess_image_adaptive(image_path: Path) -> list[Image.Image]:
    """
    Generate multiple preprocessing variants for multi-strategy OCR.

    Returns a list of preprocessed images:
    1. Standard preprocessing (grayscale + contrast + sharpen + denoise)
    2. Binarized (Otsu-style threshold) for high-contrast text
    """
    # Standard preprocessing
    standard = _preprocess_image(image_path)

    # Binarized variant: threshold-based for high-contrast text
    try:
        binarized = standard.copy()
        # Apply a threshold to binarize (simple Otsu approximation)
        binarized = binarized.point(lambda x: 0 if x < 140 else 255, '1')
        binarized = binarized.convert('L')
    except Exception:
        binarized = standard

    return [standard, binarized]


# ---------------------------------------------------------------------------
# OCR extraction
# ---------------------------------------------------------------------------


def _try_ocr_with_config(img: Image.Image, language: str, config: str) -> tuple[str, float, int]:
    """
    Try OCR with a specific Tesseract config.
    Returns (raw_text, avg_confidence, word_count).
    """
    data = pytesseract.image_to_data(
        img, lang=language, config=config, output_type=pytesseract.Output.DICT
    )
    texts = []
    confidences = []
    for i, text in enumerate(data["text"]):
        conf = int(data["conf"][i])
        if conf > 0 and text.strip():
            texts.append(text.strip())
            confidences.append(conf)
    raw_text = " ".join(texts)
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
    return raw_text, avg_confidence, len(texts)


def _ocr_quality_score(text: str, confidence: float, word_count: int) -> float:
    """
    Compute a quality score for an OCR result.

    Factors:
    - Average confidence
    - Word count (more words usually means more readable text)
    - Text length (longer text with content is better)
    - Penalty for very short text (likely noise)
    """
    if not text or word_count == 0:
        return 0.0

    # Base score from confidence
    score = confidence

    # Bonus for word count (diminishing returns)
    word_bonus = min(word_count / 50.0, 1.0) * 10
    score += word_bonus

    # Penalty for very short text
    if word_count < 5:
        score *= 0.5
    elif word_count < 10:
        score *= 0.8

    return score


def extract_text_from_image(
    image_path: Path,
    language: str = "eng",
    preprocess: bool = True,
) -> dict:
    """
    Extract raw text from an image using Tesseract OCR.

    Tries multiple PSM modes on multiple preprocessing variants
    and picks the best result based on a quality score.

    Args:
        image_path: Path to the image file.
        language: Tesseract language code (default: "eng" for English).
        preprocess: Whether to apply image preprocessing.

    Returns:
        dict with keys:
            - raw_text: The extracted text as a single string.
            - confidence: Average confidence score (0-100).
            - word_count: Number of words extracted.
            - success: Boolean indicating if OCR succeeded.
            - error: Error message if OCR failed, else None.
            - psm_used: The PSM mode that produced the best result.
            - strategy: Description of the best preprocessing strategy.

    Raises:
        FileNotFoundError: If the image file does not exist.
        ValueError: If the image format is not supported.
    """
    result = {
        "raw_text": "",
        "confidence": 0.0,
        "word_count": 0,
        "success": False,
        "error": None,
        "psm_used": None,
        "strategy": None,
    }

    try:
        # Validate file exists
        if not image_path.exists():
            result["error"] = f"Image file not found: {image_path}"
            logger.error(result["error"])
            return result

        # Validate format
        if image_path.suffix.lower() not in SUPPORTED_FORMATS:
            result["error"] = (
                f"Unsupported image format: {image_path.suffix}. "
                f"Supported: {', '.join(sorted(SUPPORTED_FORMATS))}"
            )
            logger.error(result["error"])
            return result

        # Generate preprocessing variants
        if preprocess:
            images = _preprocess_image_adaptive(image_path)
        else:
            img = Image.open(image_path)
            if img.mode != "L":
                img = img.convert("L")
            images = [img]

        # PSM modes to try — label-aware modes for packaging text
        psm_modes = [
            ("--psm 6", "uniform block"),
            ("--psm 4", "single column"),
            ("--psm 3", "fully automatic"),
            ("--psm 11", "sparse text"),
        ]

        best_text = ""
        best_confidence = 0.0
        best_word_count = 0
        best_score = 0.0
        best_psm = None
        best_strategy = None

        logger.info(f"Running OCR on: {image_path.name} ({len(images)} variants x {len(psm_modes)} PSM modes)")

        for variant_idx, img in enumerate(images):
            strategy_name = f"variant_{variant_idx}"
            if variant_idx == 0:
                strategy_name = "standard"
            elif variant_idx == 1:
                strategy_name = "binarized"

            for config, psm_desc in psm_modes:
                try:
                    text, conf, wc = _try_ocr_with_config(img, language, config)
                    score = _ocr_quality_score(text, conf, wc)

                    if score > best_score:
                        best_text = text
                        best_confidence = conf
                        best_word_count = wc
                        best_score = score
                        best_psm = config
                        best_strategy = strategy_name
                    logger.debug(f"PSM {psm_desc} ({strategy_name}): {wc} words, {conf:.1f}% confidence, score={score:.1f}")
                except Exception as e:
                    logger.debug(f"PSM {psm_desc} ({strategy_name}) failed: {e}")
                    continue

        result["raw_text"] = best_text
        result["confidence"] = round(best_confidence, 2)
        result["word_count"] = best_word_count
        result["success"] = best_word_count > 0
        result["psm_used"] = best_psm
        result["strategy"] = best_strategy

        if not result["success"]:
            result["error"] = "OCR produced no text output"

        logger.info(
            f"OCR complete: {best_word_count} words, "
            f"confidence: {best_confidence:.1f}%, "
            f"strategy: {best_strategy}, PSM: {best_psm}"
        )

    except Exception as e:
        result["error"] = f"OCR processing failed: {str(e)}"
        logger.exception("OCR extraction error")

    return result


def extract_text_simple(
    image_path: Path,
    language: str = "eng",
) -> str:
    """
    Simple OCR extraction returning just the raw text string.

    This is a convenience wrapper for cases where only the text is needed.

    Args:
        image_path: Path to the image file.
        language: Tesseract language code.

    Returns:
        Extracted text as a string, or empty string on failure.
    """
    result = extract_text_from_image(image_path, language)
    return result["raw_text"]
