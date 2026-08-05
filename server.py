import os
import json
import urllib.parse
import re
from http.server import SimpleHTTPRequestHandler, HTTPServer
from jinja2 import Environment, FileSystemLoader
from pipeline import ResumePipeline
from pdf_generator import json_to_pdf, text_to_pdf
from docx_utils import json_to_docx, text_to_docx

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

PIPELINE = ResumePipeline()
JINJA_ENV = Environment(loader=FileSystemLoader("templates"))

STATE = {
    "current_job_id": None,
    "analysis": None,
    "tailored_cv": None,
    "cover_letter": None
}

class SaaSRequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)
        
        if path == "/" or path == "/index.html":
            self.serve_static_file("static/index.html", "text/html")
            return
        elif path == "/styles.css":
            self.serve_static_file("static/styles.css", "text/css")
            return
        elif path == "/app.js":
            self.serve_static_file("static/app.js", "application/javascript")
            return
        elif path == "/api/jobs":
            self.handle_get_jobs()
        elif path == "/api/analyze":
            self.handle_analyze(query)
        elif path == "/api/tailor":
            self.handle_tailor(query)
        elif path == "/api/preview":
            self.handle_preview(query)
        elif path == "/api/cover-letter":
            self.handle_preview_cover_letter()
        elif path == "/api/download":
            self.handle_download(query)
        else:
            super().do_GET()

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        
        if path == "/api/upload":
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self.send_json_response({"error": "Empty file payload"}, 400)
                return
            
            # Read and write uploaded PDF resume
            pdf_bytes = self.rfile.read(content_length)
            with open("AI-ML resume.pdf", "wb") as f:
                f.write(pdf_bytes)
                
            print("[API] Uploaded new resume saved to: AI-ML resume.pdf")
            
            # Reset tailoring state so client regenerates against new resume
            STATE["analysis"] = None
            STATE["tailored_cv"] = None
            STATE["cover_letter"] = None
            
            self.send_json_response({"status": "success", "message": "Resume uploaded and loaded successfully."})
        elif path == "/api/chat":
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self.send_json_response({"error": "Empty message body"}, 400)
                return
                
            post_data = self.rfile.read(content_length).decode('utf-8')
            request_json = json.loads(post_data)
            user_message = request_json.get("message", "")
            
            active_job_id = STATE.get("current_job_id")
            active_job_info = "None selected"
            jobs = PIPELINE.load_jobs()
            if active_job_id is not None and 0 <= active_job_id < len(jobs):
                j = jobs[active_job_id]
                active_job_info = f"Title: {j.get('title')}, Company: {j.get('company')}, Location: {j.get('location')}"
            
            # Load candidate resume summary details
            resume_data = PIPELINE.parse_resume()
            resume_summary = (
                f"Name: {resume_data.get('name', 'Muhammad Abdullah Bilal')}\n"
                f"Title: {resume_data.get('title', 'AI/ML Engineer')}\n"
                f"Summary: {resume_data.get('summary', '')}\n"
                f"Skills: {json.dumps(resume_data.get('skills', {}))}\n"
                f"Experiences: {', '.join([exp.get('role', '') + ' at ' + exp.get('company', '') for exp in resume_data.get('experience', [])])}"
            )
            
            # Load dashboard jobs list summary
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
                
                # Tag-based parser
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
                
            trigger_search = chat_data.get("trigger_search", False)
            if trigger_search:
                params = chat_data.get("search_params", {})
                kw = params.get("keywords", "AI Engineer")
                loc = params.get("location", "London")
                cnt = params.get("count", 10)
                
                print(f"[API Chat] Starting LinkedIn search: keywords='{kw}', location='{loc}', count={cnt}...")
                try:
                    from scrape_linkedin_jobs import fetch_recent_jobs
                    new_jobs = fetch_recent_jobs(kw, loc, cnt)
                    if new_jobs:
                        with open("linkedin_ai_engineer_jobs.json", "w", encoding="utf-8") as f:
                            json.dump(new_jobs, f, indent=2, ensure_ascii=False)
                        print(f"[API Chat] Saved {len(new_jobs)} new jobs to linkedin_ai_engineer_jobs.json")
                        chat_data["response"] += f"\n\n[System] Successfully scraped and loaded {len(new_jobs)} recent roles for '{kw}' in '{loc}' into the Job Search panel! Please go to the Job Search tab to view them."
                        chat_data["jobs_updated"] = True
                    else:
                        chat_data["response"] += f"\n\n[System] Search completed but no recent jobs (posted <= 3 weeks ago) matching '{kw}' were found in '{loc}'."
                        chat_data["jobs_updated"] = False
                except Exception as scrape_err:
                    print(f"Scraping failed: {scrape_err}")
                    chat_data["response"] += f"\n\n[System Error] Failed to execute scraping script: {scrape_err}"
                    chat_data["jobs_updated"] = False
            else:
                chat_data["jobs_updated"] = False
                
            self.send_json_response(chat_data)
        else:
            self.send_error(404, "Not found")

    def serve_static_file(self, filepath: str, content_type: str):
        if not os.path.exists(filepath):
            self.send_error(404, "File not found")
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.end_headers()
        with open(filepath, "rb") as f:
            self.wfile.write(f.read())

    def send_json_response(self, data: dict, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def handle_get_jobs(self):
        jobs = PIPELINE.load_jobs()
        formatted_jobs = []
        for idx, job in enumerate(jobs):
            job_copy = job.copy()
            job_copy["job_id"] = str(idx)
            formatted_jobs.append(job_copy)
        self.send_json_response(formatted_jobs)

    def handle_analyze(self, query):
        job_id_list = query.get("job_id")
        if not job_id_list:
            self.send_json_response({"error": "Missing job_id parameter"}, 400)
            return
        
        job_id = int(job_id_list[0])
        jobs = PIPELINE.load_jobs()
        if job_id < 0 or job_id >= len(jobs):
            self.send_json_response({"error": "Invalid job_id"}, 400)
            return
            
        job = jobs[job_id]
        print(f"[API] Starting ATS analysis & tailoring for job ID {job_id}...")
        
        job_data = PIPELINE.parse_job(job)
        resume_data = PIPELINE.parse_resume()
        
        # 1. Analyze match
        analysis = PIPELINE.analyze_match(resume_data, job_data)
        
        # 2. Automatically trigger tailoring so it's ready instantly!
        print(f"[API] Tailoring CV & Cover Letter in background for job ID {job_id}...")
        tailored_cv = PIPELINE.tailor_cv(resume_data, job_data)
        cover_letter = PIPELINE.build_cover_letter(resume_data, job_data)
        
        STATE["current_job_id"] = job_id
        STATE["analysis"] = analysis
        STATE["tailored_cv"] = tailored_cv
        STATE["cover_letter"] = cover_letter
        
        # Export files immediately to company output folder
        folder_name = f"{PIPELINE.base_output_dir}/SaaS_{sanitize_filename(job_data['company'])}"
        os.makedirs(folder_name, exist_ok=True)
        json_to_pdf(tailored_cv, f"{folder_name}/tailored_cv.pdf")
        json_to_docx(tailored_cv, f"{folder_name}/tailored_cv.docx")
        text_to_pdf(cover_letter, f"{folder_name}/cover_letter.pdf", "Cover Letter")
        text_to_docx(cover_letter, f"{folder_name}/cover_letter.docx")
        
        self.send_json_response({
            "job": job_data,
            "analysis": analysis
        })

    def handle_tailor(self, query):
        job_id_list = query.get("job_id")
        if not job_id_list:
            self.send_json_response({"error": "Missing job_id parameter"}, 400)
            return
            
        job_id = int(job_id_list[0])
        jobs = PIPELINE.load_jobs()
        if job_id < 0 or job_id >= len(jobs):
            self.send_json_response({"error": "Invalid job_id"}, 400)
            return
            
        job = jobs[job_id]
        print(f"[API] Generating tailored CV & Cover Letter for job ID {job_id}...")
        
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
        
        self.send_json_response({
            "status": "success",
            "tailored_cv": tailored_cv,
            "cover_letter": cover_letter
        })

    def handle_preview(self, query):
        template_list = query.get("template")
        template_name = template_list[0] if template_list else "modern"
        
        cv_data = STATE["tailored_cv"]
        if not cv_data:
            cv_data = PIPELINE.parse_resume()
            
        try:
            template = JINJA_ENV.get_template(f"{template_name}.html")
            html_content = template.render(**cv_data)
            
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(html_content.encode("utf-8"))
        except Exception as e:
            self.send_error(500, f"Template rendering error: {e}")

    def handle_preview_cover_letter(self):
        letter_text = STATE["cover_letter"]
        if not letter_text:
            letter_text = "Please tailor your cover letter first via the Dashboard."
            
        cleaned_text = strip_candidate_header(letter_text)
        paragraphs = [f"<p>{p.strip()}</p>" for p in cleaned_text.split("\n\n") if p.strip()]
        paragraphs_html = "\n".join(paragraphs)
        
        # Load the correct target company name dynamically
        job_id = STATE.get("current_job_id")
        company_name = "Target Company"
        if job_id is not None:
            jobs = PIPELINE.load_jobs()
            if 0 <= job_id < len(jobs):
                company_name = jobs[job_id].get("company", "Target Company")
                
        cv_data = PIPELINE.parse_resume()
        
        try:
            template = JINJA_ENV.get_template("cover_letter.html")
            html_content = template.render(
                name="Muhammad Abdullah Bilal",
                contact_details="Faisalabad, Pakistan | +92 340 7437039 | muhammadabdullahb52@gmail.com",
                date="August 5, 2026",
                company=company_name,
                paragraphs_html=paragraphs_html
            )
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(html_content.encode("utf-8"))
        except Exception as e:
            self.send_error(500, f"Template rendering error: {e}")

    def handle_download(self, query):
        dl_type_list = query.get("type")
        if not dl_type_list:
            self.send_error(400, "Missing type parameter")
            return
            
        dl_type = dl_type_list[0]
        cv_data = STATE["tailored_cv"]
        letter_text = STATE["cover_letter"]
        
        if not cv_data or not letter_text:
            self.send_error(400, "No tailored resume session active. Please analyze & tailor first.")
            return
            
        filename = ""
        content_type = ""
        data_bytes = b""
        
        temp_path = "temp_download"
        
        if dl_type == "pdf":
            cv_pdf_path = f"{temp_path}_cv.pdf"
            json_to_pdf(cv_data, cv_pdf_path)
            filename = "tailored_cv.pdf"
            content_type = "application/pdf"
            with open(cv_pdf_path, "rb") as f:
                data_bytes = f.read()
            os.remove(cv_pdf_path)
            
        elif dl_type == "docx":
            cv_docx_path = f"{temp_path}_cv.docx"
            json_to_docx(cv_data, cv_docx_path)
            filename = "tailored_cv.docx"
            content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            with open(cv_docx_path, "rb") as f:
                data_bytes = f.read()
            os.remove(cv_docx_path)
            
        elif dl_type == "letter_pdf":
            letter_pdf_path = f"{temp_path}_letter.pdf"
            text_to_pdf(letter_text, letter_pdf_path, "Cover Letter")
            filename = "cover_letter.pdf"
            content_type = "application/pdf"
            with open(letter_pdf_path, "rb") as f:
                data_bytes = f.read()
            os.remove(letter_pdf_path)
            
        elif dl_type == "letter_docx":
            letter_docx_path = f"{temp_path}_letter.docx"
            text_to_docx(letter_text, letter_docx_path)
            filename = "cover_letter.docx"
            content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            with open(letter_docx_path, "rb") as f:
                data_bytes = f.read()
            os.remove(letter_docx_path)
            
        else:
            self.send_error(400, "Invalid type")
            return
            
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Disposition", f"attachment; filename={filename}")
        self.send_header("Content-Length", str(len(data_bytes)))
        self.end_headers()
        self.wfile.write(data_bytes)

def run_server(port=8000):
    server_address = ("", port)
    httpd = HTTPServer(server_address, SaaSRequestHandler)
    print(f"==================================================")
    print(f" LinkedIn AI Resume Agent SaaS Dashboard Online! ")
    print(f" Dashboard URL: http://localhost:{port}/ ")
    print(f"==================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping SaaS application server...")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
