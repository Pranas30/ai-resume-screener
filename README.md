# 🚀 AI Resume Screening Agent

A Smart Recruitment Assistant built for the Rooman Technologies AI Challenge. 
This agent uses Generative AI (Google Gemini) to automate the resume screening process, helping HR teams filter candidates instantly based on job descriptions.

## 🌟 Features
* **Contextual Analysis:** Understands the semantic meaning of resumes, not just keyword matching.
* **Instant Scoring:** Ranks candidates from 0-100% based on relevance to the Job Description.
* **Explainable AI:** Provides a one-sentence logical reason for every score (e.g., "High match but lacks 2 years of experience").
* **Privacy-First:** Processes resumes in memory without saving files permanently to a database.

## 🛠️ Tech Stack
* **Frontend:** HTML5, CSS3, JavaScript (Vanilla)
* **Backend:** Python, Flask
* **AI Engine:** Google Gemini Pro / Flash (via Google Generative AI API)
* **PDF Processing:** PyPDF2
* **Deployment:** Render / Gunicorn

## 🚀 How to Run Locally

1.  **Clone the Repository**
    ```bash
    git clone [https://github.com/YOUR_USERNAME/ai-resume-screener.git](https://github.com/YOUR_USERNAME/ai-resume-screener.git)
    cd ai-resume-screener
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set Up API Key**
    * Get a free key from [Google AI Studio](https://aistudio.google.com/app/apikey).
    * (Linux/Mac): `export GEMINI_API_KEY="your_key_here"`
    * (Windows): `set GEMINI_API_KEY=your_key_here`

4.  **Run the App**
    ```bash
    python app.py
    ```
    Visit `http://localhost:5000` in your browser.

## ⚠️ Limitations
* Currently accepts **PDF only** (not Word docs).
* Cannot read scanned/image-based PDFs (requires OCR update).
* Rate limits depend on the Google Gemini Free Tier (15 RPM).

## 🔮 Future Improvements
* Add OCR (Tesseract) to read scanned resumes.
* Add Email integration to auto-reject/shortlist candidates.
* Add a dashboard to save and export history to CSV.
