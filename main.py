import os
import sys
import json
import glob
import re
from pdf_utils import extract_text_from_pdf
from groq_client import evaluate_job_match, generate_tailored_cv, generate_cover_letter
from docx_utils import json_to_docx, text_to_docx
from pdf_generator import json_to_pdf, text_to_pdf
from server import run_server

def sanitize_filename(name: str) -> str:
    """
    Sanitizes string for valid directory and filename creation.
    """
    clean = re.sub(r'[^\w\s-]', '', name).strip()
    return re.sub(r'[-\s]+', '_', clean)

def json_to_markdown(data: dict) -> str:
    """
    Converts structured CV JSON back to clean Markdown text for previewing.
    """
    md = []
    md.append(f"# {data.get('name', 'Muhammad Abdullah Bilal')}\n")
    md.append(f"## {data.get('title', 'AI/ML Engineer')}\n")
    
    contact = data.get("contact", {})
    contact_parts = []
    if contact.get("location"): contact_parts.append(contact["location"])
    if contact.get("phone"): contact_parts.append(contact["phone"])
    if contact.get("email"): contact_parts.append(contact["email"])
    if contact.get("linkedin"): contact_parts.append(f"LinkedIn: {contact['linkedin']}")
    if contact.get("github"): contact_parts.append(f"GitHub: {contact['github']}")
    md.append(" | ".join(contact_parts) + "\n")
    
    if data.get("summary"):
        md.append(f"# Professional Summary\n{data['summary']}\n")
        
    if data.get("skills"):
        md.append("# Technical Skills\n")
        for cat, items in data["skills"].items():
            md.append(f"- **{cat}**: {', '.join(items)}")
        md.append("")
        
    if data.get("experience"):
        md.append("# Professional Experience\n")
        for exp in data["experience"]:
            md.append(f"### {exp.get('role', '')} – {exp.get('company', '')} ({exp.get('duration', '')})")
            for bullet in exp.get("bullets", []):
                md.append(f"- {bullet}")
            md.append("")
            
    if data.get("projects"):
        md.append("# Key Projects\n")
        for proj in data["projects"]:
            md.append(f"### {proj.get('name', '')}")
            for bullet in proj.get("bullets", []):
                md.append(f"- {bullet}")
            if proj.get("technologies"):
                md.append(f"- **Technologies Used**: {', '.join(proj.get('technologies', []))}")
            md.append("")
            
    if data.get("education"):
        md.append("# Education\n")
        for edu in data["education"]:
            md.append(f"### {edu.get('degree', '')} – {edu.get('institution', '')} ({edu.get('duration', '')})")
            
    if data.get("certifications"):
        md.append("\n# Certifications & Achievements\n")
        for cert in data["certifications"]:
            md.append(f"- {cert}")
            
    if data.get("activities"):
        md.append("\n# Activities\n")
        for act in data["activities"]:
            md.append(f"### {act.get('role', '')} – {act.get('organization', '')}")
            if act.get("description"):
                md.append(act.get('description', ''))
            md.append("")
            
    return "\n".join(md)

def clean_placeholders(text: str, company: str) -> str:
    """
    Cleans up any square bracket placeholders (like [Date], [Your Name], [Company Address])
    to make the document look fully professional.
    """
    text = re.sub(r'\[(?:Date|Your Date|Current Date)\]', 'August 5, 2026', text, flags=re.IGNORECASE)
    text = re.sub(r'\[(?:Company Address|Address of Company|Address)\]', 'London, UK', text, flags=re.IGNORECASE)
    text = re.sub(r'\[(?:Hiring Manager / Recruitment Team|Hiring Manager|Recruitment Team)\]', 'Hiring Manager', text, flags=re.IGNORECASE)
    text = re.sub(r'\[(?:Your Name|Candidate Name|Name)\]', 'Muhammad Abdullah Bilal', text, flags=re.IGNORECASE)
    text = re.sub(r'\[(?:Your Address|Candidate Address)\]', 'Faisalabad, Pakistan', text, flags=re.IGNORECASE)
    text = re.sub(r'\[(?:Your Phone Number|Candidate Phone Number|Phone)\]', '+92 340 7437039', text, flags=re.IGNORECASE)
    text = re.sub(r'\[(?:Your Email|Candidate Email|Email)\]', 'muhammadabdullahb52@gmail.com', text, flags=re.IGNORECASE)
    
    def br_repl(match):
        inner = match.group(1).strip()
        if ":" in inner:
            parts = inner.split(":", 1)
            return parts[1].strip()
        return inner
        
    text = re.sub(r'\[([^\]]+)\]', br_repl, text)
    return text

def extract_json_from_text(text: str) -> str:
    start_idx = text.find('{')
    end_idx = text.rfind('}')
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        return text[start_idx:end_idx+1]
    return text

def find_pdf_resume():
    for arg in sys.argv[1:]:
        if arg.endswith(".pdf"):
            return arg
    pdf_files = glob.glob("*.pdf")
    if pdf_files:
        for f in pdf_files:
            if "resume" in f.lower() or "cv" in f.lower():
                return f
        return pdf_files[0]
    return "AI-ML resume.pdf"

def main():
    # If user specifies CLI mode explicitly
    if "--cli" in sys.argv:
        cv_path = find_pdf_resume()
        print("==================================================")
        print(" Automated ATS CV & Cover Letter Generator (Groq) ")
        print("==================================================")
        print(f"Target CV File: {cv_path}")
        
        if not os.path.exists(cv_path):
            print(f"[ERROR] CV file '{cv_path}' not found!")
            return

        cv_text = extract_text_from_pdf(cv_path)
        jobs_file = "linkedin_ai_engineer_jobs.json"
        
        with open(jobs_file, "r", encoding="utf-8") as f:
            jobs = json.load(f)

        # Process a single job for testing CLI
        job = jobs[0]
        title = job.get("title", "Graduate AI Engineer")
        company = job.get("company", "Abound")
        description = job.get("description", "")
        
        print(f"Processing single CLI job: {title} @ {company}...")
        tailored_cv_raw = generate_tailored_cv(cv_text, title, company, description)
        
        clean_json_str = extract_json_from_text(tailored_cv_raw)
        cv_data = json.loads(clean_json_str)
        
        folder_name = f"outputs/{sanitize_filename(company)}_{sanitize_filename(title)}"
        os.makedirs(folder_name, exist_ok=True)
        
        json_to_pdf(cv_data, f"{folder_name}/tailored_cv.pdf")
        print(f"Generated tailored package in {folder_name}/")
    else:
        # Launch Dashboard by default!
        port = int(os.environ.get("PORT", 8000))
        run_server(port)

if __name__ == "__main__":
    main()
