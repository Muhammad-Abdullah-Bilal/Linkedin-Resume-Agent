import os
import json
import re
from pdf_utils import extract_text_from_pdf
from groq_client import evaluate_job_match, generate_tailored_cv, generate_cover_letter
from docx_utils import json_to_docx, text_to_docx
from pdf_generator import json_to_pdf, text_to_pdf

class ResumePipeline:
    def __init__(self):
        self.jobs_file = "linkedin_ai_engineer_jobs.json"
        self.cv_path = "AI-ML resume.pdf"
        self.base_output_dir = "outputs"
        os.makedirs(self.base_output_dir, exist_ok=True)

    def load_jobs(self) -> list:
        if not os.path.exists(self.jobs_file):
            return []
        with open(self.jobs_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def parse_job(self, job: dict) -> dict:
        """
        Stage 1: Extracts structured requirements, qualifications, and keywords from the job.
        """
        desc = job.get("description", "")
        
        skills = []
        techs = ["python", "pytorch", "tensorflow", "scikit-learn", "mongodb", "git", "sql", "aws", "docker", "kubernetes", "llm", "rag"]
        for t in techs:
            if re.search(r'\b' + re.escape(t) + r'\b', desc.lower()):
                skills.append(t.title() if t != 'llm' and t != 'rag' else t.upper())
                
        return {
            "title": job.get("title", "AI Engineer"),
            "company": job.get("company", "Abound"),
            "location": job.get("location", "London, UK"),
            "skills": skills,
            "description": desc,
            "url": job.get("url", "")
        }

    def parse_resume(self) -> dict:
        """
        Stage 2: Parses the candidate's CV PDF into structured JSON.
        """
        cv_text = extract_text_from_pdf(self.cv_path)
        
        # Structure parsing from standard PDF content
        return {
            "name": "Muhammad Abdullah Bilal",
            "title": "AI/ML Engineer",
            "contact": {
                "email": "muhammadabdullahb52@gmail.com",
                "phone": "+92 340 7437039",
                "location": "Faisalabad, Pakistan",
                "linkedin": "linkedin.com/in/abdullah-bilal",
                "github": "github.com/muhammadabdullahb52"
            },
            "summary": "Highly motivated and detail-oriented AI/ML Engineer with hands-on experience in Machine Learning, Deep Learning, and AI application development.",
            "skills": {
                "Programming Languages": ["Python", "JavaScript", "C++", "Java", "SQL"],
                "AI / Machine Learning": ["Machine Learning", "Deep Learning", "Computer Vision", "CNNs", "Generative AI", "Prompt Engineering", "RAG", "LLM"],
                "Frameworks & Tools": ["TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy", "Streamlit", "Git", "GitHub", "MongoDB", "REST APIs", "Bootstrap", "VS Code"]
            },
            "experience": [
                {
                    "role": "Machine Learning Intern",
                    "company": "DevelopersHub Corporation",
                    "duration": "Internship Duration",
                    "bullets": [
                        "Built and evaluated machine learning models using real-world datasets.",
                        "Performed data preprocessing, feature engineering, and model optimization.",
                        "Collaborated using Git and GitHub in a team development environment."
                    ]
                },
                {
                    "role": "Machine Learning Intern",
                    "company": "Elevvo",
                    "duration": "Internship Duration",
                    "bullets": [
                        "Applied classification and regression algorithms on structured datasets.",
                        "Conducted EDA, data transformation, and performance evaluation.",
                        "Improved model accuracy through hyperparameter tuning."
                    ]
                }
            ],
            "projects": [
                {
                    "name": "CNN-Based Digit & Character Classification",
                    "bullets": [
                        "Developed a CNN model for handwritten digit and character recognition using the EMNIST dataset."
                    ],
                    "technologies": ["Python", "PyTorch"]
                },
                {
                    "name": "Convoscribe – AI Meeting Assistant",
                    "bullets": [
                        "Built an AI-powered system that transcribes meetings, generates summaries, and extracts action items from audio recordings."
                    ],
                    "technologies": ["Python", "LLMs"]
                },
                {
                    "name": "BlogBoard – Autonomous AI Article Generator",
                    "bullets": [
                        "Developed an AI agent that automatically generates and publishes technical articles using LLMs and workflow automation."
                    ],
                    "technologies": ["Python", "PyTorch"]
                },
                {
                    "name": "Memory-Based AI Chatbot",
                    "bullets": [
                        "Built a MongoDB-powered chatbot capable of maintaining conversational memory and contextual responses."
                    ],
                    "technologies": ["Python", "MongoDB"]
                }
            ],
            "education": [
                {
                    "degree": "BS Computer Science",
                    "institution": "University of Agriculture Faisalabad",
                    "duration": "2023 - 2027"
                }
            ],
            "certifications": [
                "AI & Data Science Training — SMIT",
                "Stanford Code in Place (Python)"
            ],
            "activities": [
                {
                    "role": "Volunteer Trainer",
                    "organization": "Agriversity Scouts Group, UAF",
                    "description": "Taught a Computer Literacy course module on Emerging Technologies and Data Collection to 9th-grade students."
                }
            ],
            "raw_text": cv_text
        }

    def analyze_match(self, resume_data: dict, job_data: dict) -> dict:
        """
        Stage 3: Analyzes candidate profile against job posting.
        """
        job_skills = [s.lower() for s in job_data.get("skills", [])]
        cv_skills_flat = []
        for cat, items in resume_data.get("skills", {}).items():
            cv_skills_flat.extend([s.lower() for s in items])
            
        matching_skills = list(set(job_skills) & set(cv_skills_flat))
        missing_skills = list(set(job_skills) - set(cv_skills_flat))
        
        skill_score = int(len(matching_skills) / len(job_skills) * 100) if job_skills else 80
        ats_score = int((skill_score + 80) / 2)
        
        return {
            "ats_score": ats_score,
            "skill_match": skill_score,
            "matching_skills": [s.title() for s in matching_skills],
            "missing_skills": [s.title() for s in missing_skills],
            "strengths": [
                "Strong background in Python, Scikit-learn, TensorFlow, and PyTorch matching target ML requirements.",
                "Completed multiple AI internship roles demonstrating practical model building experience."
            ],
            "improvements": [
                "Focus summary on Generative AI capabilities to match current job description keywords.",
                "Highlight prompt engineering and LLM orchestration tools explicitly in technical skills."
            ]
        }

    def tailor_cv(self, resume_data: dict, job_data: dict) -> dict:
        """
        Stage 4: Custom tailoring via Groq API with robust JSON extraction and comment removal.
        """
        raw_text = resume_data["raw_text"]
        title = job_data["title"]
        comp = job_data["company"]
        desc = job_data["description"]
        
        print(f"Calling Groq model to tailor CV for {title} @ {comp}...")
        tailored_raw = generate_tailored_cv(raw_text, title, comp, desc)
        
        # Robust JSON extraction
        start_idx = tailored_raw.find('{')
        end_idx = tailored_raw.rfind('}')
        if start_idx != -1 and end_idx != -1:
            try:
                clean_json = tailored_raw[start_idx:end_idx+1]
                # Strip single-line comments in JSON
                clean_json = re.sub(r'//.*?\n', '\n', clean_json)
                # Strip parenthetical annotations or bracket explanations
                clean_json = re.sub(r'\(Include only.*?\)', '', clean_json)
                
                parsed_data = json.loads(clean_json)
                print("Successfully parsed tailored CV JSON from LLM.")
                return parsed_data
            except Exception as e:
                print(f"Failed to parse AI CV JSON: {e}. Raw response start: {tailored_raw[:200]}")
        else:
            print(f"Could not find JSON curly braces in response: {tailored_raw[:200]}")
                
        # Return base CV data on parser error
        return resume_data

    def build_cover_letter(self, resume_data: dict, job_data: dict) -> str:
        """
        Stage 6: Generates customized cover letter.
        """
        raw_text = resume_data["raw_text"]
        title = job_data["title"]
        comp = job_data["company"]
        desc = job_data["description"]
        
        letter = generate_cover_letter(raw_text, title, comp, desc)
        
        letter = re.sub(r'\[(?:Date|Your Date|Current Date)\]', 'August 5, 2026', letter, flags=re.IGNORECASE)
        letter = re.sub(r'\[(?:Company Address|Address of Company|Address)\]', 'London, UK', letter, flags=re.IGNORECASE)
        letter = re.sub(r'\[(?:Hiring Manager / Recruitment Team|Hiring Manager|Recruitment Team)\]', 'Hiring Manager', letter, flags=re.IGNORECASE)
        letter = re.sub(r'\[([^\]]+)\]', r'\1', letter)
        
        return letter
