import os
import json
import re
import time
from groq import Groq

def load_dotenv():
    env_file = ".env"
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip("'").strip('"')
                    normalized_key = key.upper().replace("-", "_")
                    if normalized_key == "GROQ_API_KEY" or "GROQ" in normalized_key:
                        os.environ["GROQ_API_KEY"] = val
                    else:
                        os.environ[key] = val

def get_groq_client():
    load_dotenv()
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("Warning: GROQ_API_KEY environment variable is not set in environment or .env file.")
    return Groq(api_key=api_key) if api_key else Groq()

def chat_with_fallback(messages: list, primary_model: str = "llama-3.3-70b-versatile", temperature: float = 0.2, max_tokens: int = 1500):
    client = get_groq_client()
    models_to_try = [primary_model, "llama-3.1-8b-instant", "mixtral-8x7b-32768"]
    
    for model in models_to_try:
        try:
            response = client.chat.completions.create(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            err_msg = str(e)
            if "429" in err_msg or "rate_limit" in err_msg.lower():
                print(f"  [Notice] Model '{model}' rate limited. Trying fallback model...")
                time.sleep(1)
                continue
            else:
                raise e
    raise RuntimeError("All Groq models failed or rate limited.")

def evaluate_job_match(cv_text: str, job_title: str, company: str, job_description: str) -> dict:
    system_prompt = (
        "You are an expert AI & Tech Talent Recruiter. Your task is to evaluate how well a candidate's CV "
        "matches a given job description.\n"
        "Score the candidate's match strictly from 0 to 10 (0 = completely unsuitable, 10 = perfect match).\n"
        "Return ONLY a valid JSON object with the following keys:\n"
        "{\n"
        '  "score": <number between 0 and 10>,\n'
        '  "reasoning": "<1-2 sentence explanation of the score>"\n'
        "}\n"
        "Do not include any Markdown wrap or additional conversational text outside the JSON."
    )
    
    user_prompt = (
        f"--- CANDIDATE CV ---\n{cv_text[:3000]}\n\n"
        f"--- JOB DETAILS ---\n"
        f"Job Title: {job_title}\n"
        f"Company: {company}\n"
        f"Description:\n{job_description[:3000]}\n"
    )
    
    try:
        content = chat_with_fallback(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            max_tokens=300
        )
        
        clean_content = re.sub(r'^```(?:json)?\s*', '', content, flags=re.IGNORECASE)
        clean_content = re.sub(r'\s*```$', '', clean_content)
        
        data = json.loads(clean_content)
        score = float(data.get("score", 0.0))
        reasoning = data.get("reasoning", "No reasoning provided.")
        return {"score": score, "reasoning": reasoning}
    except Exception as e:
        print(f"  [API Error] Failed to evaluate job '{job_title}': {e}")
        return {"score": 0.0, "reasoning": f"Error during Groq API evaluation: {e}"}

def generate_tailored_cv(cv_text: str, job_title: str, company: str, job_description: str) -> str:
    system_prompt = (
        "You are a Senior Executive Resume Writer, ATS Resume Consultant, and Technical Recruiter with 15+ years of experience helping candidates get interviews at Google, Microsoft, OpenAI, Amazon, Meta, NVIDIA, Tesla and top AI startups.\n\n"
        "Your task is to rewrite and optimize the candidate's CV for a specific job description while maintaining 100% factual accuracy.\n\n"
        "=========================\n"
        "PRIMARY OBJECTIVE\n"
        "=========================\n"
        "Create an ATS-optimized resume that maximizes keyword matching while remaining truthful.\n"
        "The final resume should look like it was written by a professional resume writer.\n"
        "It should be concise, achievement-focused, highly readable, and optimized for Applicant Tracking Systems (ATS).\n\n"
        "=========================\n"
        "STRICT RULES\n"
        "=========================\n"
        "1. NEVER invent anything. Do NOT create Skills, Experience, Projects, Responsibilities, Companies, Dates, Degrees, Certifications, Awards, Metrics unless they already exist in the original CV.\n"
        "2. You MAY: Rewrite sentences, Improve wording, Improve grammar, Improve clarity, Reorder sections, Prioritize relevant projects, Prioritize relevant skills, Emphasize relevant experience, Use keywords from the job description ONLY IF they truthfully apply to existing experience.\n"
        "3. ATS OPTIMIZATION: Carefully analyze the Job Description. Extract important technical skills, frameworks, programming languages, AI technologies, soft skills, responsibilities, qualifications. Then naturally integrate those keywords throughout the resume wherever supported by the original CV. Do NOT keyword stuff. The resume should sound natural.\n"
        "4. PROFESSIONAL SUMMARY: Write a strong 3-4 line executive summary. It should include years/level of experience, strongest technical expertise, biggest strengths, industries, career objective, job title alignment. Use strong action language. Avoid clichés.\n"
        "5. EXPERIENCE: Rewrite every bullet using professional accomplishment-oriented language. Start every bullet with a strong action verb (e.g. Developed, Designed, Built, Optimized, Implemented, Engineered, Integrated, Automated, Evaluated, Collaborated, Improved). Each bullet should be concise, impactful, ATS-friendly, technically strong. Never repeat the same sentence structure.\n"
        "6. PROJECTS: Projects are one of the most important sections. Each project should contain Project Name, 2-4 professional bullet points, Technologies Used. Only use technologies that actually exist. Emphasize AI, ML, LLMs, APIs, Agents, Automation, RAG, NLP, Computer Vision when supported by the original project.\n"
        "7. SKILLS: Categorize skills professionally. Example categories: Programming Languages, AI / Machine Learning, Generative AI, Frameworks & Tools, Developer Tools.\n"
        "8. ORDER OF SECTIONS: Name, Professional Title, Contact, Professional Summary, Technical Skills, Professional Experience, Projects, Education, Certifications, Leadership & Activities.\n"
        "9. WRITING STYLE: Professional, Executive, Concise, Technical, Modern, ATS Friendly. No emojis, no tables, no graphics, no icons, no decorative characters.\n"
        "10. OUTPUT FORMAT: Return ONLY valid JSON matching the exact schema below. No markdown, no explanations, no comments, no ```json blocks.\n\n"
        "JSON Schema:\n"
        "{\n"
        "  \"name\": \"Muhammad Abdullah Bilal\",\n"
        "  \"title\": \"Candidate's professional title, tailored for the target role (e.g. AI Engineer or ML Engineer)\",\n"
        "  \"contact\": {\n"
        "    \"email\": \"muhammadabdullahb52@gmail.com\",\n"
        "    \"phone\": \"+92 340 7437039\",\n"
        "    \"location\": \"Faisalabad, Pakistan\",\n"
        "    \"linkedin\": \"linkedin.com/in/abdullah-bilal\",\n"
        "    \"github\": \"github.com/muhammadabdullahb52\"\n"
        "  },\n"
        "  \"summary\": \"A strong 3-4 line executive summary tailored to the target role, highlighting relevant skills and experience from the CV.\",\n"
        "  \"skills\": {\n"
        "    \"Programming Languages\": [\"Python\", \"C++\"],\n"
        "    \"AI / Machine Learning\": [\"Machine Learning\", \"Deep Learning\"],\n"
        "    \"Generative AI\": [\"LLMs\", \"RAG\"],\n"
        "    \"Frameworks & Tools\": [\"PyTorch\", \"Git\"]\n"
        "  },\n"
        "  \"experience\": [\n"
        "    {\n"
        "      \"role\": \"Machine Learning Intern\",\n"
        "      \"company\": \"DevelopersHub Corporation\",\n"
        "      \"duration\": \"Internship Duration\",\n"
        "      \"bullets\": [\n"
        "        \"Tailored bullet point based ONLY on candidate's original CV, rephrasing to align with job keywords.\",\n"
        "        \"Second tailored bullet point based ONLY on original CV.\"\n"
        "      ]\n"
        "    }\n"
        "  ],\n"
        "  \"projects\": [\n"
        "    {\n"
        "      \"name\": \"Project Name\",\n"
        "      \"bullets\": [\n"
        "        \"Project bullet description optimized for keywords based strictly on original CV.\",\n"
        "        \"Second bullet point representing candidate achievements.\"\n"
        "      ],\n"
        "      \"technologies\": [\"Python\", \"PyTorch\"]\n"
        "    }\n"
        "  ],\n"
        "  \"education\": [\n"
        "    {\n"
        "      \"degree\": \"BS Computer Science\",\n"
        "      \"institution\": \"University of Agriculture Faisalabad\",\n"
        "      \"duration\": \"2023 - 2027\"\n"
        "    }\n"
        "  ],\n"
        "  \"certifications\": [\n"
        "    \"AI & Data Science Training — SMIT\",\n"
        "    \"Stanford Code in Place (Python)\"\n"
        "  ],\n"
        "  \"activities\": [\n"
        "    {\n"
        "      \"role\": \"Volunteer Trainer\",\n"
        "      \"organization\": \"Agriversity Scouts Group, UAF\",\n"
        "      \"description\": \"Taught Emerging Technologies course module based strictly on original CV facts.\"\n"
        "    }\n"
        "  ]\n"
        "}"
    )
    
    user_prompt = (
        f"Candidate CV:\n{cv_text[:3000]}\n\n"
        f"Target Role: {job_title} at {company}\n\n"
        f"Job Description Keywords & Requirements:\n{job_description[:2500]}\n"
    )
    
    try:
        return chat_with_fallback(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=1500
        )
    except Exception as e:
        print(f"  [API Error] Failed to generate CV for '{job_title}': {e}")
        return "{}"

def generate_cover_letter(cv_text: str, job_title: str, company: str, job_description: str) -> str:
    system_prompt = f"""
You are an Executive Career Coach and Professional Resume Writer.

Write a compelling, personalized cover letter for the position of {job_title} at {company}.

=========================
GOAL
=========================

Write a modern cover letter that sounds natural, confident, and professional.

The cover letter should persuade the recruiter to invite the candidate for an interview.

=========================
STRICT RULES
=========================

1. Never invent experience.

2. Never invent achievements.

3. Never invent metrics.

4. Only use information from the original CV.

5. Mention the company naturally.

6. Mention why the candidate is interested in this company.

7. Show enthusiasm without sounding desperate.

8. Highlight the strongest matching experiences.

9. Use keywords from the job description naturally.

10. Keep the letter around 350-450 words.

=========================
STRUCTURE
=========================

Muhammad Abdullah Bilal

Faisalabad, Pakistan

+92 340 7437039

muhammadabdullahb52@gmail.com

August 5, 2026

Hiring Manager

{company}

Dear Hiring Manager,

Paragraph 1
• Introduce yourself
• Mention the role
• Express enthusiasm

Paragraph 2
• Highlight most relevant experience
• Mention technologies
• Explain why you're a good fit

Paragraph 3
• Highlight projects
• Connect them to company needs

Paragraph 4
• Closing statement
• Thank recruiter
• Invite discussion

Sincerely,

Muhammad Abdullah Bilal

Return only the cover letter.
"""
    
    user_prompt = (
        f"Candidate CV:\n{cv_text[:3000]}\n\n"
        f"Target Role: {job_title} at {company}\n\n"
        f"Job Description:\n{job_description[:2000]}\n"
    )
    
    try:
        return chat_with_fallback(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.4,
            max_tokens=1000
        )
    except Exception as e:
        print(f"  [API Error] Failed to generate Cover Letter for '{job_title}': {e}")
        return f"Cover Letter for {job_title} at {company}"
