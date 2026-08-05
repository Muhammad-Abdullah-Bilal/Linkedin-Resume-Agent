import urllib.request
import re
import html
import json
import time
from datetime import datetime, timedelta

def clean_html(raw_html):
    if not raw_html:
        return ""
    text = re.sub(r'<br\s*/?>', '\n', raw_html, flags=re.IGNORECASE)
    text = re.sub(r'</p>', '\n\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</li>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)
    text = html.unescape(text)
    lines = [line.strip() for line in text.splitlines()]
    return '\n'.join(line for line in lines if line)

def is_within_three_weeks(posted_text):
    posted_text = posted_text.lower().strip()
    if not posted_text or posted_text == "n/a":
        return False
    
    if "minute" in posted_text or "hour" in posted_text or "day" in posted_text:
        # "4 days ago", "1 day ago", "21 days ago"
        match = re.search(r'(\d+)\s+day', posted_text)
        if match:
            days = int(match.group(1))
            return days <= 21
        return True # "today", "hours ago"
        
    if "week" in posted_text:
        # "1 week ago", "2 weeks ago", "3 weeks ago"
        match = re.search(r'(\d+)\s+week', posted_text)
        if match:
            weeks = int(match.group(1))
            return weeks <= 3
        return True # "1 week ago"
        
    return False # "month", "year", > 3 weeks

def fetch_recent_jobs(keywords="AI Engineer", location="London", target_count=10):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    
    recent_jobs = []
    seen_ids = set()
    start = 0
    
    while len(recent_jobs) < target_count and start < 100:
        url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={urllib.parse.quote(keywords)}&location={urllib.parse.quote(location)}&start={start}"
        print(f"Fetching search page start={start}...")
        req = urllib.request.Request(url, headers=headers)
        
        try:
            with urllib.request.urlopen(req) as resp:
                html_content = resp.read().decode('utf-8')
        except Exception as e:
            print(f"Error fetching search page at start={start}: {e}")
            break
            
        job_ids = re.findall(r'jobPosting:(\d+)', html_content)
        if not job_ids:
            job_ids = re.findall(r'view/[^/]+-(\d+)', html_content)
            
        if not job_ids:
            print("No more job IDs found on page.")
            break
            
        for job_id in job_ids:
            if job_id in seen_ids:
                continue
            seen_ids.add(job_id)
            
            detail_url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
            req = urllib.request.Request(detail_url, headers=headers)
            
            try:
                with urllib.request.urlopen(req) as resp:
                    detail_html = resp.read().decode('utf-8')
                
                # Extract posted time
                posted_match = re.search(r'<span class="posted-time-ago__text[^"]*">\s*(.*?)\s*</span>', detail_html, re.DOTALL)
                posted_time = clean_html(posted_match.group(1)) if posted_match else "N/A"
                
                if not is_within_three_weeks(posted_time):
                    print(f"Skipping job {job_id}: posted '{posted_time}' (exceeds 3 weeks)")
                    continue
                
                # Extract title
                title_match = re.search(r'<h2 class="top-card-layout__title[^"]*">(.*?)</h2>', detail_html, re.DOTALL)
                title = clean_html(title_match.group(1)) if title_match else "N/A"
                
                # Extract company
                company_match = re.search(r'<a class="topcard__org-name-link[^"]*"[^>]*>(.*?)</a>', detail_html, re.DOTALL)
                if not company_match:
                    company_match = re.search(r'alt="([^"]+)"', detail_html)
                company = clean_html(company_match.group(1)) if company_match else "N/A"
                
                # Extract location
                loc_match = re.search(r'<span class="topcard__flavor topcard__flavor--bullet">\s*(.*?)\s*</span>', detail_html, re.DOTALL)
                location_str = clean_html(loc_match.group(1)) if loc_match else location
                
                # Extract job description
                desc_match = re.search(r'<div class="show-more-less-html__markup[^"]*">(.*?)</div>', detail_html, re.DOTALL)
                if not desc_match:
                    desc_match = re.search(r'<section class="core-section-container[^"]*">(.*?)</section>', detail_html, re.DOTALL)
                
                description = clean_html(desc_match.group(1)) if desc_match else "N/A"
                job_url = f"https://www.linkedin.com/jobs/view/{job_id}"
                
                job_data = {
                    "job_id": job_id,
                    "title": title,
                    "company": company,
                    "location": location_str,
                    "posted_time": posted_time,
                    "url": job_url,
                    "description": description
                }
                
                recent_jobs.append(job_data)
                print(f"[{len(recent_jobs)}/{target_count}] Added job '{title}' at '{company}' (posted {posted_time})")
                
                if len(recent_jobs) >= target_count:
                    break
                time.sleep(0.3)
            except Exception as e:
                print(f"Error fetching detail for job {job_id}: {e}")
                
        start += 25
        
    return recent_jobs

if __name__ == "__main__":
    jobs = fetch_recent_jobs("AI Engineer", "London", 10)
    output_filename = "linkedin_ai_engineer_jobs.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)
    print(f"Successfully saved {len(jobs)} recent jobs (<= 3 weeks) to {output_filename}")
