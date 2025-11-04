import os
import shutil
import io
import re
from typing import List, Dict, Any

import numpy as np
import pandas as pd
import requests
import streamlit as st
import plotly.express as px

# -------------------------------------------------
# basic page config
# -------------------------------------------------
st.set_page_config(page_title="R-Score Dashboard", layout="wide")

# -------------------------------------------------
# Supabase creds from Streamlit secrets
# -------------------------------------------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_ANON_KEY"]

AUTH_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Content-Type": "application/json",
}

def show_login():
    st.title("Sign in to RScoreCalc")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    c1, c2 = st.columns(2)

    # sign in
    with c1:
        if st.button("Sign in"):
            url = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"
            payload = {"email": email, "password": password}
            r = requests.post(url, json=payload, headers=AUTH_HEADERS)
            if r.status_code == 200:
                data = r.json()
                st.session_state["auth"] = data
                st.success("Logged in.")
                st.rerun()
            else:
                st.error(f"Login failed: {r.text}")

    # sign up
    with c2:
        if st.button("Create account"):
            url = f"{SUPABASE_URL}/auth/v1/signup"
            payload = {"email": email, "password": password}
            r = requests.post(url, json=payload, headers=AUTH_HEADERS)
            if r.status_code in (200, 201):
                st.success("Account created. Check your email to confirm.")
            else:
                st.error(f"Signup failed: {r.text}")


# if not logged in -> show login and stop
if "auth" not in st.session_state:
    show_login()
    st.stop()

auth = st.session_state["auth"]
access_token = auth["access_token"]
user_id = auth["user"]["id"]

# get profile row from Supabase
profiles_url = f"{SUPABASE_URL}/rest/v1/profiles"
headers_authed = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {access_token}",
}
params = {
    "id": f"eq.{user_id}",
    "select": "id,is_premium",
}
resp = requests.get(profiles_url, headers=headers_authed, params=params)
rows = resp.json() if resp.ok else []

if rows:
    st.session_state["is_premium"] = bool(rows[0].get("is_premium", False))
else:
    # user exists in auth but not in profiles — treat as free
    st.session_state["is_premium"] = False
if "tos_accepted" not in st.session_state:
    st.session_state.tos_accepted = False

if not st.session_state.tos_accepted:
    # ... your TOS markdown ...
    agree = st.checkbox("I have read and agree to these Terms of Use.")
    if st.button("Agree and enter"):
        if agree:
            st.session_state.tos_accepted = True
            st.rerun()
        else:
            st.warning("Please check the box to agree.")
    st.stop()

def require_premium():
    if not st.session_state.get("is_premium", False):
        st.markdown("### 🔒 Premium feature")
        st.write("This section is for premium accounts.")
        st.stop()
# --- Ensure Tesseract finds its language data ---
# Check common tessdata directories across macOS and Linux
for td in (
    "/opt/homebrew/share/tessdata",              # macOS Homebrew
    "/usr/local/share/tessdata",                 # Linux local installs
    "/usr/share/tesseract-ocr/5/tessdata",       # Ubuntu 22.04+ (Streamlit Cloud)
    "/usr/share/tesseract-ocr/4.00/tessdata",    # Older Linux systems
):
    if os.path.isdir(td):
        os.environ.setdefault("TESSDATA_PREFIX", td)
        print(f"[INFO] Tesseract data found at: {td}")
        break
try:
    import pytesseract  # type: ignore
    # Prefer PATH first, then common Linux, then macOS:
    candidates = [
        shutil.which("tesseract"),
        "/usr/bin/tesseract",
        "/usr/local/bin/tesseract",
        "/opt/homebrew/bin/tesseract",          # macOS (Apple Silicon)
        "C:\\Program Files\\Tesseract-OCR\\tesseract.exe",  # Windows (optional)
    ]
    for p in candidates:
        if p and os.path.isfile(p):
            pytesseract.pytesseract.tesseract_cmd = p
            break

    # Find tessdata (language models) – Linux, then others:
    td_candidates = [
        os.environ.get("TESSDATA_PREFIX"),
        "/usr/share/tesseract-ocr/5/tessdata",
        "/usr/share/tesseract-ocr/4.00/tessdata",
        "/usr/share/tesseract-ocr/tessdata",
        "/usr/local/share/tessdata",
        "/opt/homebrew/share/tessdata",
    ]
    for td in td_candidates:
        if td and os.path.isdir(td):
            os.environ["TESSDATA_PREFIX"] = td
            break
except Exception:
    pass
# --- OCR import and fallback ---
# === Local OCR helpers (self-contained; do NOT rely on ocr_utils) ===
import re, io
from typing import List, Dict, Any
try:
    from PIL import Image
except Exception:
    Image = None  # type: ignore
try:
    import cv2  # type: ignore
except Exception:
    cv2 = None  # type: ignore

def _local_tesseract_status():
    """Report whether pytesseract and the tesseract binary are usable."""
    status = {"has_pytesseract": False, "binary_ok": False, "version": None, "error": None}
    try:
        import pytesseract as _pt
        status["has_pytesseract"] = True
        try:
            v = _pt.get_tesseract_version()
            status["binary_ok"] = True
            status["version"] = str(v)
        except Exception as e:
            status["error"] = str(e)
    except Exception as e:
        status["error"] = str(e)
    return status

def _preprocess_gray(pil_img):
    """Light denoise + binarize + upscale for better OCR."""
    if Image is None:
        return None
    img = pil_img.convert("L")
    if cv2 is None:
        return img
    import numpy as _np
    arr = _np.array(img)
    try:
        arr = cv2.bilateralFilter(arr, d=5, sigmaColor=55, sigmaSpace=55)
        arr = cv2.adaptiveThreshold(arr, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                    cv2.THRESH_BINARY, 35, 10)
        h, w = arr.shape
        if max(h, w) < 1500:
            arr = cv2.resize(arr, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)
        return Image.fromarray(arr)
    except Exception:
        return img

COURSE_CODE_RE = re.compile(
    r"\b\d{3}\s*-\s*[A-Z0-9]{2,4}\s*-\s*[A-Z0-9]{2,3}\b",
    re.I,
)
NAV_JUNK_PREFIXES = tuple([
    "assignments", "calendar", "class forum", "course documents", "grades",
    "list of my absences", "online classes", "recommended websites",
    "teachers info", "my services", "team forums", "current average",
    "omnivox", "léa", "angus beauregard", "john abbott college"
])
def _clean_course_name(name: str) -> str:
    if not name:
        return ""
    s = str(name)

    # Normalize punctuation
    s = s.replace("—", "-").replace("–", "-")
    s = s.replace("|", " ").replace("»", " ").replace("«", " ")

    # Drop row-number prefixes like "1." / "2."
    s = re.sub(r"^[\s|>•\-]*\d+\.\s*", "", s)

    # Remove any known left-nav prefixes, headers, or user name artifacts
    s_low = s.lower().strip()
    for pref in NAV_JUNK_PREFIXES:
        if s_low.startswith(pref):
            s = s[len(pref):].lstrip(" :>-,.|")
            s_low = s.lower().strip()

    # Remove embedded crumbs such as "Course documents >" or "Team Forums >"
    s = re.sub(r"(?i)course\s*documents\s*>\s*", "", s)
    s = re.sub(r"(?i)team\s*forums\s*>\s*", "", s)

    # --- Strip numeric noise from course names ---
    # 1) Fractions like "19.3/23" anywhere in the string
    s = re.sub(r"\b\d+(?:[.,]\d+)?\s*/\s*\d+(?:[.,]\d+)?\b", "", s)
    # 2) Trailing percentages or numeric tokens like "84", "84%", "42.2" etc.
    s = re.sub(r"(?:\s*\b\d{1,3}(?:[.,]\d{1,2})?\s*%?)+\s*$", "", s)
    # 3) Any stray leading numbers that remain
    s = re.sub(r"^\s*\d+\s*", "", s)

    # Final guard: drop any remaining digits anywhere in the name
    s = re.sub(r"\d+", "", s)

    # Trim trailing dashes and punctuation
    s = re.sub(r"\s*--+\s*$", "", s)
    s = s.strip(" .-–—")

    # HARD RULE: allow only letters (incl. accents) and spaces — remove any other symbols
    # This prevents artifacts like "? . General Chemistry"
    s = re.sub(r"[^A-Za-zÀ-ÿ\s]", " ", s)

    # Collapse whitespace (again after symbol stripping)
    s = re.sub(r"\s+", " ", s).strip()

    # Guard against heading-like leftovers becoming names
    if s.lower() in ("current average", "team forums", "assignments", "calendar",
                     "list of my absences", "teachers info", "recommended websites"):
        return ""

    return s

PCT_RE = re.compile(r"(\d{1,3}(?:[.,]\d{1,2})?)\s*%")
# Labels used on both desktop and mobile layouts
LABEL_GRADE_RE = re.compile(r"(?i)(?:projected\s*grade|your\s*grade|current\s*grade|note|resultat|résultat)\s*[:\-]?\s*(\d{1,3}(?:[.,]\d{1,2})?)\s*%")
LABEL_AVG_RE   = re.compile(r"(?i)(?:class\s*average|moyenne(?:\s*de\s*classe)?)\s*[:\-]?\s*(\d{1,3}(?:[.,]\d{1,2})?)\s*%")
# Expanded label patterns (cover "avg" shorthand and more EN/FR variants)
LABEL_GRADE_RE_ALT = re.compile(
    r"(?i)\b(?:grade|current\s*grade|projected\s*grade|résultat|resultat)\b[^0-9%]{0,40}(\d{1,3}(?:[.,]\d{1,2})?)\s*%"
)
LABEL_AVG_RE_ALT = re.compile(
    r"(?i)\b(?:avg|average|class\s*avg|class\s*average|moyenne(?:\s*de\s*classe)?)\b[^0-9%]{0,40}(\d{1,3}(?:[.,]\d{1,2})?)\s*%"
)

def _extract_grade_avg_from_block(block: str):
    """
    Prefer labeled values; then fractions a/b -> %; then generic percent fallback.
    This avoids mixing 'Your Grade' and 'Class Avg' and recovers missing avgs.
    """
    your_grade = None
    class_avg = None

    # 1) Labeled values (any of the patterns)
    mg = LABEL_GRADE_RE.search(block) or LABEL_GRADE_RE_ALT.search(block)
    ma = LABEL_AVG_RE.search(block)   or LABEL_AVG_RE_ALT.search(block)
    if mg:
        your_grade = _to_float(mg.group(1))
    if ma:
        class_avg = _to_float(ma.group(1))

    # 2) Fractions like "47.3/89.01" → your grade %
    if your_grade is None:
        frac = _fraction_to_pct(block)
        if frac is not None:
            your_grade = frac

    # 3) Directional proximity (percent near 'avg' or 'grade' tokens)
    if class_avg is None:
        m = re.search(rf"(?i){PCT_RE.pattern}[^a-z]{{0,40}}(?:avg|average|class\s*average|class\s*avg|moyenne)", block)
        if m:
            class_avg = _to_float(m.group(1))
    if your_grade is None:
        m = re.search(rf"(?i)(?:grade|current\s*grade|projected\s*grade|résultat|resultat)[^0-9%]{{0,40}}{PCT_RE.pattern}", block)
        if m:
            your_grade = _to_float(m.group(1))

    # 4) Generic fallback: first % = grade, last % = class avg
    if your_grade is None or class_avg is None:
        pcts = [ _to_float(p) for p in PCT_RE.findall(block) ]
        pcts = [p for p in pcts if p is not None and p <= 100]
        if pcts:
            if your_grade is None:
                your_grade = pcts[0]
            if class_avg is None and len(pcts) >= 2:
                class_avg = pcts[-1]

    return your_grade, class_avg
def _to_float(s):
    if not s: return None
    s = s.replace(",", ".").replace("%", "").strip()
    try:
        return float(s)
    except Exception:
        return None

def _fraction_to_pct(text):
    m = re.search(r"\b(\d+(?:[.,]\d+)?)\s*/\s*(\d+(?:[.,]\d+)?)\b", text)
    if not m: return None
    a = _to_float(m.group(1)); b = _to_float(m.group(2))
    if a is None or not b: return None
    if b == 0: return None
    return round(100.0 * a / b, 2)

def _parse_omnivox_text(text: str) -> List[Dict[str, Any]]:
    """Parse Omnivox 'Grades' screenshots text into course rows.

    Strategy:
      - Pass 1: For each line that contains a Quebec-style class code (e.g., 201-SN2-RE),
        treat that line as the anchor for the row. Prefer the two percentages found on
        that same line as (your_grade, class_avg). Course name is taken from the
        closest previous human-readable line (ignoring left-nav/header junk).
      - Pass 2: If very few rows were found, fall back to numbered-row parsing.
    """
    lines = [ln for ln in text.splitlines() if ln.strip()]
    rows: List[Dict[str, Any]] = []

    def is_junk_line(s: str) -> bool:
        t = (s or "").strip().lower()
        if not t:
            return True
        if any(k in t for k in ("omnivox", "john abbott college", "angus beauregard")):
            return True
        if any(t.startswith(p) for p in NAV_JUNK_PREFIXES):
            return True
        # obvious headings
        if re.search(r"current\s*grade", t) or re.search(r"class\s*average", t):
            return True
        # sidebar crumbs with '>'
        if ">" in t and len(t) <= 40:
            return True
        return False

    i = 0
    while i < len(lines):
        ln = lines[i]
        m = COURSE_CODE_RE.search(ln)
        if not m:
            i += 1
            continue

        class_code = m.group(0).replace(" ", "")

        # --- Percentages: prefer those on the same line as the code ---
        pcts_on_line = [ _to_float(p) for p in PCT_RE.findall(ln) ]
        pcts_on_line = [p for p in pcts_on_line if p is not None and p <= 100]
        your_grade = None
        class_avg  = None

        # Look a wider surrounding window and use robust extractor
        start = max(0, i - 4)
        end   = min(len(lines), i + 8)
        # Split the neighborhood around the code line into pre/post.
        # We will **prefer values after the code line** to prevent pulling
        # the previous card's percentages (which caused a one-row offset).
        block_pre  = "\n".join(lines[start:i])
        block_post = "\n".join(lines[i:end])

        # Prefer values that appear after the code line
        yg, ca = _extract_grade_avg_from_block(block_post)
        if your_grade is None:
            your_grade = yg
        if class_avg is None:
            class_avg = ca
        # Final fallback: if still missing, allow pre-code block (rare)
        if (your_grade is None or class_avg is None) and block_pre:
            yg2, ca2 = _extract_grade_avg_from_block(block_pre)
            if your_grade is None:
                your_grade = yg2
            if class_avg is None:
                class_avg = ca2

        # Fallback: if still missing and two percents are on the code line, map [first,last] → [grade, avg]
        if (your_grade is None or class_avg is None) and len(pcts_on_line) >= 2:
            if your_grade is None:
                your_grade = pcts_on_line[0]
            if class_avg is None:
                class_avg = pcts_on_line[-1]

        # --- Course name: search upward for a clean, non-junk line ---
        course_name = ""
        for k in range(i-1, max(-1, i-4), -1):
            if k < 0:
                break
            cand = _clean_course_name(lines[k])
            if cand and not is_junk_line(cand) and not COURSE_CODE_RE.search(cand):
                course_name = cand
                break

        # Last resort: look slightly below, then bail if it smells like junk
        if not course_name:
            for k in range(i+1, min(len(lines), i+4)):
                cand = _clean_course_name(lines[k])
                if cand and not is_junk_line(cand) and not COURSE_CODE_RE.search(cand):
                    course_name = cand
                    break

        # Filter out clear junk rows
        if not course_name or is_junk_line(course_name):
            i += 1
            continue

        rows.append({
            "Course Name": course_name,
            "Class Code": class_code,
            "Your Grade": your_grade,
            "Class Avg": class_avg,
            "Std. Dev": None,
            "Credits": None,
        })
        i += 1

    # Build a set of seen keys (class code or normalized name) to avoid duplicates
    seen_keys = set()
    for r in rows:
        key = (r.get("Class Code") or "").strip()
        if key:
            seen_keys.add(("code", key))
        nm = _clean_course_name(r.get("Course Name", ""))
        if nm:
            seen_keys.add(("name", nm.lower()))

    # ---- Pass 2: numbered rows scan (summary table) ----
    # We always run this to capture any rows the code-anchored pass missed.
    blocks, cur = [], []
    for ln in lines:
        if re.match(r"^\s*\d+\.\s*$", ln) or re.match(r"^\s*\d+\.\s", ln):
            if cur:
                blocks.append("\n".join(cur))
                cur = []
            cur.append(ln)
        else:
            cur.append(ln)
    if cur:
        blocks.append("\n".join(cur))

    for block in blocks:
        bl = [b.strip() for b in block.splitlines() if b.strip()]
        if not bl:
            continue

        # Course name: first plausible alpha line after the row number
        course_name = ""
        for b in bl[1:5]:
            cand = _clean_course_name(b)
            if cand and not COURSE_CODE_RE.search(cand) and len(re.findall(r"[A-Za-zÀ-ÿ]{3,}", cand)) >= 2:
                course_name = cand
                break
        if not course_name:
            continue

        # Class code within block (optional)
        class_code = ""
        for b in bl:
            m = COURSE_CODE_RE.search(b)
            if m:
                class_code = m.group(0).replace(" ", "")
                break

        # Robust extraction for numbered table blocks
        your_grade, class_avg = _extract_grade_avg_from_block(block)

        # Skip if we already have this row from pass 1
        key_code = ("code", class_code) if class_code else None
        key_name = ("name", course_name.lower())
        if (key_code and key_code in seen_keys) or key_name in seen_keys:
            continue

        rows.append({
            "Course Name": course_name,
            "Class Code": class_code,
            "Your Grade": your_grade,
            "Class Avg": class_avg,
            "Std. Dev": None,
            "Credits": None,
        })
        if key_code:
            seen_keys.add(key_code)
        seen_keys.add(key_name)

    # ---- Pass 3: mobile "Projected grade" cards ----
    # Anchor each card to its own label lines to avoid leaking % from neighboring cards.
    for idx, ln in enumerate(lines):
        if not re.search(r"(?i)projected\s*grade", ln):
            continue

        # Card bounds: from this "Projected grade" to the next one (exclusive)
        next_proj = len(lines)
        for k in range(idx + 1, len(lines)):
            if re.search(r"(?i)projected\s*grade", lines[k]):
                next_proj = k
                break

        # Tight block just for this card
        block_lines = lines[idx:next_proj]
        block_text = "\n".join(block_lines)

        # --- Your grade: prefer the % on the same (or immediate next) "Projected grade" line ---
        your_grade = None
        for j in range(idx, min(next_proj, idx + 3)):
            if re.search(r"(?i)projected\s*grade", lines[j]):
                m_pct = PCT_RE.search(lines[j])
                if m_pct:
                    your_grade = _to_float(m_pct.group(1))
                    break
        # Fallback to the last labeled 'grade' inside the card only
        if your_grade is None:
            m_all = list(LABEL_GRADE_RE.finditer(block_text)) + list(LABEL_GRADE_RE_ALT.finditer(block_text))
            if m_all:
                your_grade = _to_float(m_all[-1].group(1))
            else:
                # final fallback: a/b → %
                frac = _fraction_to_pct(block_text)
                if frac is not None:
                    your_grade = frac

        # --- Class average: look within this card only ---
        class_avg = None
        for j in range(idx, next_proj):
            if re.search(r"(?i)(class\s*average|class\s*avg|moyenne)", lines[j]):
                m_pct = PCT_RE.search(lines[j])
                if m_pct:
                    class_avg = _to_float(m_pct.group(1))
                    break
        if class_avg is None:
            m_all = list(LABEL_AVG_RE.finditer(block_text)) + list(LABEL_AVG_RE_ALT.finditer(block_text))
            if m_all:
                class_avg = _to_float(m_all[-1].group(1))

        # If neither value is found within this card, skip
        if your_grade is None and class_avg is None:
            continue

        # --- Class code: search close to the card only (a few lines above or within) ---
        class_code = ""
        for j in range(max(0, idx - 5), next_proj):
            m = COURSE_CODE_RE.search(lines[j])
            if m:
                class_code = m.group(0).replace(" ", "")
                break

        # --- Course name: the nearest clean alpha line above the 'Projected grade' label ---
        course_name = ""
        for j in range(idx - 1, max(0, idx - 6) - 1, -1):
            cand = _clean_course_name(lines[j])
            if cand and not COURSE_CODE_RE.search(cand) and len(re.findall(r"[A-Za-zÀ-ÿ]{3,}", cand)) >= 2:
                course_name = cand
                break

        key_code = ("code", class_code) if class_code else None
        key_name = ("name", course_name.lower()) if course_name else None
        if (key_code and key_code in seen_keys) or (key_name and key_name in seen_keys):
            continue

        rows.append({
            "Course Name": course_name,
            "Class Code": class_code,
            "Your Grade": your_grade,
            "Class Avg": class_avg,
            "Std. Dev": None,
            "Credits": None,
        })
        if key_code:
            seen_keys.add(key_code)
        if key_name:
            seen_keys.add(key_name)
    return rows

def app_extract_from_image_bytes(file_bytes: bytes):
    """
    Always-available OCR path used by the Import tab.
    Returns (rows, engine_status, text_preview).
    """
    status = _local_tesseract_status()
    if Image is None:
        return [], {**status, "error": "Pillow not available"}, ""
    if not (status["has_pytesseract"] and status["binary_ok"]):
        return [], status, ""
    import pytesseract as _pt
    img = Image.open(io.BytesIO(file_bytes))
    prep = _preprocess_gray(img)
    text = ""
    last_err = None
    for cfg in ["--oem 1 --psm 6", "--oem 1 --psm 4", "--oem 1 --psm 3"]:
        try:
            t = _pt.image_to_string(prep, lang="eng+fra", config=cfg)
            text = t or ""
            # Accept as soon as we see a class code or labeled fields
            if COURSE_CODE_RE.search(text) or re.search(r"(?i)projected\s*grade", text):
                break
        except Exception as e:
            last_err = e
    if text == "" and last_err is not None:
        return [], {**status, "error": str(last_err)}, ""
    rows = _parse_omnivox_text(text or "")
    return rows, status, (text or "")[:800]

# ---- Normalize & merge (works for dicts *or* dataclass objects) ----
_DEF_FIELDS = ["Course Name","Class Code","Your Grade","Class Avg","Std. Dev","Credits"]

def _row_to_dict_any(r):
    """Return a uniform dict regardless of input row type."""
    if isinstance(r, dict):
        d = {k: v for k, v in r.items()}
        # normalize common alt keys
        d.setdefault("Course Name", d.get("course_name", ""))
        d.setdefault("Class Code", d.get("class_code", ""))
        d.setdefault("Your Grade", d.get("your_grade"))
        d.setdefault("Class Avg",  d.get("class_avg"))
        d.setdefault("Std. Dev",   d.get("std_dev"))
        d.setdefault("Credits",    d.get("credits"))
    else:
        d = {
            "Course Name": getattr(r, "Course Name", None) or getattr(r, "course_name", ""),
            "Class Code": getattr(r, "Class Code", None) or getattr(r, "class_code", ""),
            "Your Grade": getattr(r, "Your Grade", None) or getattr(r, "your_grade", None),
            "Class Avg":  getattr(r, "Class Avg",  None) or getattr(r, "class_avg",  None),
            "Std. Dev":   getattr(r, "Std. Dev",   None) or getattr(r, "std_dev",   None),
            "Credits":    getattr(r, "Credits",    None) or getattr(r, "credits",    None),
        }
    # string cleanups
    d["Course Name"] = (d.get("Course Name") or "").strip()
    d["Class Code"]  = (d.get("Class Code")  or "").strip()
    return {k: d.get(k) for k in _DEF_FIELDS}


def app_merge_rows_any(rows):
    """Merge rows by Class Code (fallback Course Name) filling missing values.
    Works whether rows are dicts or dataclass CourseRow objects.
    """
    merged = {}
    for r in rows:
        dr = _row_to_dict_any(r)
        key = dr.get("Class Code") or dr.get("Course Name", "").lower()
        if not key:
            continue
        if key not in merged:
            merged[key] = dr
        else:
            dst = merged[key]
            if not dst.get("Course Name") and dr.get("Course Name"):
                dst["Course Name"] = dr["Course Name"]
            for fld in ["Your Grade","Class Avg","Std. Dev","Credits"]:
                if (dst.get(fld) is None or dst.get(fld) == "") and (dr.get(fld) not in (None, "")):
                    dst[fld] = dr[fld]
    return list(merged.values())
# Try to use external ocr_utils if it exists; otherwise shim to our local OCR.
try:
    import importlib
    import ocr_utils as _ocr_utils
    ocr_utils = importlib.reload(_ocr_utils)
except Exception:
    import types
    ocr_utils = types.SimpleNamespace()

    # Use our local pipeline so callers can keep using the legacy functions.
    def _shim_extract_from_image_file(file_bytes: bytes):
        rows, _status, _preview = app_extract_from_image_bytes(file_bytes)
        return rows

    def _shim_merge_by_code(rows):
        return app_merge_rows_any(rows)

    ocr_utils.extract_from_image_file = _shim_extract_from_image_file
    ocr_utils.merge_by_code = _shim_merge_by_code
# --- OCR aliases for legacy call sites ---
# If any old code still calls the bare function names, route them to the module.
def extract_from_image_file(file_bytes):
    return ocr_utils.extract_from_image_file(file_bytes)

def merge_by_code(rows):
    return ocr_utils.merge_by_code(rows)

# ---- Fallback OCR implementation if ocr_utils lacks the expected API ----
try:
    import re, io
    from dataclasses import dataclass
    from typing import List, Dict, Any
    from PIL import Image
    try:
        import pytesseract  # type: ignore
    except Exception:  # pragma: no cover
        pytesseract = None  # type: ignore
    try:
        import cv2  # type: ignore
    except Exception:  # pragma: no cover
        cv2 = None  # type: ignore

    if not hasattr(ocr_utils, 'extract_from_image_file') or not hasattr(ocr_utils, 'merge_by_code'):
        COURSE_CODE = r"\b\d{3}\s*-\s*[A-Z0-9]{2,4}\s*-\s*[A-Z0-9]{2,3}\b"
        PCT = r"(\d{1,3}(?:[.,]\d{1,2})?)\s*%"
        LABEL_GRADE = r"(?:your\s*current\s*grade|projected\s*grade|current\s*grade|note|resultat|result)"
        LABEL_AVG   = r"(?:class\s*average|moyenne\s*de\s*classe|moyenne|average)"
        LABEL_SD    = r"(?:std\.?\s*dev\.?|ecart[- ]?type|standard\s*deviation)"

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

        def _preprocess_for_ocr(pil_img: Image.Image) -> Image.Image:
            img = pil_img.convert("L")
            if cv2 is None:
                return img
            arr = np.array(img)
            try:
                arr = cv2.bilateralFilter(arr, d=5, sigmaColor=55, sigmaSpace=55)
                arr = cv2.adaptiveThreshold(arr, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                            cv2.THRESH_BINARY, 35, 10)
                # trim borders
                contours, _ = cv2.findContours(255 - arr, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                if contours:
                    x, y, w, h = cv2.boundingRect(np.vstack(contours))
                    pad = 6
                    x = max(0, x - pad); y = max(0, y - pad)
                    arr = arr[y:y + h + 2*pad, x:x + w + 2*pad]
                h_, w_ = arr.shape
                if max(w_, h_) < 1500:
                    arr = cv2.resize(arr, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)
                return Image.fromarray(arr)
            except Exception:
                return img

        def _ocr_text(pil_img: Image.Image, lang: str = "eng+fra") -> str:
            if pytesseract is None:
                return ""
            prep = _preprocess_for_ocr(pil_img)
            cfg = "--oem 1 --psm 6"
            try:
                return pytesseract.image_to_string(prep, lang=lang, config=cfg)
            except Exception:
                return pytesseract.image_to_string(prep)  # fallback

        def _tesseract_status():
            status = {"has_pytesseract": pytesseract is not None, "binary_ok": False, "version": None, "error": None}
            if pytesseract is None:
                status["error"] = "pytesseract not installed in environment"
                return status
            try:
                # Will raise if the binary is not found
                v = pytesseract.get_tesseract_version()
                status["binary_ok"] = True
                status["version"] = str(v)
            except Exception as e:
                status["error"] = str(e)
            return status

        def _debug_ocr(file_bytes: bytes) -> Dict[str, Any]:
            info: Dict[str, Any] = {}
            try:
                pil = Image.open(io.BytesIO(file_bytes))
                info["image_mode"] = pil.mode
                info["image_size"] = pil.size
            except Exception as e:
                info["open_error"] = str(e)
                return info
            try:
                prep = _preprocess_for_ocr(pil)
                info["preprocessed_size"] = getattr(prep, "size", None)
            except Exception as e:
                info["preprocess_error"] = str(e)
            txt = ""
            try:
                txt = _ocr_text(pil)
            except Exception as e:
                info["ocr_error"] = str(e)
            info["tesseract_status"] = _tesseract_status()
            info["text_len"] = len(txt or "")
            preview = (txt or "")[:800]
            info["text_preview"] = preview
            try:
                codes = re.findall(COURSE_CODE, txt or "")
                info["codes_found"] = codes
            except Exception:
                info["codes_found"] = []
            try:
                pcts = re.findall(PCT, txt or "")
                info["percents_found"] = pcts[:20]
            except Exception:
                info["percents_found"] = []
            try:
                rows = extract_courses_from_text(txt or "")
                info["rows_parsed"] = [getattr(r, "course_name", "") for r in rows][:10]
                info["rows_count"] = len(rows)
            except Exception as e:
                info["parse_error"] = str(e)
            return info

        def _to_float(x: str | None) -> float | None:
            if not x: return None
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
            if not m: return None
            a = _to_float(m.group(1)); b = _to_float(m.group(2))
            if a is None or not b: return None
            if b == 0: return None
            return round(100.0 * a / b, 2)

        def extract_courses_from_text(text: str) -> List[CourseRow]:
            """
            Two-pass parser:
              Pass 1: anchor on Quebec course codes like 109-102-MQ (most reliable).
              Pass 2: if few/none found, split by row numbers '1.', '2.', ... and
                      treat the first percent in the block as 'your grade' and the
                      last percent as 'class average'. Also accepts 'a/b' → %.
            """
            lines = [ln for ln in text.splitlines() if ln.strip()]
            rows: List[CourseRow] = []

            # ---- Pass 1: by course code anchor ----
            i = 0
            while i < len(lines):
                ln = lines[i]
                code_match = re.search(COURSE_CODE, ln)
                if not code_match:
                    i += 1
                    continue

                start = max(0, i - 2)
                end   = min(len(lines), i + 8)
                block = "\n".join(lines[start:end])

                # Course name: prefer previous line or earlier alpha line not containing a code
                course_name = ""
                if i > 0:
                    prev = lines[i-1].strip()
                    if len(re.findall(r"[A-Za-zÀ-ÿ]{3,}", prev)) >= 2 and "sect" not in prev.lower():
                        course_name = prev
                if not course_name:
                    for k in range(start, i):
                        cand = lines[k].strip()
                        if len(re.findall(r"[A-Za-zÀ-ÿ]{3,}", cand)) >= 2 and not re.search(COURSE_CODE, cand) and "sect" not in cand.lower():
                            course_name = cand
                            break

                class_code = code_match.group(0).replace(" ", "")

                # Try labeled extraction first
                your_grade = _pct_near_label(block, LABEL_GRADE)
                class_avg  = _pct_near_label(block, LABEL_AVG)
                std_dev    = _pct_near_label(block, LABEL_SD)

                # If no explicit 'your grade' label, try fraction a/b → %
                if your_grade is None:
                    frac = _fraction_to_pct(block)
                    if frac is not None:
                        your_grade = frac

                # If still missing avg, take last percentage in block as class average
                if class_avg is None:
                    pcts = [ _to_float(p) for p in re.findall(PCT, block) ]
                    pcts = [p for p in pcts if p is not None and p <= 100]
                    if pcts:
                        if your_grade is None:
                            your_grade = pcts[0]
                        class_avg = pcts[-1] if len(pcts) > 1 else None

                rows.append(CourseRow(
                    course_name=course_name,
                    class_code=class_code,
                    your_grade=your_grade,
                    class_avg=class_avg,
                    std_dev=std_dev
                ))

                i += 1  # jump past this block

            # ---- Pass 2: numbered rows fallback (works for the big 'Grades' table) ----
            if len(rows) < 2:
                # Build row blocks split on "1.", "2.", ...
                blocks: list[str] = []
                cur: list[str] = []
                for ln in lines:
                    if re.match(r"^\s*\d+\.\s*$", ln) or re.match(r"^\s*\d+\.\s", ln):
                        if cur:
                            blocks.append("\n".join(cur))
                            cur = []
                        cur.append(ln)
                    else:
                        cur.append(ln)
                if cur:
                    blocks.append("\n".join(cur))

                for block in blocks:
                    blines = [b.strip() for b in block.splitlines() if b.strip()]
                    # Course name: first good alpha line after the row number
                    course_name = ""
                    for b in blines[1:4]:
                        if len(re.findall(r"[A-Za-zÀ-ÿ]{3,}", b)) >= 2 and "sect" not in b.lower():
                            course_name = _clean_course_name(b)
                            if course_name:
                                break

                    # Course code within block (optional)
                    class_code = ""
                    for b in blines:
                        m = re.search(COURSE_CODE, b)
                        if m:
                            class_code = m.group(0).replace(" ", "")
                            break

                    # Percentages in block
                    pcts = [ _to_float(p) for p in re.findall(PCT, block) ]
                    pcts = [p for p in pcts if p is not None and p <= 100]
                    your_grade = None
                    class_avg  = None

                    frac = _fraction_to_pct(block)
                    if frac is not None:
                        your_grade = frac
                    if pcts:
                        if your_grade is None:
                            your_grade = pcts[0]
                        if len(pcts) >= 2:
                            class_avg = pcts[-1]

                    if course_name or class_code or (your_grade is not None or class_avg is not None):
                        rows.append(CourseRow(
                            course_name=course_name,
                            class_code=class_code,
                            your_grade=your_grade,
                            class_avg=class_avg,
                            std_dev=None
                        ))

            return rows

        def merge_by_code(rows: List[CourseRow]) -> List[CourseRow]:
            by: Dict[str, CourseRow] = {}
            for r in rows:
                key = r.class_code or r.course_name.lower()
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

        def extract_from_image_file(file_bytes: bytes) -> List[CourseRow]:
            img = Image.open(io.BytesIO(file_bytes))
            text = _ocr_text(img)
            return extract_courses_from_text(text)

        # Attach fallbacks to the imported module namespace so the rest of the app can call them
        ocr_utils.extract_from_image_file = extract_from_image_file  # type: ignore
        ocr_utils.merge_by_code = merge_by_code  # type: ignore
        ocr_utils._debug_ocr = _debug_ocr  # type: ignore
        ocr_utils._tesseract_status = _tesseract_status  # type: ignore
except Exception:
    # If anything above fails, we'll surface the error during the first OCR call
    pass

# ================== PAGE & THEME ==================
st.set_page_config(page_title="R-Score Dashboard", layout="wide")

st.markdown("""
<style>
header, div[data-testid="stToolbar"] {
  visibility: hidden;
}
/* ===== App background ===== */
[data-testid="stAppViewContainer"] {
  background: linear-gradient(145deg, #f7f8fa 0%, #e5e7eb 100%);
}

/* ===== main container ===== */
.block-container {
  padding-top: 1.5rem;
  max-width: 1400px;
}

/* ===== glass cards (content) ===== */
.glass-card {
  background: rgba(255,255,255,0.65);
  border-radius: 20px;
  backdrop-filter: blur(10px);
  box-shadow: 0 8px 30px rgba(0,0,0,0.06);
  border: 1px solid rgba(255,255,255,0.4);
  padding: 1.25rem 1.5rem 1.25rem 1.5rem;
  margin-top: 0.25rem;       /* <— moved down so it doesn't hug the tabs */
  margin-bottom: 1rem;
}

/* ===== metric cards ===== */
.metric-card {
  background: #111827;
  color: #fff;
  border-radius: 18px;
  padding: 1rem 1.25rem;
  box-shadow: 0 12px 30px rgba(0,0,0,0.3);
}

def show_login():
    st.title("Sign in or Sign up to RScoreCalc")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Sign in"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                user = res.user
                if user:
                    st.session_state["user"] = user
                    # fetch profile
                    prof = supabase.table("profiles").select("*").eq("id", user.id).single().execute()
                    st.session_state["is_premium"] = prof.data.get("is_premium", False)
                    st.rerun()
                else:
                    st.error("Login failed.")
            except Exception as e:
                st.error(f"Auth error: {e}")

    with col2:
        if st.button("Create account"):
            try:
                res = supabase.auth.sign_up({"email": email, "password": password})
                st.success("✅ Account created! Check your email to confirm before logging in.")
            except Exception as e:
                st.error(f"Sign-up error: {e}")
/* ===== tabs ===== */
.stTabs [data-baseweb="tab-list"] {
  background: rgba(255,255,255,0.85);
  border-radius: 9999px;
  padding: 0.35rem;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
  gap: 0.5rem;
  margin-bottom: 0;      /* <— kill the gap under the tabs */
}
.stTabs{ margin-bottom:0 !important; }
/* hard kill ghost underline / spacer below tabs */
.stTabs [data-baseweb="tab-panel"], .stTabs [data-baseweb="tab-content"]{ border-top:0 !important; }
.stTabs [data-baseweb="tab-list"]{ border-bottom:0 !important; }
.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="focus-underline"],
.stTabs [data-baseweb="tab-border"] { display:none !important; }
.stTabs [data-baseweb="tab"]::after{ display:none !important; }

/* Compact toolbar wrapper for tab-level settings */
.glass-toolbar {
  background: transparent;
  border-radius: 14px;
  padding: 0;
  box-shadow: none;
  margin-bottom: 0.25rem;
  border: 0;
}

/* Tiny metric “chips” for scenarios */
.chip-row{
  display:flex; gap:.6rem; flex-wrap:wrap; align-items:stretch; margin-top:.5rem;
}
.metric-chip{
  flex:1 1 180px;
  background:#fff;
  border-radius:12px;
  padding:.65rem .8rem;
  box-shadow:0 6px 18px rgba(0,0,0,.06);
  border:1px solid rgba(17,24,39,.08);
}
.metric-chip .label{ font-size:.8rem; color:#6b7280; margin-bottom:.15rem; }
.metric-chip .value{ font-size:1.35rem; font-weight:800; color:#111827; line-height:1.2; }

.stTabs [data-baseweb="tab"] {
  border-radius: 9999px;
  padding: 0.45rem 1.1rem;
  background: transparent;
  color: #4b5563;
  font-weight: 500;
  transition: all .2s ease-in-out;
}

.stTabs [data-baseweb="tab"]:hover {
  background: rgba(255,255,255,0.5);
}

.stTabs [aria-selected="true"] {
  background: #ffffff;
  color: #111827;
  box-shadow: 0 4px 10px rgba(0,0,0,0.04);
}

/* ===== tables ===== */
[data-testid="stDataFrame"] {
  border-radius: 16px;
  overflow: hidden;
}

/* ===== podium ===== */
.podium {
  display: flex;
  justify-content: center;
  align-items: flex-end;
  gap: 1rem;
  margin-top: 2rem;
}
.podium-card {
  flex: 1;
  text-align: center;
  padding: 1.5rem;
  border-radius: 24px;
  backdrop-filter: blur(10px);
  color: #111827;
  box-shadow: 0 8px 25px rgba(0,0,0,0.1);
  font-weight: 600;
  transition: transform 0.2s ease-in-out;
}
.podium-card:hover { transform: translateY(-5px); }
.gold   { background: linear-gradient(180deg,#facc15 0%,#fef9c3 100%); }
.silver { background: linear-gradient(180deg,#d1d5db 0%,#f3f4f6 100%); }
.bronze { background: linear-gradient(180deg,#f97316 0%,#fed7aa 100%); }
.podium-rgain {
  font-size: 1.5rem;
  margin-top: 0.5rem;
  font-weight: 700;
}
/* === Hide top Streamlit bar === */
header {
  visibility: hidden;
  height: 0;
  margin: 0;
  padding: 0;
}
div[data-testid="stToolbar"] {
  visibility: hidden;
  height: 0;
  margin: 0;
  padding: 0;
}
</style>
""", unsafe_allow_html=True)
# ================== TERMS OF USE GATE ==================
if "tos_accepted" not in st.session_state:
    st.session_state.tos_accepted = False

if not st.session_state.tos_accepted:
    st.markdown("## Terms of Use")
    st.markdown(
        """
        This R‑Score tool is **independent** and **not affiliated with John Abbott College** (JAC), Omnivox, or My JAC Portal. It is for **informational/educational** use only and **does not guarantee admission** decisions. Do **not** enter any Omnivox credentials here.

        By continuing you agree to:
        - Use this site responsibly and in accordance with the JAC **College Policy on appropriate use of computing resources**.
        - Not attempt unauthorized access, phishing, scraping, or any activity prohibited by JAC policies or law.
        - Accept that results are estimates based on inputs you provide; no warranty is given.

        Reference: JAC policies are available at <https://johnabbott.omnivox.ca/intr/Module/Information/Conditions.aspx>. Relevant Omnivox terms include (non‑exhaustive): password confidentiality, prohibition on unauthorized access, and restrictions on reproducing content or disrupting services.
        """
    )
    with st.expander("Reference: Omnivox terms (excerpts)"):
        st.markdown(
            """
            - Treat your Omnivox password like your bank PIN; do not share or store it.
            - Unauthorized access (using someone else’s identifier/password, attempting to obtain a password) is forbidden.
            - Reproducing content from Omnivox for illegitimate ends (e.g., phishing), distributing malware, or disrupting services is forbidden.
            - Collecting/storing personal data of other users is forbidden.
            - Infractions may result in severe sanctions, including expulsion and civil/criminal recourse.
            - Links to third‑party sites are provided for convenience; Omnivox has no control over those sites.
            - Do not infringe third‑party intellectual property when uploading content.
            - Zoom classes are hosted on an external platform; consult Zoom’s own terms.
            """
        )
    agree = st.checkbox("I have read and agree to these Terms of Use.")
    colA, colB = st.columns([1,1])
    with colA:
        if st.button("Agree and enter"):
            if agree:
                st.session_state.tos_accepted = True
                try:
                    st.rerun()
                except Exception:
                    st.experimental_rerun()
            else:
                st.warning("Please check the box to agree before continuing.")
    with colB:
        st.caption("If you do not agree, close this tab or window.")
    st.stop()


# ================== CONSTANTS ==================
REQUIRED_COLS = ["Course Name", "Your Grade", "Class Avg", "Std. Dev", "Credits"]
ALL_COLS = REQUIRED_COLS

# maps from messy CSV headers -> ours
HEADER_ALIASES = {
    "course": "Course Name",
    "course name": "Course Name",
    "class": "Course Name",
    "grade": "Your Grade",
    "your grade": "Your Grade",
    "note": "Your Grade",
    "mark": "Your Grade",
    "average": "Class Avg",
    "class avg": "Class Avg",
    "std": "Std. Dev",
    "std dev": "Std. Dev",
    "standard deviation": "Std. Dev",
    "credits": "Credits",
    "credit": "Credits",
}
# ---------- Credit lookup helpers ----------
import re as _re

def _norm_code(code: str) -> str:
    if not code:
        return ""
    return _re.sub(r"\s+", "", str(code).upper())

def _norm_name(name: str) -> str:
    # reuse your _clean_course_name if present
    try:
        return _clean_course_name(name).lower()
    except NameError:
        # fallback: letters+spaces only
        s = _re.sub(r"[^A-Za-zÀ-ÿ\s]", " ", str(name) or "")
        s = _re.sub(r"\s+", " ", s).strip()
        return s.lower()

@st.cache_data(show_spinner=False)
def load_credit_mappings(mtime_sig: float | None = None):
    """
    Loads one or more mapping files and returns:
      - code_to_credits: dict["201-SN2-RE"] -> 2.0
      - name_to_credits: dict["differential calculus"] -> 2.0
    Recognized filenames/columns are flexible.

    mtime_sig is a cache-buster; pass _credit_mapping_mtime_sig() so edits to the CSV invalidate cache.
    """
    candidates = [
        "course_credits_mapping.csv",
        "data/course_credits_mapping.csv",
        "credits_map.csv",
        "ministerial_credits.csv",
        "data/ministerial_credits.csv",
    ]
    code_to, name_to = {}, {}

    for fn in candidates:
        if not os.path.exists(fn):
            continue
        try:
            m = pd.read_csv(fn)
        except Exception:
            continue

        # lenient column discovery
        cols = {c.strip().lower(): c for c in m.columns}
        col_code = cols.get("class code") or cols.get("code") or cols.get("class_code") or cols.get("course code") or cols.get("ministerial code")
        col_name = cols.get("course name") or cols.get("name") or cols.get("course") or cols.get("title")
        col_cred = cols.get("credits") or cols.get("credit") or cols.get("cr")
        if not col_cred:
            continue

        mm = m.copy()
        for c in (col_code, col_name, col_cred):
            if c and c in mm.columns:
                mm[c] = mm[c].astype(str)

        # coerce credits
        mm["_credits_"] = pd.to_numeric(mm[col_cred], errors="coerce")
        mm = mm[pd.notna(mm["_credits_"]) & (mm["_credits_"] > 0)]

        # helpers
        def _norm_code_local(v: str) -> str:
            return _re.sub(r"\s+", "", str(v or "")).upper()

        def _norm_name_local(v: str) -> str:
            try:
                return _clean_course_name(v).lower()
            except Exception:
                s = _re.sub(r"[^A-Za-zÀ-ÿ\s]", " ", str(v) or "")
                s = _re.sub(r"\s+", " ", s).strip()
                return s.lower()

        if col_code and col_code in mm.columns:
            for v, cr in zip(mm[col_code], mm["_credits_"]):
                code_to[_norm_code_local(v)] = float(cr)

        if col_name and col_name in mm.columns:
            for v, cr in zip(mm[col_name], mm["_credits_"]):
                name_to[_norm_name_local(v)] = float(cr)

    # reference mtime_sig to bind it into cache key
    _ = mtime_sig
    return code_to, name_to

# Helper: cache-busting signature for mapping files
def _credit_mapping_mtime_sig() -> float:
    """Return a combined mtime signature for known mapping files."""
    paths = [
        "course_credits_mapping.csv",
        "data/course_credits_mapping.csv",
        "credits_map.csv",
        "ministerial_credits.csv",
        "data/ministerial_credits.csv",
    ]
    mtimes = []
    for pth in paths:
        try:
            if os.path.exists(pth):
                mtimes.append(os.path.getmtime(pth))
        except Exception:
            pass
    return float(sum(mtimes)) if mtimes else 0.0

def autofill_credits_df(df_in: pd.DataFrame) -> pd.DataFrame:
    """
    Returns a copy with Credits filled where missing/zero using:
      1) Class Code match
      2) Cleaned Course Name match
    Adds a readonly 'Credits Source' column for debugging.
    """
    code_to, name_to = load_credit_mappings(_credit_mapping_mtime_sig())
    df = df_in.copy()
    if "Credits" not in df.columns:
        df["Credits"] = np.nan

    # If empty, ensure debug column exists and return immediately
    if df.empty:
        if "Credits Source" not in df.columns:
            df["Credits Source"] = None
        return df

    def choose(row):
        cr = row.get("Credits", np.nan)
        if pd.notna(cr) and float(cr or 0) > 0:
            return cr, None
        # try code
        code = _norm_code(row.get("Class Code", ""))
        if code and code in code_to:
            return code_to[code], "code"
        # try name
        nm = _norm_name(row.get("Course Name", ""))
        if nm and nm in name_to:
            return name_to[nm], "name"
        return np.nan, None

    # Build a 2-column frame in a robust way (works across pandas versions)
    picked = df.apply(lambda r: pd.Series(choose(r), index=["_credits", "_source"]), axis=1)

    # Assign back with proper dtypes
    df["Credits"] = pd.to_numeric(picked["_credits"], errors="coerce")
    df["Credits Source"] = picked["_source"].astype("string")
    return df
# ================== HELPERS ==================
def zscore(grade, avg, sd):
    try:
        grade = float(grade); avg = float(avg); sd = float(sd)
        if sd == 0:
            return 0.0
        return (grade - avg) / sd
    except Exception:
        return 0.0

def clean_numeric(df: pd.DataFrame, cols):
    for c in cols:
        if c not in df.columns:
            df[c] = np.nan
        df[c] = (
            df[c].astype(str)
            .str.replace(",", ".", regex=False)
            .str.extract(r"([0-9.]+)")[0]
            .astype(float)
        )
    return df

def ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
    for c in ALL_COLS:
        if c not in df.columns:
            df[c] = ""
    return df[ALL_COLS]

def load_uni_csv(path="uni_acceptance.csv") -> pd.DataFrame:
    if os.path.exists(path):
        df = pd.read_csv(path)
    else:
        # fallback sample with min & recommended thresholds
        df = pd.DataFrame([
            ("McGill","Bachelor of Engineering",31.0,32.5,"https://www.mcgill.ca/engineering/"),
            ("McGill","Desautels BCom (Management)",30.0,31.0,"https://www.mcgill.ca/desautels/programs/bcom"),
            ("McGill","BSc (Science)",28.5,30.0,"https://www.mcgill.ca/science/"),
            ("Concordia","BCompSci (Computer Science)",27.0,28.0,"https://www.concordia.ca/academics/undergraduate/computer-science.html"),
            ("Concordia","BEng (Mechanical)",28.0,29.5,"https://www.concordia.ca/academics/undergraduate/mechanical-engineering.html"),
            ("Université de Montréal","BSc (Sciences)",27.5,28.5,"https://admission.umontreal.ca/programmes/"),
            ("Polytechnique Montréal","BEng",29.0,30.5,"https://www.polymtl.ca/futurs/"),
            ("ÉTS","BEng (Génie)",26.5,27.5,"https://www.etsmtl.ca/programmes/1er-cycle"),
            ("Université Laval","Bachelor programs (sample)",26.0,27.0,"https://www.ulaval.ca/etudes"),
            ("Université de Sherbrooke","BEng",27.0,28.0,"https://www.usherbrooke.ca/programmes"),
            ("UQAM","BAA / Business",25.0,26.0,"https://etudier.uqam.ca/"),
        ], columns=["university","program","min_r","rec_r","url"])
    # normalize columns
    for col in ["university","program","min_r","url"]:
        if col not in df.columns:
            df[col] = ""
    if "rec_r" not in df.columns:
        try:
            df["rec_r"] = pd.to_numeric(df["min_r"], errors="coerce") + 1.0
        except Exception:
            df["rec_r"] = df["min_r"]
    return df[["university","program","min_r","rec_r","url"]]

def map_headers(df: pd.DataFrame) -> pd.DataFrame:
    """Try to rename messy CSV headers to our standard ones."""
    new_cols = {}
    for col in df.columns:
        key = col.strip().lower()
        if key in HEADER_ALIASES:
            new_cols[col] = HEADER_ALIASES[key]
    if new_cols:
        df = df.rename(columns=new_cols)
    return df

def compute_importance(df: pd.DataFrame):
    if df.empty:
        return df.assign(Importance=0.0)
    total_credits = df["Credits"].fillna(1).replace(0,1).sum()
    imps = []
    for _, r in df.iterrows():
        sd = r["Std. Dev"]
        cr = r["Credits"] if pd.notna(r["Credits"]) and r["Credits"] != 0 else 1
        if pd.isna(sd) or sd == 0 or total_credits == 0:
            imps.append(0.0)
        else:
            imps.append((5.0 / sd) * (cr / total_credits))
    df = df.copy()
    df["Importance"] = imps
    return df


# ================== SESSION ==================
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=ALL_COLS)
if "overall_r" not in st.session_state:
    st.session_state.overall_r = None
if "manual_editor_version" not in st.session_state:
    st.session_state.manual_editor_version = 0

# ================== SETTINGS (session defaults) ==================
if "r_offset_min" not in st.session_state:
    st.session_state.r_offset_min = -2.0
if "r_offset_max" not in st.session_state:
    st.session_state.r_offset_max =  2.0

# ================== HEADER ==================
st.markdown(
    '<div class="glass-card"><h2 style="margin-bottom:0.2rem;">R-Score Dashboard</h2></div>',
    unsafe_allow_html=True
)
def require_premium():
    if not st.session_state.get("is_premium", False):
        st.markdown("### 🔒 Premium feature")
        st.write("You unlocked only the free tools. To use this section, click **Unlock Pro (mock)** on the landing page.")
        st.stop()
# ================== TABS ==================
# Add Help/Explanation first; Settings last
explain_tab, manual_tab, csv_tab, import_tab, tab3, tab4, tab5, tab6, settings_tab = st.tabs([
    "Help / Explanation",
    "Manual",
    "CSV",
    "Import (OCR)",
    "Results",
    "Importance",
    "Biggest gains",
    "Programs",
    "Settings"
])
# ---------- EXPLANATION TAB ----------
with explain_tab:
    st.subheader("How to get your numbers (step‑by‑step)")

    st.markdown(
        """
        For **each course**, the dashboard needs:

        - **Course Name**  
          Letters only. We automatically clean “1. … 19.3/23” and other noise from OCR.

        - **Credits**  
          How many credits the course is worth. We **autofill** from the local mapping file
          (`course_credits_mapping.csv`). You can still override it in the table.

        - **Your Grade (%)**  
          Your current/final grade for the course.

        - **Class Avg (%)**  
          The class average for the same evaluation window.

        - **Std. Dev**  
          **Only shown on the course’s detailed page** in Omnivox. Look for the yellow
          “**Course summary**” card on a class page; the **Standard deviation** value is in the
          **Class statistics** box. If you don’t have it, you can leave it blank for now
          (we’ll treat it as 0, which makes the Z‑score 0 and keeps R at its baseline).
        """
    )

    st.markdown(
        """
        ### Recommended workflow

        1. **Take a list screenshot (or two).**  
           From the Omnivox **Grades** list, capture the table that shows every course with
           **Current grade (average)** and **Class average**. If it doesn't fit in one image,
           take multiple screenshots—upload them all together.

        2. **Open each course to get Std. Dev.**  
           Click a course in the sidebar → **Grades** / **Detailed marks per assessment**.  
           In the **Course summary** panel (right side), copy the **Standard deviation**.  
           Tip: a screenshot of this section is enough; the OCR will merge it by class code.

        3. **Import (OCR).**  
           Go to **Import (OCR)** and upload the list screenshot(s) **first**, then the
           course‑detail screenshot(s). The parser merges rows by **Class code** and
           fills missing pieces (grade/avg/std dev). Review the table and click
           **Add reviewed rows to my table**.

        4. **Autofill credits.**  
           Credits are looked up by **Class code** first, then by cleaned **Course name**
           using `course_credits_mapping.csv`. If a course is missing a credit value, you can
           edit the number directly in the review table or in the **Manual** tab.

        5. **Edit or add anything manually.**  
           Use the **Manual** tab for quick corrections (everything shows to **two decimals**).
        """
    )

    st.markdown(
        """
        ### Quick tips
        - If OCR ever shifts numbers by one row, upload the **mobile card view** screenshot or
          include a bit more vertical spacing between cards. The parser now **prefers values that
          appear *after* the class code line**, which prevents mixing with the previous card.
        - If a course name shows junk (like `? . General chemistry`), it will be auto‑cleaned to
          letters‑and‑spaces only.
        - Use **periods** for decimals (e.g., `82.50`). Tables and results round to **two decimals**.
        - You can always upload a **CSV** instead (download the template in the **CSV** tab).
        """
    )

# ---------- MANUAL TAB ----------
with manual_tab:
    st.write("Enter or edit your courses below. Click 'Confirm Changes' when done.")

    if "df" not in st.session_state:
        st.session_state.df = pd.DataFrame(columns=REQUIRED_COLS)

    df_manual = st.session_state.df.copy()
    df_manual = ensure_columns(df_manual)[REQUIRED_COLS]
    df_manual["Course Name"] = df_manual["Course Name"].astype(str).fillna("")

    editor_key = f"manual_editor_{st.session_state.get('manual_editor_version', 0)}"

    edited_df = st.data_editor(
        df_manual,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key=editor_key,
        column_config={
            # ... your column_config ...
        },
    )

    if st.button("✅ Confirm Changes"):
        st.session_state.df = ensure_columns(edited_df.copy())
        st.success("Changes saved!")
        st.rerun()
# ---------- CSV TAB ----------
with import_tab:
    require_premium()
with csv_tab:
    st.write("Upload a CSV. We'll try to auto-detect columns.")

    template_df = pd.DataFrame([
        {"Course Name": "Calculus I", "Your Grade": 85, "Class Avg": 78, "Std. Dev": 7, "Credits": 2},
        {"Course Name": "Chemistry",  "Your Grade": 82, "Class Avg": 75, "Std. Dev": 6, "Credits": 2},
        {"Course Name": "Physics",    "Your Grade": 88, "Class Avg": 80, "Std. Dev": 5, "Credits": 2},
    ], columns=REQUIRED_COLS)
    st.download_button(
        "⬇️ Download template CSV",
        data=template_df.to_csv(index=False).encode(),
        file_name="rscore_template.csv",
        mime="text/csv"
    )
    st.markdown(
        """
        **How to fill the template**
        1. Download the CSV above.
        2. Replace the example rows with your courses. Keep these exact column names: `Course Name`, `Your Grade`, `Class Avg`, `Std. Dev`, `Credits`.
        3. Use periods for decimals (e.g., `82.5`). If `Credits` is blank or 0, we count it as 1.
        4. Save the file and upload it below. You can edit afterwards in the **Manual** tab.
        """
    )

    up = st.file_uploader("Upload CSV", type=["csv"], key="csv_up")
    if up is not None:
        try:
            df_up = pd.read_csv(up, encoding="utf-8-sig", engine="python")
            rename_map = {}
            for c in df_up.columns:
                c_lower = c.strip().lower().replace(".", "").replace("_", "").replace(" ", "")
                if "coursename" in c_lower or c_lower in ("course","classname","name"):
                    rename_map[c] = "Course Name"
                elif "grade" in c_lower or "mark" in c_lower or "note" in c_lower:
                    rename_map[c] = "Your Grade"
                elif "avg" in c_lower or "average" in c_lower or "mean" in c_lower:
                    rename_map[c] = "Class Avg"
                elif "std" in c_lower or "deviation" in c_lower or "sigma" in c_lower:
                    rename_map[c] = "Std. Dev"
                elif "credit" in c_lower or c_lower == "cr":
                    rename_map[c] = "Credits"
            df_up = df_up.rename(columns=rename_map)
            for col in REQUIRED_COLS:
                if col not in df_up.columns:
                    df_up[col] = np.nan
            df_up = df_up[REQUIRED_COLS]
            df_up = clean_numeric(df_up, ["Your Grade", "Class Avg", "Std. Dev", "Credits"])
            df_up["Credits"] = df_up["Credits"].fillna(1)
            df_up.loc[df_up["Credits"] == 0, "Credits"] = 1
            # Try to autofill Credits from mapping (by code/name)
            df_up = autofill_credits_df(df_up)
            df_up["Credits"] = pd.to_numeric(df_up["Credits"], errors="coerce").fillna(1)
            df_up.loc[df_up["Credits"] == 0, "Credits"] = 1
            st.session_state.df = df_up
            st.success(f"Loaded {len(df_up)} rows from CSV.")
            st.session_state.manual_editor_version = st.session_state.get("manual_editor_version", 0) + 1
        except Exception as e:
            st.error(f"CSV error: {e}")

# ---------- IMPORT TAB (Photo OCR only) ----------
with import_tab:
    require_premium()
with import_tab:
    st.markdown("### 📸 Import from Omnivox screenshots")

    ocr_files = st.file_uploader(
        "Upload one or more screenshots (PNG/JPG). We'll parse Course + Code + Grade + Class average (+ Std. dev when present).",
        type=["png","jpg","jpeg"],
        accept_multiple_files=True,
        key="ocr_files"
    )

    # Always initialize these so downstream code never sees undefined names
    df_ocr = pd.DataFrame(columns=["Course Name","Class Code","Your Grade","Class Avg","Std. Dev","Credits"])
    tess_status = _local_tesseract_status()
    ocr_debug = []
    all_rows = []

    # Credit mapping status + manual reload
    with st.expander("ℹ️ Credit mapping status"):
        code_map, name_map = load_credit_mappings(_credit_mapping_mtime_sig())
        st.write(f"Loaded **{len(code_map)}** code mappings and **{len(name_map)}** name mappings.")
        candidates = [
            "course_credits_mapping.csv",
            "data/course_credits_mapping.csv",
            "credits_map.csv",
            "ministerial_credits.csv",
            "data/ministerial_credits.csv",
        ]
        found = [p for p in candidates if os.path.exists(p)]
        if found:
            st.write("Found file(s):")
            for p in found:
                st.write(f"• `{os.path.abspath(p)}`")
        else:
            st.warning("No mapping files found in working directory. Current CWD:")
            st.code(os.getcwd())
        if st.button("↻ Reload mapping files"):
            st.cache_data.clear()
            st.success("Cache cleared — reloading…")
            try:
                st.rerun()
            except Exception:
                st.experimental_rerun()

    if ocr_files:
        st.caption(f"Processing {len(ocr_files)} screenshot(s)…")
        for up in ocr_files:
            try:
                _bytes = up.read()
                rows, status_used, preview = app_extract_from_image_bytes(_bytes)
                if status_used:
                    tess_status = status_used
                all_rows.extend(rows)

                # Compact preview for debug log
                snapshot = []
                for r in rows:
                    if isinstance(r, dict):
                        snapshot.append(r)
                    elif hasattr(r, "to_app_row"):
                        snapshot.append(r.to_app_row())
                    else:
                        snapshot.append({
                            "Course Name": getattr(r, "course_name", ""),
                            "Class Code": getattr(r, "class_code", ""),
                            "Your Grade": getattr(r, "your_grade", None),
                            "Class Avg": getattr(r, "class_avg", None),
                            "Std. Dev": getattr(r, "std_dev", None),
                            "Credits": getattr(r, "credits", None),
                        })
                ocr_debug.append({
                    "file": getattr(up, "name", "image"),
                    "rows_found": len(rows),
                    "rows_preview": snapshot[:6],
                    "engine": tess_status,
                    "analysis": {"text_preview": preview},
                })
            except Exception as e:
                st.warning(f"OCR error on {getattr(up,'name','image')}: {e}")

    # If we parsed anything, normalize to a DataFrame
    if all_rows:
        merged_any = app_merge_rows_any(all_rows)
        df_ocr = pd.DataFrame(merged_any, columns=["Course Name","Class Code","Your Grade","Class Avg","Std. Dev","Credits"])

    # Only proceed with cleaning / UI if there's something to show
    if not df_ocr.empty:
        # keep Class Code for lookups; clean names & drop junk
        if "Course Name" in df_ocr.columns:
            df_ocr["Course Name"] = df_ocr["Course Name"].astype(str).map(_clean_course_name)
            junk_prefixes = ("current average","team forums","assignments","calendar","list of my absences","teachers info","recommended websites")
            junk = df_ocr["Course Name"].fillna("").str.strip().eq("") | df_ocr["Course Name"].str.lower().str.startswith(junk_prefixes)
            df_ocr = df_ocr[~junk].reset_index(drop=True)
            df_ocr = df_ocr[df_ocr["Course Name"].str.strip() != ""]
            df_ocr = df_ocr[df_ocr["Course Name"].str.len() >= 3].reset_index(drop=True)

        # Fill credits from mapping (by Class Code first, then Course Name)
        df_ocr = autofill_credits_df(df_ocr)
        # ensure debug columns visible even when NaN
        if "Credits Source" not in df_ocr.columns:
            df_ocr["Credits Source"] = ""

        # Review editor (2-decimals everywhere)
        review_cols = ["Course Name","Your Grade","Class Avg","Std. Dev","Credits"]
        for col in ["Your Grade","Class Avg","Std. Dev","Credits"]:
            df_ocr[col] = pd.to_numeric(df_ocr[col], errors="coerce")

        edited = st.data_editor(
            df_ocr[review_cols],
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            column_config={
                "Course Name": st.column_config.TextColumn("Course Name"),
                "Your Grade":  st.column_config.NumberColumn("Your Grade", min_value=0.0, max_value=100.0, step=0.01, format="%.2f"),
                "Class Avg":   st.column_config.NumberColumn("Class Avg",  min_value=0.0, max_value=100.0, step=0.01, format="%.2f"),
                "Std. Dev":    st.column_config.NumberColumn("Std. Dev",   min_value=0.0, max_value=50.0,  step=0.01, format="%.2f"),
                "Credits":     st.column_config.NumberColumn("Credits",     min_value=0.0, max_value=10.0,  step=0.01, format="%.2f"),
            },
            key="ocr_review_editor"
        )

        with st.expander("ℹ️ Credit autofill details"):
            dbg = df_ocr[["Course Name","Class Code","Credits","Credits Source"]].copy()
            st.dataframe(dbg, use_container_width=True)

        # OCR engine status + guidance
        if not tess_status.get("has_pytesseract") or not tess_status.get("binary_ok"):
            st.warning(f"OCR engine not fully available. Details: {tess_status}")
            with st.expander("How to enable OCR on macOS (one-time setup)"):
                st.markdown(
                    "1) **Install the Tesseract binary** (Homebrew):\n"
                    "```bash\n"
                    "brew install tesseract\n"
                    "```\n"
                    "2) **Install Python packages** in your virtualenv:\n"
                    "```bash\n"
                    "source .venv/bin/activate\n"
                    "pip install pytesseract pillow opencv-python-headless\n"
                    "```\n"
                    "3) **Restart** this app and re-upload your screenshot.\n"
                    "\n"
                    "_If Homebrew is on Apple Silicon, the binary is typically at `/opt/homebrew/bin/tesseract`; this app already checks that path automatically._"
                )
        else:
            st.caption(f"OCR engine OK • Tesseract {tess_status.get('version')}")

        # Debug log
        with st.expander("🔎 OCR debug log (what the parser extracted)"):
            for entry in ocr_debug:
                st.write(f"**{entry.get('file','image')}** — rows found: {entry.get('rows_found')}")
                st.json(entry)

        if st.button("✅ Add reviewed rows to my table", key="commit_ocr"):
            edited = edited.copy()
            for col in ["Your Grade","Class Avg","Std. Dev","Credits"]:
                edited[col] = pd.to_numeric(edited[col], errors="coerce")
            edited["Credits"] = edited["Credits"].fillna(1)
            edited.loc[edited["Credits"] == 0, "Credits"] = 1
            st.session_state.df = pd.concat([st.session_state.df, edited], ignore_index=True)
            st.session_state.manual_editor_version = st.session_state.get("manual_editor_version", 0) + 1
            st.success(f"Added {len(edited)} row(s). You can fine-tune in the Manual tab.")
            try:
                st.rerun()
            except Exception:
                st.experimental_rerun()
    else:
        # Nothing parsed yet; show engine status and any logs
        if ocr_files:
            st.warning("No parsable rows found in your screenshots. Expand the debug log below to inspect OCR text.")
        if not tess_status.get("has_pytesseract") or not tess_status.get("binary_ok"):
            st.warning(f"OCR engine not fully available. Details: {tess_status}")
        else:
            st.caption(f"OCR engine OK • Tesseract {tess_status.get('version')}")
        with st.expander("🔎 OCR debug log (what the parser extracted)"):
            if ocr_debug:
                for entry in ocr_debug:
                    st.write(f"**{entry.get('file','image')}** — rows found: {entry.get('rows_found')}")
                    st.json(entry)
            else:
                st.caption("No OCR files processed yet.")
# ---------- SETTINGS TAB ----------
with settings_tab:
    st.subheader("R‑range settings")
    st.caption("These shift R(min)/R(max) for different schools.")

    c1, c2 = st.columns(2)
    with c1:
        st.number_input("R offset (min)", key="r_offset_min", step=0.5)
    with c2:
        st.number_input("R offset (max)", key="r_offset_max", step=0.5)
    st.caption("Formula: R = 35 + 5×Z + offset")
    st.markdown("""
    **What are these settings?**  
    - **R offset (min):** Conservative shift applied to your per-course R when computing **R (min)**.  
    - **R offset (max):** Optimistic shift applied when computing **R (max)**.  
    - Your **central R** is computed as `35 + 5×Z`. We then add these offsets to estimate a realistic range across schools that grade a bit harder or softer.
    """)

    # Optional live example using your current results (if available)
    r_c = st.session_state.get("overall_r_central")
    if r_c is not None and not pd.isna(r_c):
        r_min_ex = float(r_c) + float(st.session_state.get("r_offset_min", -2.0))
        r_max_ex = float(r_c) + float(st.session_state.get("r_offset_max",  2.0))
        st.markdown(
            f"Example with your current central R (**{r_c:.2f}**):  "
            f"**R (min)** ≈ **{r_min_ex:.2f}**, **R (max)** ≈ **{r_max_ex:.2f}**."
        )

    st.info("Not sure what to pick? Leave the defaults (−2.0 and +2.0). You can always adjust later.")
# ---------- TAB 3 (Results) ----------
with tab3:
    r_offset_min = float(st.session_state.get("r_offset_min", -2.0))
    r_offset_max = float(st.session_state.get("r_offset_max",  2.0))
    df = st.session_state.df.copy()
    if df.empty:
        st.warning("No data yet.")
    else:
        df = clean_numeric(df, ["Your Grade", "Class Avg", "Std. Dev", "Credits"])
        df["Credits"] = df["Credits"].fillna(1)
        df.loc[df["Credits"] == 0, "Credits"] = 1

        total_credits = df["Credits"].sum()
        df["Z"] = df.apply(lambda r: zscore(r["Your Grade"], r["Class Avg"], r["Std. Dev"]), axis=1)

        # central R (no offset)
        df["R (central)"] = df["Z"].apply(lambda z: 35.0 + 5.0 * z)
        # user offsets
        df["R (min)"] = df["Z"].apply(lambda z: 35.0 + 5.0 * z + r_offset_min)
        df["R (max)"] = df["Z"].apply(lambda z: 35.0 + 5.0 * z + r_offset_max)

        df["Weighted R (central)"] = df["R (central)"] * df["Credits"]
        df["Weighted R (min)"] = df["R (min)"] * df["Credits"]
        df["Weighted R (max)"] = df["R (max)"] * df["Credits"]

        r_central = df["Weighted R (central)"].sum() / total_credits
        r_min = df["Weighted R (min)"].sum() / total_credits
        r_max = df["Weighted R (max)"].sum() / total_credits
        st.session_state.overall_r_central = float(r_central)
        st.session_state.overall_r_min = float(r_min)
        st.session_state.overall_r_max = float(r_max)
        st.session_state.overall_r = float(r_central)  # keep this for backwards-compat
        st.session_state.overall_r = float(r_central)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f'<div class="metric-card"><div>R (central)</div><div style="font-size:2rem;">{r_central:.2f}</div></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="metric-card"><div>R (min)</div><div style="font-size:2rem;">{r_min:.2f}</div></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div class="metric-card"><div>R (max)</div><div style="font-size:2rem;">{r_max:.2f}</div></div>', unsafe_allow_html=True)

        st.subheader("Course breakdown")
        out_cols = ["Course Name","Your Grade","Class Avg","Std. Dev","Credits","R (central)","R (min)","R (max)"]
        df_out = df[out_cols].copy()
        num_cols = [c for c in out_cols if c != "Course Name"]
        df_out[num_cols] = df_out[num_cols].round(2)
        st.dataframe(df_out, use_container_width=True)

        st.download_button(
            "Download results CSV",
            df.to_csv(index=False).encode(),
            file_name="rscore_results.csv",
            mime="text/csv"
        )


# ---------- TAB 4 (Importance) ----------
with import_tab:
    require_premium()
with tab4:
    st.markdown(
    "**What does 'Importance' mean?** It estimates how much your overall R-score reacts to improving a specific course. "
    "We approximate it as **(5 ÷ Std. Dev) × (Course Credits ÷ Total Credits)**. "
    "So, courses with **lower Std. Dev** and **more credits** usually have **bigger bubbles**. "
    "Use this to prioritize where an extra few points could move your overall R the most."
)
    df = st.session_state.df.copy()
    if df.empty:
        st.warning("Add courses first.")
    else:
        df = clean_numeric(df, ["Your Grade", "Class Avg", "Std. Dev", "Credits"])
        df["Credits"] = df["Credits"].fillna(1)
        df.loc[df["Credits"] == 0, "Credits"] = 1
        df_imp = compute_importance(df)
        df_imp["Bubble Size"] = df_imp["Importance"] * 120

        fig = px.scatter(
            df_imp,
            x="Course Name",
            y="Importance",
            size="Bubble Size",
            color="Credits",
            hover_data=["Your Grade","Class Avg","Std. Dev","Credits"],
            size_max=70,
            title="Importance to overall R (bigger = bigger impact)"
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(255,255,255,0)",
            font_color="#111827",
            title_font_size=18,
            height=480,
            margin=dict(l=20,r=20,t=50,b=20),
        )
        fig.update_traces(
            marker=dict(line=dict(width=1,color="#111827"),opacity=0.8)
        )
        st.plotly_chart(fig, use_container_width=True)

# ---------- TAB 5 (Biggest gains) ----------
with import_tab:
    require_premium()
with tab5:
    st.subheader("🏆 Biggest Potential R-Score Gains")

    if "df" not in st.session_state or st.session_state.df is None:
        st.warning("Upload or enter your grades first.")
    else:
        df = st.session_state.df.copy()
        # Ensure numerics and sane Credits before calculations
        df = clean_numeric(df, ["Your Grade", "Class Avg", "Std. Dev", "Credits"])
        df["Credits"] = df["Credits"].fillna(1)
        df.loc[df["Credits"] == 0, "Credits"] = 1
        total_credits = df["Credits"].sum()
        if pd.isna(total_credits) or total_credits <= 0:
            total_credits = 1.0

        # --- Accurate per-course R-score gain calculation ---
        # Simulate a +3 grade point improvement for each course, safely handle zero/missing Std. Dev
        df["Z_base"] = df.apply(lambda r: zscore(r["Your Grade"], r["Class Avg"], r["Std. Dev"]), axis=1)
        df["Z_plus3"] = df.apply(lambda r: zscore(min(float(r["Your Grade"]) + 3.0, 100.0), r["Class Avg"], r["Std. Dev"]), axis=1)
        df["R_base"] = 35 + 5 * df["Z_base"]
        df["R_plus3"] = 35 + 5 * df["Z_plus3"]
        df["ΔR"] = df["R_plus3"] - df["R_base"]

        # Weight by credits to approximate total R impact
        df["gain_score"] = df["ΔR"] * df["Credits"]

        # Sort top 3 potential improvements
        df_sorted = df.sort_values("gain_score", ascending=False).head(3).reset_index(drop=True)

        # Build an ordered trio: Silver (left), Gold (center), Bronze (right)
        stage = []
        if len(df_sorted) >= 2:
            s = df_sorted.iloc[1] if len(df_sorted) > 1 else None
        else:
            s = None
        g = df_sorted.iloc[0] if len(df_sorted) > 0 else None
        b = df_sorted.iloc[2] if len(df_sorted) > 2 else None

        def card_html(row, medal, emoji, height_px, total_credits):
            if row is None:
                return ""
            # safe credits fallback
            try:
                credits = float(row.get("Credits", 1))
            except Exception:
                credits = 1.0
            if pd.isna(credits) or credits <= 0:
                credits = 1.0
            try:
                delta_r = float(row.get("ΔR", 0))
            except Exception:
                delta_r = 0.0
            overall_gain = round((delta_r * credits) / float(total_credits or 1.0), 2)

            bg = {
                "gold":   "linear-gradient(180deg,#facc15 0%,#fef9c3 100%)",
                "silver": "linear-gradient(180deg,#d1d5db 0%,#f3f4f6 100%)",
                "bronze": "linear-gradient(180deg,#f97316 0%,#fed7aa 100%)",
            }[medal]

            style = (
                f"height:{height_px}px; width:240px; display:grid; place-items:center;"
                " text-align:center; padding:18px; border-radius:24px; box-shadow:0 8px 25px rgba(0,0,0,0.1);"
                f" background:{bg};"
            )
            return (
                f'<div style="{style}">' \
                f'<div style="display:flex; flex-direction:column; align-items:center; gap:12px;">' \
                f'<div style="font-size:2rem; line-height:1;">{emoji}</div>' \
                f'<div style="font-size:1.1rem; font-weight:600; margin:0; line-height:1.2;">{row["Course Name"]}</div>' \
                f'<div style="font-size:1.5rem; margin:0; font-weight:700; line-height:1.2;">+{overall_gain} Overall R&#8209;score</div>' \
                f'</div>' \
                f'</div>'
            )

        silver_html = card_html(s, "silver", "🥈", 200, total_credits)
        gold_html   = card_html(g, "gold",   "🥇", 260, total_credits)
        bronze_html = card_html(b, "bronze", "🥉", 180, total_credits)

        html = (
            '<div style="display:flex;justify-content:center;align-items:flex-end;gap:16px;margin:16px 0 24px;">'
            f'{silver_html}{gold_html}{bronze_html}'
            '</div>'
        )
        st.markdown(html, unsafe_allow_html=True)

        # --- Example hypothesis generator ---
        st.markdown("### 📈 Hypothetical Improvements")

        insights = []
        for i, row in df_sorted.iterrows():
            course = row["Course Name"]
            per_course_gain = round(row["ΔR"], 2)
            overall_gain = round((row["ΔR"] * row["Credits"]) / df["Credits"].sum(), 2)
            insights.append(
                f"If you raise your **{course}** grade by **3 points**, "
                f"your overall R-score could rise by approximately **+{overall_gain}**."
            )

        for insight in insights:
            st.markdown(f"- {insight}")

        # ---- Revamped quick scenarios (compact chips) ----
        dfx = st.session_state.df.copy()
        if not dfx.empty:
            dfx = clean_numeric(dfx, ["Your Grade", "Class Avg", "Std. Dev", "Credits"])
            dfx["Credits"] = dfx["Credits"].fillna(1)
            dfx.loc[dfx["Credits"] == 0, "Credits"] = 1

            def overall_r_of(df_in):
                Z = (df_in["Your Grade"] - df_in["Class Avg"]) / df_in["Std. Dev"]
                R = 35.0 + 5.0 * Z
                return float((R * df_in["Credits"]).sum() / df_in["Credits"].sum())

            base = overall_r_of(dfx)
            plus1 = overall_r_of(dfx.assign(**{"Your Grade": (dfx["Your Grade"] + 1).clip(upper=100)}))
            plus2 = overall_r_of(dfx.assign(**{"Your Grade": (dfx["Your Grade"] + 2).clip(upper=100)}))
            plus3 = overall_r_of(dfx.assign(**{"Your Grade": (dfx["Your Grade"] + 3).clip(upper=100)}))

            st.markdown("### 🔮 Quick scenarios")
            st.markdown('<div class="chip-row">', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-chip"><div class="label">Baseline</div><div class="value">{base:.2f}</div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-chip"><div class="label">+1 to all grades</div><div class="value">{plus1:.2f}</div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-chip"><div class="label">+2 to all grades</div><div class="value">{plus2:.2f}</div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-chip"><div class="label">+3 to all grades</div><div class="value">{plus3:.2f}</div></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

# ---------- TAB 6 (Programs) ----------
with import_tab:
    require_premium()
with tab6:
    st.markdown('<div class="glass-toolbar">', unsafe_allow_html=True)
    uni_df = load_uni_csv()

    # Filters + selectors (left-justified; 5 controls + right spacer)
    cols = st.columns([1.4, 1.6, 1.8, 1.6, 2.4, 8])  # last column is an empty spacer to anchor left
    with cols[0]:
        uni_choice = st.selectbox("University", ["All"] + sorted(uni_df["university"].dropna().unique().tolist()))
    with cols[1]:
        prog_choice = st.selectbox("Program", ["All"] + sorted(uni_df["program"].dropna().unique().tolist()))
    with cols[2]:
        threshold_type = st.selectbox("Threshold", ["Minimum (acceptance)", "Recommended (competitive)"])
    with cols[3]:
        r_use_choice = st.selectbox("Use your R", ["Central", "Lower", "Higher"])
    with cols[4]:
        stretch_window = st.select_slider("Stretch (+R)", options=[0.5,1.0,1.5,2.0,2.5,3.0], value=1.5)
    # cols[5] is an empty spacer to keep the row left-aligned

    st.markdown('</div>', unsafe_allow_html=True)

    # Apply filters
    if uni_choice != "All":
        uni_df = uni_df[uni_df["university"] == uni_choice]
    if prog_choice != "All":
        uni_df = uni_df[uni_df["program"] == prog_choice]

    # Pick threshold column
    th_col = "min_r" if threshold_type.startswith("Minimum") else "rec_r"

    # Choose user's R according to selector (fallback compute if not present)
    central_r = st.session_state.get("overall_r_central", None)
    lower_r   = st.session_state.get("overall_r_min", None)
    higher_r  = st.session_state.get("overall_r_max", None)
    if central_r is None or pd.isna(central_r):
        df_tmp = st.session_state.df.copy()
        if not df_tmp.empty:
            df_tmp = clean_numeric(df_tmp, ["Your Grade", "Class Avg", "Std. Dev", "Credits"])
            df_tmp["Credits"] = df_tmp["Credits"].fillna(1)
            df_tmp.loc[df_tmp["Credits"] == 0, "Credits"] = 1
            Z = (df_tmp["Your Grade"] - df_tmp["Class Avg"]) / df_tmp["Std. Dev"]
            baseR = 35.0 + 5.0 * Z
            central_r = float((baseR * df_tmp["Credits"]).sum() / df_tmp["Credits"].sum())
            lower_r   = central_r + float(st.session_state.get("r_offset_min", -2.0))
            higher_r  = central_r + float(st.session_state.get("r_offset_max",  2.0))

    current_r = {"Central": central_r, "Lower": lower_r, "Higher": higher_r}.get(r_use_choice, central_r)

    if current_r is None or pd.isna(current_r):
        st.warning("Calculate your R in the Results tab first.")
    else:
        st.markdown(f"### Your selected R: **{current_r:.2f}**  •  Comparing to **{threshold_type.lower()}** thresholds")

        q = pd.to_numeric(uni_df[th_col], errors="coerce")
        qualified = uni_df[q <= current_r].sort_values(th_col)
        stretch   = uni_df[(q > current_r) & (q <= current_r + stretch_window)].sort_values(th_col)

        # ensure stretch has content if empty
        show_nearest_caption = False
        if stretch.empty and not uni_df.empty:
            stretch = uni_df[q > current_r].sort_values(th_col).head(5)
            show_nearest_caption = True

        # QUALIFIED (once)
        st.subheader("✅ You likely qualify for")
        if qualified.empty:
            st.write("No matches found.")
        else:
            for _, row in qualified.iterrows():
                st.markdown(
                    f'<div class="glass-card" style="background:rgba(17,24,39,0.9);color:white;">'
                    f'<div style="font-weight:600;">{row["university"]}</div>'
                    f'<div>{row["program"]}</div>'
                    f'<div style="opacity:0.7;">Min: {float(row["min_r"]):.2f} • Rec: {float(row["rec_r"]):.2f}</div>'
                    f'<a href="{row["url"]}" target="_blank" style="color:#6ee7b7;">Program page ↗</a>'
                    f'</div>',
                    unsafe_allow_html=True
                )

        # STRETCH (once)
        st.subheader(f"🟡 Stretch programs (≤ +{stretch_window:.1f} R)")
        if show_nearest_caption:
            st.caption("No stretch within window; showing nearest-above programs instead.")
        if stretch.empty:
            st.write("No stretch programs found — try improving your grades!")
        else:
            for _, row in stretch.iterrows():
                st.markdown(
                    f'<div class="glass-card" style="background:rgba(255,230,170,0.3);">'
                    f'<div style="font-weight:600;">{row["university"]}</div>'
                    f'<div>{row["program"]}</div>'
                    f'<div style="opacity:0.7;">Min: {float(row["min_r"]):.2f} • Rec: {float(row["rec_r"]):.2f}</div>'
                    f'<a href="{row["url"]}" target="_blank">Program page ↗</a>'
                    f'</div>',
                    unsafe_allow_html=True
                )

        # Only close toolbar div once

st.markdown("""
<hr style="margin-top:40px;opacity:0.3">
<div style="text-align:center; color:gray; font-size:0.9em;">
RScore Pro © 2025 • Built by Angus Beauregard<br>
<a href="https://rscore.app/privacy" target="_blank">Privacy Policy</a> •
<a href="https://rscore.app/terms" target="_blank">Terms of Service</a>
</div>
""", unsafe_allow_html=True)
