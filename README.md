# 🤖 LinkedIn AI Resume Agent

A production-grade, full-stack AI career assistant designed to search jobs on LinkedIn, audit your resume against target requirements, calculate ATS match scorecards, and dynamically generate tailored resumes and cover letters—all managed via a modern, glassmorphic dark-mode web dashboard.

---

## 🚀 Key Features

* **Glassmorphic Web Dashboard**: A premium, responsive interface featuring live PDF previews, a interactive scorecard, a download center, and active job management.
* **AI Career Agent Chat**: A built-in career coach with guardrails that handles resume questions, matching logic, and processes real-time scraper requests (e.g., *"Find ML Engineer jobs in London"*).
* **Factual ATS Tailoring**: Tailors your resume and cover letter using advanced Groq fallback LLM configurations. strictly follows **anti-fabrication rules** (no invented certifications, metrics, or titles).
* **Premium Exporter Engine**: Custom-built raw PDF and Word (.docx) builders featuring centered letterheads, clean dividers, and Latin-1 encoding translations to prevent rendering issues.
* **Dual Execution Modes**: Launcher supports running either the graphical web dashboard (default) or a fast command-line tailorer (`python main.py --cli`).

---

## 🛠️ Tech Stack

* **Backend**: Python 3 (standard stateless socket router `http.server`).
* **Frontend**: HTML5, Vanilla CSS3 (Custom Glassmorphism styling variables), JavaScript (V8 fetch logic, markdown parser).
* **AI / Matching**: Groq Fallback API (Llama 3.3, Llama 3.1, Mixtral) with tag-based tool calling.
* **Document Compilation**: Pure Python canvas operations (`pdf_generator.py`) and zipfile OpenXML writers (`docx_utils.py`) to bypass heavy system dependencies.

---

## 📦 Directory Structure

```text
├── main.py                     # Entry point (CLI & Dashboard launcher)
├── server.py                   # Web application server & endpoints
├── pipeline.py                 # Core resume tailoring and matching pipeline
├── groq_client.py              # LLM integration client
├── pdf_generator.py            # High-end custom PDF exporter
├── docx_utils.py               # OpenXML Word exporter
├── pdf_utils.py                # Text extraction helper
├── scrape_linkedin_jobs.py     # LinkedIn job scraper
├── requirements.txt            # Dependency listings
├── templates/                  # Jinja2 layout templates
└── static/                     # HTML/CSS/JS frontend files
```

---

## 🚦 Local Installation & Run

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/<your-username>/linkedin-resume-agent.git
   cd linkedin-resume-agent
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   Create a `.env` file in the root directory and add your credentials:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```

4. **Launch the Dashboard**:
   ```bash
   python main.py
   ```
   Open your browser and navigate to [http://localhost:8000/](http://localhost:8000/).

5. **Run CLI Mode (Alternative)**:
   ```bash
   python main.py --cli
   ```

---

## ☁️ Deployment (Free on Render)

This application is configured for deployment on the **Render Free Tier**:
1. Connect your GitHub repository to [Render.com](https://render.com/).
2. Create a new **Web Service**.
3. Set the build command to `pip install -r requirements.txt` and the start command to `python main.py`.
4. Add the `GROQ_API_KEY` environment variable in Render's dashboard. Render automatically configures the `$PORT` routing, which the app reads dynamically.
