import os
import json
import re
import io
from flask import Flask, request, jsonify, send_from_directory, make_response, send_file
from jinja2 import Environment, FileSystemLoader
from pipeline import ResumePipeline
from pdf_generator import json_to_pdf, text_to_pdf
from docx_utils import json_to_docx, text_to_docx

app = Flask(__name__)

# Initialize pipeline and environments
PIPELINE = ResumePipeline()
JINJA_ENV = Environment(loader=FileSystemLoader("templates"))

STATE = {
    "current_job_id": None,
    "analysis": None,
    "tailored_cv": None,
    "cover_letter": None
}

def sanitize_filename(name: str) -> str:
    clean = re.sub(r'[^\w\s-]', '', name).strip()
    return re.sub(r'[-\s]+', '_', clean)

def strip_candidate_header(text: str) -> str:
    lines = text.splitlines()
    clean_lines = []
    stripped_count = 0
    
    for line in lines:
        s = line.strip()
        if not s:
            clean_lines.append("")
            continue
            
        if stripped_count < 4:
            s_low = s.lower()
            if ("abdullah" in s_low or "bilal" in s_low or 
                "faisalabad" in s_low or "pakistan" in s_low or 
                "340" in s_low or "7437039" in s_low or 
                "gmail.com" in s_low or "muhammad" in s_low):
                stripped_count += 1
                continue
                
        clean_lines.append(line)
        
    return "\n".join(clean_lines)

# --- Frontend Routes ---

@app.route("/")
@app.route("/index.html")
def index():
    return send_from_directory("static", "index.html")

@app.route("/styles.css")
def styles():
    return send_from_directory("static", "styles.css")

@app.route("/app.js")
def app_js():
    return send_from_directory("static", "app.js")

# --- API Endpoints ---

@app.route("/api/jobs", methods=["GET"])
def get_jobs():
    jobs = PIPELINE.load_jobs()
    formatted_jobs = []
    for idx, job in enumerate(jobs):
        job_copy = job.copy()
        job_copy["job_id"] = str(idx)
        formatted_jobs.append(job_copy)
    return jsonify(formatted_jobs)

@app.route("/api/upload", methods=["POST"])
def upload_resume():
    pdf_bytes = request.data
    if not pdf_bytes:
        return jsonify({"error": "Empty file payload"}), 400
        
    with open("AI-ML resume.pdf", "wb") as f:
        f.write(pdf_bytes)
        
    print("[API Flask] Uploaded new resume saved to: AI-ML resume.pdf")
    
    # Reset tailoring state so client regenerates against new resume
    STATE["analysis"] = None
    STATE["tailored_cv"] = None
    STATE["cover_letter"] = None
    
    return jsonify({"status": "success", "message": "Resume uploaded successfully."})

@app.route("/api/analyze", methods=["GET"])
def analyze_job():
    job_id_str = request.args.get("job_id")
    if not job_id_str:
        return jsonify({"error": "Missing job_id parameter"}), 400
        
    job_id = int(job_id_str)
    jobs = PIPELINE.load_jobs()
    if job_id < 0 or job_id >= len(jobs):
        return jsonify({"error": "Invalid job_id"}), 400
        
    job = jobs[job_id]
    print(f"[API Flask] Starting ATS analysis & tailoring for job ID {job_id}...")
    
    job_data = PIPELINE.parse_job(job)
    resume_data = PIPELINE.parse_resume()
    
    analysis = PIPELINE.analyze_match(resume_data, job_data)
    tailored_cv = PIPELINE.tailor_cv(resume_data, job_data)
    cover_letter = PIPELINE.build_cover_letter(resume_data, job_data)
    
    STATE["current_job_id"] = job_id
    STATE["analysis"] = analysis
    STATE["tailored_cv"] = tailored_cv
    STATE["cover_letter"] = cover_letter
    
    # Export files to company output folder
    folder_name = f"{PIPELINE.base_output_dir}/SaaS_{sanitize_filename(job_data['company'])}"
    os.makedirs(folder_name, exist_ok=True)
    json_to_pdf(tailored_cv, f"{folder_name}/tailored_cv.pdf")
    json_to_docx(tailored_cv, f"{folder_name}/tailored_cv.docx")
    text_to_pdf(cover_letter, f"{folder_name}/cover_letter.pdf", "Cover Letter")
    text_to_docx(cover_letter, f"{folder_name}/cover_letter.docx")
    
    return jsonify({
        "job": job_data,
        "analysis": analysis
    })

@app.route("/api/tailor", methods=["GET"])
def tailor_documents():
    job_id_str = request.args.get("job_id")
    if not job_id_str:
        return jsonify({"error": "Missing job_id parameter"}), 400
        
    job_id = int(job_id_str)
    jobs = PIPELINE.load_jobs()
    if job_id < 0 or job_id >= len(jobs):
        return jsonify({"error": "Invalid job_id"}), 400
        
    job = jobs[job_id]
    print(f"[API Flask] Generating tailored CV & Cover Letter for job ID {job_id}...")
    
    job_data = PIPELINE.parse_job(job)
    resume_data = PIPELINE.parse_resume()
    
    tailored_cv = PIPELINE.tailor_cv(resume_data, job_data)
    cover_letter = PIPELINE.build_cover_letter(resume_data, job_data)
    
    STATE["tailored_cv"] = tailored_cv
    STATE["cover_letter"] = cover_letter
    
    folder_name = f"{PIPELINE.base_output_dir}/SaaS_{PIPELINE.load_jobs()[job_id]['company']}"
    os.makedirs(folder_name, exist_ok=True)
    
    json_to_pdf(tailored_cv, f"{folder_name}/tailored_cv.pdf")
    json_to_docx(tailored_cv, f"{folder_name}/tailored_cv.docx")
    text_to_pdf(cover_letter, f"{folder_name}/cover_letter.pdf", "Cover Letter")
    text_to_docx(cover_letter, f"{folder_name}/cover_letter.docx")
    
    return jsonify({
        "status": "success",
        "tailored_cv": tailored_cv,
        "cover_letter": cover_letter
    })

@app.route("/api/preview", methods=["GET"])
def preview_cv():
    template_name = request.args.get("template", "modern")
    cv_data = STATE["tailored_cv"]
    if not cv_data:
        cv_data = PIPELINE.parse_resume()
        
    try:
        template = JINJA_ENV.get_template(f"{template_name}.html")
        html_content = template.render(**cv_data)
        response = make_response(html_content)
        response.headers["Content-Type"] = "text/html"
        return response
    except Exception as e:
        return f"Template rendering error: {e}", 500

@app.route("/api/cover-letter", methods=["GET"])
def preview_cover_letter():
    letter_text = STATE["cover_letter"]
    if not letter_text:
        letter_text = "Please tailor your cover letter first via the Dashboard."
        
    cleaned_text = strip_candidate_header(letter_text)
    paragraphs = [f"<p>{p.strip()}</p>" for p in cleaned_text.split("\n\n") if p.strip()]
    paragraphs_html = "\n".join(paragraphs)
    
    job_id = STATE.get("current_job_id")
    company_name = "Target Company"
    if job_id is not None:
        jobs = PIPELINE.load_jobs()
        if 0 <= job_id < len(jobs):
            company_name = jobs[job_id].get("company", "Target Company")
            
    try:
        template = JINJA_ENV.get_template("cover_letter.html")
        html_content = template.render(
            name="Muhammad Abdullah Bilal",
            contact_details="Faisalabad, Pakistan | +92 340 7437039 | muhammadabdullahb52@gmail.com",
            date="August 5, 2026",
            company=company_name,
            paragraphs_html=paragraphs_html
        )
        response = make_response(html_content)
        response.headers["Content-Type"] = "text/html"
        return response
    except Exception as e:
        return f"Template rendering error: {e}", 500

@app.route("/api/download", methods=["GET"])
def download_document():
    dl_type = request.args.get("type")
    if not dl_type:
        return "Missing type parameter", 400
        
    cv_data = STATE["tailored_cv"]
    letter_text = STATE["cover_letter"]
    
    if not cv_data or not letter_text:
        return "No tailored resume session active. Please analyze & tailor first.", 400
        
    filename = ""
    content_type = ""
    temp_path = "temp_download"
    
    if dl_type == "pdf":
        cv_pdf_path = f"{temp_path}_cv.pdf"
        json_to_pdf(cv_data, cv_pdf_path)
        filename = "tailored_cv.pdf"
        content_type = "application/pdf"
        response = send_file(cv_pdf_path, mimetype=content_type, as_attachment=True, download_name=filename)
        # Delete temp file after sending
        @response.call_on_close
        def remove_file():
            if os.path.exists(cv_pdf_path):
                os.remove(cv_pdf_path)
        return response
        
    elif dl_type == "docx":
        cv_docx_path = f"{temp_path}_cv.docx"
        json_to_docx(cv_data, cv_docx_path)
        filename = "tailored_cv.docx"
        content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        response = send_file(cv_docx_path, mimetype=content_type, as_attachment=True, download_name=filename)
        @response.call_on_close
        def remove_file():
            if os.path.exists(cv_docx_path):
                os.remove(cv_docx_path)
        return response
        
    elif dl_type == "letter_pdf":
        letter_pdf_path = f"{temp_path}_letter.pdf"
        text_to_pdf(letter_text, letter_pdf_path, "Cover Letter")
        filename = "cover_letter.pdf"
        content_type = "application/pdf"
        response = send_file(letter_pdf_path, mimetype=content_type, as_attachment=True, download_name=filename)
        @response.call_on_close
        def remove_file():
            if os.path.exists(letter_pdf_path):
                os.remove(letter_pdf_path)
        return response
        
    elif dl_type == "letter_docx":
        letter_docx_path = f"{temp_path}_letter.docx"
        text_to_docx(letter_text, letter_docx_path)
        filename = "cover_letter.docx"
        content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        response = send_file(letter_docx_path, mimetype=content_type, as_attachment=True, download_name=filename)
        @response.call_on_close
        def remove_file():
            if os.path.exists(letter_docx_path):
                os.remove(letter_docx_path)
        return response
    else:
        return "Invalid type", 400

@app.route("/api/chat", methods=["POST"])
def chat():
    request_json = request.get_json(silent=True) or {}
    user_message = request_json.get("message", "")
    if not user_message:
        return jsonify({"error": "Empty message body"}), 400
        
    active_job_id = STATE.get("current_job_id")
    active_job_info = "None selected"
    jobs = PIPELINE.load_jobs()
    if active_job_id is not None and 0 <= active_job_id < len(jobs):
        j = jobs[active_job_id]
        active_job_info = f"Title: {j.get('title')}, Company: {j.get('company')}, Location: {j.get('location')}"
    
    resume_data = PIPELINE.parse_resume()
    resume_summary = (
        f"Name: {resume_data.get('name', 'Muhammad Abdullah Bilal')}\n"
        f"Title: {resume_data.get('title', 'AI/ML Engineer')}\n"
        f"Summary: {resume_data.get('summary', '')}\n"
        f"Skills: {json.dumps(resume_data.get('skills', {}))}\n"
        f"Experiences: {', '.join([exp.get('role', '') + ' at ' + exp.get('company', '') for exp in resume_data.get('experience', [])])}"
    )
    
    jobs_list_summary = ""
    for idx, job in enumerate(jobs[:10]):
        jobs_list_summary += f"Job ID {idx}: {job.get('title')} at {job.get('company')} ({job.get('location')})\n"
        
    system_prompt = (
        "You are an expert AI Career Coach and Resume Matching Specialist for Muhammad Abdullah Bilal.\n"
        "You are helping the candidate evaluate their resume, match skills, and prepare for interviews.\n\n"
        "CANDIDATE RESUME PROFILE:\n" + resume_summary + "\n\n"
        "DASHBOARD JOBS LIST:\n" + jobs_list_summary + "\n"
        "Active Job selected: " + active_job_info + "\n\n"
        "STRICT GUARDRAILS:\n"
        "1. You must ONLY answer questions relating to the candidate's career, resume, target jobs, portfolio, interview prep, and job searching. If the user asks general knowledge questions (e.g., 'what is the capital of X', 'solve this math equation', or general programming puzzles), you MUST politely decline to answer, stating that you are an AI Career Coach dedicated to their job search, and steer them back to career topics.\n"
        "2. If the user asks to score, rank, compare, or evaluate their resume against 'all jobs' or 'the dashboard jobs', you MUST calculate and return an estimated matching score (e.g., 8.5/10) for each of the 10 dashboard jobs listed above, explaining the reason for the score based on their resume profile.\n"
        "3. If the user asks to search, find, or scrape jobs on LinkedIn, you MUST append a search trigger line at the very end of your response on a new line: \n"
        "   [SEARCH_TRIGGER] {\"keywords\": \"<target search term>\", \"location\": \"<target location (default: London)>\", \"count\": 10}\n"
        "   Only output this tag if a LinkedIn job search is requested. Do NOT output it for general career discussion.\n"
        "4. Always reply in clean markdown. Wrap important headers and labels in **bold**.\n"
        "5. When presenting scores, comparative ranks, or tabular details (such as scoring all 10 jobs), you MUST present the data in a clean, highly structured Markdown Table format (e.g. | Job ID | Job Title & Company | Matching Score | Key Reason |). Do NOT use plain lists for tabular data. Do NOT output raw HTML tags.\n"
        "6. Keep your responses extremely concise, short, and direct. Avoid long, wordy introductions, repetitive pleasantries, or lengthy conclusions. Focus on high density of information in as few words as possible.\n\n"
        "Format your response as a standard conversational markdown text. Do NOT wrap your entire response in JSON."
    )
    
    from groq_client import chat_with_fallback
    try:
        raw_reply = chat_with_fallback(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        trigger_search = False
        search_params = {}
        response_text = raw_reply
        
        trigger_tag = "[SEARCH_TRIGGER]"
        if trigger_tag in raw_reply:
            parts = raw_reply.split(trigger_tag, 1)
            response_text = parts[0].strip()
            json_str = parts[1].strip()
            try:
                start_idx = json_str.find('{')
                end_idx = json_str.rfind('}')
                if start_idx != -1 and end_idx != -1:
                    search_params = json.loads(json_str[start_idx:end_idx+1])
                    trigger_search = True
            except Exception as json_err:
                print(f"Failed to parse search params JSON: {json_err}")
        
        chat_data = {
            "response": response_text,
            "trigger_search": trigger_search,
            "search_params": search_params
        }
    except Exception as err:
        chat_data = {
            "response": f"Sorry, I encountered an error communicating with the chat service: {err}",
            "trigger_search": False
        }
        
    # Execute scrape if triggered
    if chat_data.get("trigger_search", False):
        params = chat_data.get("search_params", {})
        kw = params.get("keywords", "AI Engineer")
        loc = params.get("location", "London")
        cnt = params.get("count", 10)
        
        print(f"[API Flask Chat] Starting LinkedIn search: keywords='{kw}', location='{loc}', count={cnt}...")
        try:
            from scrape_linkedin_jobs import fetch_recent_jobs
            new_jobs = fetch_recent_jobs(kw, loc, cnt)
            if new_jobs:
                with open("linkedin_ai_engineer_jobs.json", "w", encoding="utf-8") as f:
                    json.dump(new_jobs, f, indent=2, ensure_ascii=False)
                chat_data["response"] += f"\n\n[System] Successfully scraped and loaded {len(new_jobs)} recent roles for '{kw}' in '{loc}' into the Job Search panel! Please go to the Job Search tab to view them."
                chat_data["jobs_updated"] = True
            else:
                chat_data["response"] += f"\n\n[System] Search completed but no recent jobs (posted <= 3 weeks ago) matching '{kw}' were found in '{loc}'."
                chat_data["jobs_updated"] = False
        except Exception as scrape_err:
            chat_data["response"] += f"\n\n[System Error] Failed to execute scraping script: {scrape_err}"
            chat_data["jobs_updated"] = False
    else:
        chat_data["jobs_updated"] = False
        
    return jsonify(chat_data)

if __name__ == "__main__":
    app.run(port=8000, debug=True)
