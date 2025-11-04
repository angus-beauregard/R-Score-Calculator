# 📊 RScore Pro — Quebec CEGEP R-Score Helper

**Your R-Score, cleaned up.**  
RScore Pro is a simple, privacy-focused tool for CEGEP students to calculate and visualize their R-scores. It supports **manual entry (free)** and **Pro features (OCR import, credit autofill, and comparisons)** while running fully in your browser — no Omnivox login required.

---

## 🚀 Features

### 🆓 Free Tools
- Manual course entry
- Automatic R-score calculation
- Adjustable min/max settings

### 💎 Pro Tools (Mocked for now)
- OCR import from Omnivox screenshots
- Automatic credit autofill
- Program comparison tools

### 🧠 Trust & Privacy
- Runs fully in your browser
- No Omnivox credentials are ever stored or requested
- Transparent R-score formula

---

## 🧩 Tech Stack

- **Frontend:** [Streamlit](https://streamlit.io/)
- **Language:** Python 3.13+
- **UI Styling:** Custom HTML + CSS (via Streamlit markdown)
- **Deployment:** Streamlit Cloud (`streamlit.app`)

---

## 🖥️ Local Setup

Clone the repository and install dependencies.

```bash
# Clone this repo
git clone https://github.com/<your-username>/rscore-pro.git
cd rscore-pro

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
venv\Scripts\activate     # On Windows

# Install requirements
pip install -r requirements.txt
