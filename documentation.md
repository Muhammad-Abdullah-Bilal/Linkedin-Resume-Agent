now what we are going to build:
we are going to build a linkedin agent that can work for us and search the specific job roles on linkedin for us and then exact the job info related things that then automatically apply for us

First step:
job search
for this task we will use the browser act platform that can do web search for us and find the job on linkedin for us
go to browseract -> signup -> go to broweract/skill-forge -> there you can see the command and also written copy to agent -> copy that command and paste in antigravity it will automatically do the configurations for us -> then write in antigravity like "search the top 10 ai engineer job roles on linkedin in london and save the info in a file with json format" -> it will automatically search the jobs and then will write in a file


Next step: 
for next step i have written this prompt in antigravity:
i want you to create a python file which send the api call to groq, also create a main.py file which loops over the job details that are present in json file and send the detail along with my cv {first convert pdf to text} to llm and let it decided whether it is a good match or not, in the system prompt ask it to score from 0-10. if it sends back anything above 6 then the main.py file should print the job title. generally also print all the job titles and their scores on the terminal when i run that main.py file

This prompt will analyze out cv and give us the score based on our searched jobs


Next step:
write this prompt in antigravity
For each job posting, create a tailored CV and cover letter optimized for ATS and aligned with the job requirements.
Extract and incorporate relevant keywords, skills, and technologies from the job description where they genuinely match the candidate's existing experience.
Do not invent experience, skills, projects, certifications, or achievements.
Only rephrase, reorganize, and emphasize information already present in the original CV.
Prioritize the most relevant experience, projects, and skills for the target role.
Generate a professional, ATS-friendly CV and a customized cover letter for each job.
Update main.py to automate this process and save all outputs in separate folders:
outputs/<company_name>_<job_title>/
Each folder should contain:
tailored_cv.pdf
tailored_cv.docx
cover_letter.pdf
cover_letter.docx
The goal is to maximize ATS match and relevance while maintaining complete factual accuracy.