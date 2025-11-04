# ocr_utils.py — clean OCR helpers for the R-Score app (no Streamlit / Qt)
# Works locally with Tesseract (eng+fra). No API keys or internet required.

from __future__ import annotations
import io
import re
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple

import numpy as np
from PIL import Image

try:
    import pytesseract  # type: ignore
except Exception:  # pragma: no cover
    pytesseract = None  # type: ignore

try:
    import cv2  # type: ignore
except Exception:  # pragma: no cover
    cv2 = None  # type: ignore

try:
    import easyocr  # type: ignore
    _EASYOCR_READER = easyocr.Reader(['en', 'fr'], gpu=False)
except Exception:  # pragma: no cover
    easyocr = None  # type: ignore
    _EASYOCR_READER = None

__all__ = [
    "preprocess_for_ocr",
    "ocr_text",
    "extract_courses_from_text",
    "merge_by_code",
    "extract_from_image_file",
    "extract_from_image_file_debug",
    "CourseRow",
]

# ---------- Patterns ----------
COURSE_CODE = r"\b\d{3}\s*-\s*[A-Z]{2,3}[A-Z]?\s*-\s*[A-Z0-9]{2}\b"  # e.g., 201-SN2-RE
PCT = r"(\d{1,3}(?:[.,]\d{1,2})?)\s*%?"

# Bilingual labels (lowercased comparisons)
LABEL_GRADE = r"(?:your\s*current\s*grade|projected\s*grade|current\s*grade|your\s*grade|note|résultat|resultat|grade)"
LABEL_AVG   = r"(?:class\s*average|moyenne\s*(?:de\s*classe)?|average)"
LABEL_SD    = r"(?:std\.?\s*dev\.?|ecart[- ]?type|écart[- ]?type|standard\s*deviation)"

# ---------- Data model ----------
@dataclass
class CourseRow:
    course_name: str = ""
    class_code: str = ""
    your_grade: float | None = None
    class_avg:  float | None = None
    std_dev:    float | None = None
    credits:    float | None = None
    source:     str = "ocr"

    def to_app_row(self) -> Dict[str, Any]:
        return {
            "Course Name": self.course_name,
            "Your Grade":  self.your_grade,
            "Class Avg":   self.class_avg,
            "Std. Dev":    self.std_dev,
            "Credits":     self.credits,
        }

# ---------- Image pre-processing ----------

def preprocess_for_ocr(pil_img: Image.Image) -> Image.Image:
    """Grayscale → light denoise → adaptive threshold → trim → upscale small images."""
    img = pil_img.convert("L")
    if cv2 is None:
        return img
    arr = np.array(img)
    try:
        arr = cv2.bilateralFilter(arr, d=7, sigmaColor=75, sigmaSpace=75)
        arr = cv2.adaptiveThreshold(arr, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                    cv2.THRESH_BINARY, 35, 10)
        # Trim large white borders
        contours, _ = cv2.findContours(255 - arr, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            x, y, w, h = cv2.boundingRect(np.vstack(contours))
            pad = 6
            x = max(0, x - pad); y = max(0, y - pad)
            arr = arr[y:y + h + 2*pad, x:x + w + 2*pad]
        # Upscale mobile-size screenshots
        H, W = arr.shape
        if max(W, H) < 1500:
            arr = cv2.resize(arr, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)
        return Image.fromarray(arr)
    except Exception:
        return img

# ---------- OCR ----------

def ocr_text(pil_img: Image.Image, lang: str = "eng+fra") -> str:
    # Prefer EasyOCR if available — tends to be more robust on UI screenshots
    if _EASYOCR_READER is not None:
        try:
            np_img = np.array(pil_img.convert('RGB'))
            results = _EASYOCR_READER.readtext(np_img, detail=0, paragraph=True)
            return "\n".join(results)
        except Exception:
            pass  # fall back to Tesseract

    if pytesseract is None:
        raise ImportError(
            "No OCR engine available. Install either easyocr or pytesseract (with tesseract-ocr)."
        )
    prep = preprocess_for_ocr(pil_img)
    # Try a couple of segmentation modes for tougher layouts
    cfgs = ["--oem 1 --psm 6", "--oem 1 --psm 4", "--oem 3 --psm 6"]
    last_txt = ""
    for cfg in cfgs:
        try:
            txt = pytesseract.image_to_string(prep, lang=lang, config=cfg)
            if txt and len(txt) > len(last_txt):
                last_txt = txt
        except Exception:
            continue
    if last_txt:
        return last_txt
    # Absolute fallback
    return pytesseract.image_to_string(prep)

# ---------- Helpers ----------

def _to_float(x: str | None) -> float | None:
    if not x:
        return None
    x = x.replace(",", ".").replace("%", "").strip()
    try:
        return float(x)
    except Exception:
        return None


def _pct_near_label(text: str, label_pat: str) -> float | None:
    t = text.lower()
    m = re.search(rf"{label_pat}[^0-9%]{{0,40}}{PCT}", t)
    if m:
        return _to_float(m.group(1))
    m = re.search(rf"{PCT}[^a-z]{{0,40}}{label_pat}", t)
    if m:
        return _to_float(m.group(1))
    return None


def _fraction_to_pct(text: str) -> float | None:
    m = re.search(r"\b(\d+(?:[.,]\d+)?)\s*/\s*(\d+(?:[.,]\d+)?)\b", text)
    if not m:
        return None
    a = _to_float(m.group(1)); b = _to_float(m.group(2))
    if a is None or b in (None, 0):
        return None
    return round(100.0 * a / b, 2)

# ---------- Parse OCR text into rows ----------

def extract_courses_from_text(text: str) -> List[CourseRow]:
    lines = [ln for ln in text.splitlines() if ln.strip()]
    out: List[CourseRow] = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        code_m = re.search(COURSE_CODE, ln)
        if not code_m:
            i += 1
            continue
        start = max(0, i - 2)
        end   = min(len(lines), i + 8)
        block = "\n".join(lines[start:end])

        # Course name: prefer prev line with letters; else first texty line above
        course_name = ""
        if i > 0:
            prev = lines[i-1].strip()
            if len(re.findall(r"[A-Za-zÀ-ÿ]{3,}", prev)) >= 2:
                course_name = prev
        if not course_name:
            for k in range(start, i):
                cand = lines[k].strip()
                if len(re.findall(r"[A-Za-zÀ-ÿ]{3,}", cand)) >= 2 and not re.search(COURSE_CODE, cand):
                    course_name = cand
                    break

        class_code = code_m.group(0).replace(" ", "")
        your_grade = _pct_near_label(block, LABEL_GRADE)
        class_avg  = _pct_near_label(block, LABEL_AVG)
        std_dev    = _pct_near_label(block, LABEL_SD)
        if your_grade is None:
            frac = _fraction_to_pct(block)
            if frac is not None:
                your_grade = frac

        out.append(CourseRow(course_name=course_name, class_code=class_code,
                             your_grade=your_grade, class_avg=class_avg, std_dev=std_dev))
        i = end  # skip ahead to avoid reusing same block
    return out

# ---------- Merge duplicates ----------

def merge_by_code(rows: List[CourseRow]) -> List[CourseRow]:
    by: Dict[str, CourseRow] = {}
    for r in rows:
        key = r.class_code or r.course_name.strip().lower()
        if key not in by:
            by[key] = r
        else:
            dst = by[key]
            if not dst.course_name and r.course_name: dst.course_name = r.course_name
            if dst.your_grade is None and r.your_grade is not None: dst.your_grade = r.your_grade
            if dst.class_avg  is None and r.class_avg  is not None: dst.class_avg  = r.class_avg
            if dst.std_dev    is None and r.std_dev    is not None: dst.std_dev    = r.std_dev
            if dst.credits    is None and r.credits    is not None: dst.credits    = r.credits
    return list(by.values())

# ---------- Public entry points ----------

def extract_from_image_file_debug(file_bytes: bytes) -> Tuple[List[CourseRow], Dict[str, Any]]:
    """OCR an image and return (rows, debug dict) for logging in the UI."""
    dbg: Dict[str, Any] = {}
    orig = Image.open(io.BytesIO(file_bytes))
    dbg["orig_size"] = orig.size
    dbg["orig_mode"] = orig.mode

    pre = preprocess_for_ocr(orig)
    dbg["pre_size"] = pre.size
    try:
        buf = io.BytesIO()
        pre.save(buf, format="PNG")
        dbg["pre_png"] = buf.getvalue()
    except Exception:
        dbg["pre_png"] = None

    dbg["engine"] = "easyocr" if _EASYOCR_READER is not None else ("tesseract" if pytesseract is not None else "none")
    text = ocr_text(pre)
    dbg["text_len"] = len(text)
    dbg["ocr_sample"] = text[:800]
    dbg["course_code_hits"] = re.findall(COURSE_CODE, text)

    rows = extract_courses_from_text(text)
    dbg["rows_count"] = len(rows)
    dbg["rows_missing"] = {
        "your_grade_missing": sum(1 for r in rows if r.your_grade is None),
        "class_avg_missing":  sum(1 for r in rows if r.class_avg is None),
        "std_dev_missing":    sum(1 for r in rows if r.std_dev is None),
    }
    dbg["rows_preview"] = [r.to_app_row() for r in rows[:5]]
    return rows, dbg


def extract_from_image_file(file_bytes: bytes) -> List[CourseRow]:
    """OCR an image (PNG/JPG bytes) and return parsed CourseRow list."""
    rows, _ = extract_from_image_file_debug(file_bytes)
    return rows