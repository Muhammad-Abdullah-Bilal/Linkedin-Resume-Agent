import re

def clean_latin1(text: str) -> str:
    """
    Cleans up unicode characters (en-dashes, em-dashes, smart quotes, bullets)
    and maps them to standard latin1 or safe PDF character equivalents.
    Replaces unicode bullet points with standard byte value 149 (\x95)
    which matches the bullet symbol in PDF Helvetica WinAnsiEncoding.
    """
    if not isinstance(text, str):
        return text
    text = text.replace('\u2013', '-').replace('\u2014', '-')
    text = text.replace('–', '-').replace('—', '-')
    text = text.replace('\u2018', "'").replace('\u2019', "'")
    text = text.replace('\u201c', '"').replace('\u201d', '"')
    text = text.replace('\u2022', '\x95').replace('•', '\x95')
    return text

def sanitize_filename(name: str) -> str:
    clean = re.sub(r'[^\w\s-]', '', name).strip()
    return re.sub(r'[-\s]+', '_', clean)

def strip_candidate_header(text: str) -> str:
    """
    Strips candidate's personal contact details from the start of the body
    to avoid duplication when a letterhead header is already drawn.
    """
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

def text_to_pdf(text: str, filename: str, doc_title: str = "Document"):
    """
    Renders cover letter text into a high-end, premium letterhead layout.
    Filters out encoding issues and fits content elegantly on a single page.
    """
    # 1. Strip candidate details from body text to avoid duplication
    cleaned_letter_text = strip_candidate_header(text)
    raw_lines = cleaned_letter_text.splitlines()
    lines = [clean_latin1(line.strip()) for line in raw_lines]
    
    pages_streams = []
    current_page_cmds = []
    
    margin_top = 740
    margin_bottom = 54
    margin_left = 54
    page_width = 612
    margin_right = 54
    
    current_y = margin_top
    
    def add_page():
        nonlocal current_page_cmds, current_y
        if current_page_cmds:
            pages_streams.append("\n".join(current_page_cmds))
        current_page_cmds = []
        current_y = margin_top
        
    add_page()
    
    def draw_text(text_str: str, x: int, y: int, size: float, bold: bool = False, color: str = "0.15 0.15 0.15"):
        esc = text_str.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
        font = "/F2" if bold else "/F1"
        current_page_cmds.append(f"BT {font} {size} Tf {color} rg {x} {y} Td ({esc}) Tj ET")

    def draw_text_centered(text_str: str, y: int, size: float, bold: bool = False, color: str = "0.4 0.4 0.4"):
        text_w = sum(6.5 if c.isupper() else 4.5 for c in text_str) * (size / 10.0)
        x = int((page_width / 2) - (text_w / 2))
        draw_text(text_str, x, y, size, bold, color)

    def draw_line(y: int):
        current_page_cmds.append(f"0.8 0.8 0.8 RG 0.5 w {margin_left} {y} m {page_width - margin_right} {y} l S")

    # 2. Draw styled centered letterhead header at the top
    name = "Muhammad Abdullah Bilal"
    contact_str = "Faisalabad, Pakistan  |  +92 340 7437039  |  muhammadabdullahb52@gmail.com"
    draw_text_centered(name, current_y, 18, bold=True, color="0.12 0.30 0.47")
    current_y -= 15
    draw_text_centered(contact_str, current_y, 8.5, color="0.4 0.4 0.4")
    current_y -= 10
    draw_line(current_y)
    current_y -= 25
        
    # 3. Process Date, Recipient and Greeting
    body_started = False
    recipient_block = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line:
            i += 1
            continue
            
        if "dear" in line.lower() or len(recipient_block) >= 5:
            body_started = True
            
        if not body_started:
            recipient_block.append(line)
        else:
            if recipient_block:
                for idx, r_line in enumerate(recipient_block):
                    draw_text(r_line, margin_left, current_y, 10, bold=(idx == 0))
                    current_y -= 14
                current_y -= 12
                recipient_block = []
                
            if "sincerely" in line.lower() or "best regards" in line.lower():
                current_y -= 12
                draw_text(line, margin_left, current_y, 9.5, bold=True)
                current_y -= 25
                if i + 1 < len(lines):
                    draw_text(lines[i+1], margin_left, current_y, 9.5, bold=True)
                break
            else:
                words = line.split()
                curr_line = ""
                for w in words:
                    if len(curr_line) + len(w) > 96:
                        draw_text(curr_line.rstrip(), margin_left, current_y, 9.5)
                        current_y -= 13.5
                        if current_y < margin_bottom:
                            add_page()
                        curr_line = w + " "
                    else:
                        curr_line += w + " "
                if curr_line.strip():
                    draw_text(curr_line.rstrip(), margin_left, current_y, 9.5)
                    current_y -= 13.5
                current_y -= 6
                
        i += 1

    if current_page_cmds:
        pages_streams.append("\n".join(current_page_cmds))
        
    num_pages = len(pages_streams)
    objects = []
    
    objects.append("1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj")
    page_refs = " ".join([f"{3 + i*2} 0 R" for i in range(num_pages)])
    objects.append(f"2 0 obj\n<< /Type /Pages /Kids [{page_refs}] /Count {num_pages} >>\nendobj")
    
    font1_obj_num = 3 + num_pages * 2
    font2_obj_num = font1_obj_num + 1
    
    for i in range(num_pages):
        page_obj_num = 3 + i * 2
        stream_obj_num = page_obj_num + 1
        
        footer_cmd = ""
        if num_pages > 1:
            footer_cmd = f"BT /F1 8 Tf 0.5 0.5 0.5 rg 306 20 Td (Page {i+1} of {num_pages}) Tj ET"
            
        stream_content = pages_streams[i] + "\n" + footer_cmd
        
        page_obj = f"{page_obj_num} 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 {font1_obj_num} 0 R /F2 {font2_obj_num} 0 R >> >> /Contents {stream_obj_num} 0 R >>\nendobj"
        stream_obj = f"{stream_obj_num} 0 obj\n<< /Length {len(stream_content)} >>\nstream\n{stream_content}\nendstream\nendobj"
        
        objects.append(page_obj)
        objects.append(stream_obj)
        
    objects.append(f"{font1_obj_num} 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj")
    objects.append(f"{font2_obj_num} 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>\nendobj")
    
    pdf_body = "%PDF-1.4\n"
    offsets = [len(pdf_body)]
    for obj in objects:
        pdf_body += obj + "\n"
        offsets.append(len(pdf_body))
        
    xref_offset = len(pdf_body)
    total_objs = len(objects) + 1
    
    xref = f"xref\n0 {total_objs}\n0000000000 65535 f \n"
    for off in offsets[:-1]:
        xref += f"{off:010d} 00000 n \n"
        
    trailer = f"trailer\n<< /Size {total_objs} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF"
    final_pdf = pdf_body + xref + trailer
    
    with open(filename, "wb") as f:
        f.write(final_pdf.encode('latin1', errors='replace'))

def json_to_pdf(data: dict, filename: str):
    """
    Renders structured CV JSON into a high-end, premium resume layout.
    Resolves encoding errors, aligns contact info centered, and wraps margins correctly.
    """
    pages_streams = []
    current_page_cmds = []
    
    margin_top = 740
    margin_bottom = 45
    margin_left = 54
    page_width = 612
    margin_right = 54
    
    current_y = margin_top
    
    def add_page():
        nonlocal current_page_cmds, current_y
        if current_page_cmds:
            pages_streams.append("\n".join(current_page_cmds))
        current_page_cmds = []
        current_y = margin_top
        
    add_page()
    
    def draw_text(text_str: str, x: int, y: int, size: float, bold: bool = False, color: str = "0.15 0.15 0.15"):
        esc = clean_latin1(text_str).replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
        font = "/F2" if bold else "/F1"
        current_page_cmds.append(f"BT {font} {size} Tf {color} rg {x} {y} Td ({esc}) Tj ET")

    def draw_text_centered(text_str: str, y: int, size: float, bold: bool = False, color: str = "0.4 0.4 0.4"):
        text_w = sum(6.5 if c.isupper() else 4.5 for c in text_str) * (size / 10.0)
        x = int((page_width / 2) - (text_w / 2))
        draw_text(text_str, x, y, size, bold, color)

    def draw_line(y: int):
        current_page_cmds.append(f"0.8 0.8 0.8 RG 0.5 w {margin_left} {y} m {page_width - margin_right} {y} l S")

    # --- Header Block ---
    name = data.get("name", "Muhammad Abdullah Bilal")
    draw_text_centered(name, current_y, 18, bold=True, color="0.12 0.30 0.47")
    current_y -= 15
    
    title = data.get("title", "AI/ML Engineer")
    draw_text_centered(title, current_y, 11, bold=True, color="0.4 0.4 0.4")
    current_y -= 14
    
    contact = data.get("contact", {})
    contact_parts = []
    if contact.get("location"): contact_parts.append(contact["location"])
    if contact.get("phone"): contact_parts.append(contact["phone"])
    if contact.get("email"): contact_parts.append(contact["email"])
    if contact.get("linkedin"): contact_parts.append(contact["linkedin"])
    if contact.get("github"): contact_parts.append(contact["github"])
    
    line1 = "  |  ".join(contact_parts[:3])
    line2 = "  |  ".join(contact_parts[3:])
    
    draw_text_centered(line1, current_y, 8.5)
    current_y -= 11
    if line2:
        draw_text_centered(line2, current_y, 8.5)
        current_y -= 16
    else:
        current_y -= 5
        
    def check_y(needed: int):
        nonlocal current_y
        if current_y < margin_bottom + needed:
            add_page()

    def draw_section_heading(title_str: str):
        nonlocal current_y
        check_y(45)
        current_y -= 10
        draw_text(title_str, margin_left, current_y, 11.5, bold=True, color="0.12 0.30 0.47")
        current_y -= 3
        draw_line(current_y)
        current_y -= 13

    # --- Summary ---
    if data.get("summary"):
        draw_section_heading("Professional Summary")
        summary_text = data["summary"]
        words = summary_text.split()
        curr_line = ""
        for w in words:
            if len(curr_line) + len(w) > 94:
                check_y(15)
                draw_text(curr_line.rstrip(), margin_left, current_y, 9.5)
                current_y -= 13
                curr_line = w + " "
            else:
                curr_line += w + " "
        if curr_line:
            check_y(15)
            draw_text(curr_line.rstrip(), margin_left, current_y, 9.5)
            current_y -= 13

    # --- Skills ---
    if data.get("skills"):
        draw_section_heading("Technical Skills")
        for cat, skill_list in data["skills"].items():
            check_y(15)
            skill_str = ", ".join(skill_list)
            draw_text(f"{cat}:", margin_left, current_y, 9.5, bold=True)
            label_offset = len(cat) * 5.2 + 15
            
            words = skill_str.split()
            curr_line = ""
            is_first_line = True
            for w in words:
                limit = 94 - (int(label_offset / 5) if is_first_line else 0)
                if len(curr_line) + len(w) > limit:
                    check_y(15)
                    x_pos = margin_left + label_offset if is_first_line else margin_left + 15
                    draw_text(curr_line.rstrip(), x_pos, current_y, 9.5)
                    current_y -= 13
                    curr_line = w + " "
                    is_first_line = False
                else:
                    curr_line += w + " "
            if curr_line:
                check_y(15)
                x_pos = margin_left + label_offset if is_first_line else margin_left + 15
                draw_text(curr_line.rstrip(), x_pos, current_y, 9.5)
                current_y -= 13

    # --- Experience ---
    if data.get("experience"):
        draw_section_heading("Professional Experience")
        for exp in data["experience"]:
            check_y(45)
            role = exp.get("role", "")
            comp = exp.get("company", "")
            dur = exp.get("duration", "")
            
            draw_text(f"{role} - {comp}", margin_left, current_y, 10, bold=True)
            draw_text(dur, page_width - margin_right - (len(dur) * 5.2), current_y, 9.5, bold=False, color="0.4 0.4 0.4")
            current_y -= 13
            
            for bullet in exp.get("bullets", []):
                check_y(25)
                words = bullet.split()
                curr_line = "\x95  "
                for w in words:
                    if len(curr_line) + len(w) > 88:
                        draw_text(curr_line.rstrip(), margin_left + 12, current_y, 9.5)
                        current_y -= 13
                        check_y(15)
                        curr_line = "   " + w + " "
                    else:
                        curr_line += w + " "
                if curr_line:
                    draw_text(curr_line.rstrip(), margin_left + 12, current_y, 9.5)
                    current_y -= 13

    # --- Projects ---
    if data.get("projects"):
        draw_section_heading("Key Projects")
        for proj in data["projects"]:
            check_y(40)
            p_name = proj.get("name", "")
            p_bullets = proj.get("bullets", [])
            p_techs = proj.get("technologies", [])
            
            draw_text(p_name, margin_left, current_y, 10, bold=True)
            current_y -= 13
            
            for bullet in p_bullets:
                check_y(25)
                words = bullet.split()
                curr_line = "\x95  "
                for w in words:
                    if len(curr_line) + len(w) > 88:
                        draw_text(curr_line.rstrip(), margin_left + 12, current_y, 9.5)
                        current_y -= 13
                        check_y(15)
                        curr_line = "   " + w + " "
                    else:
                        curr_line += w + " "
                if curr_line:
                    draw_text(curr_line.rstrip(), margin_left + 12, current_y, 9.5)
                    current_y -= 13
            
            if p_techs:
                check_y(15)
                techs_str = ", ".join(p_techs)
                draw_text("Technologies Used:", margin_left + 12, current_y, 9.5, bold=True)
                draw_text(techs_str, margin_left + 105, current_y, 9.5)
                current_y -= 13

    # --- Education ---
    if data.get("education"):
        draw_section_heading("Education")
        for edu in data["education"]:
            check_y(35)
            deg = edu.get("degree", "")
            inst = edu.get("institution", "")
            dur = edu.get("duration", "")
            
            draw_text(f"{deg} - {inst}", margin_left, current_y, 9.5, bold=True)
            draw_text(dur, page_width - margin_right - (len(dur) * 5.2), current_y, 9.5, bold=False, color="0.4 0.4 0.4")
            current_y -= 13

    # --- Certifications ---
    if data.get("certifications"):
        draw_section_heading("Certifications & Achievements")
        for cert in data["certifications"]:
            check_y(15)
            draw_text(f"\x95  {cert}", margin_left + 12, current_y, 9.5)
            current_y -= 13

    # --- Activities ---
    if data.get("activities"):
        draw_section_heading("Activities")
        for act in data["activities"]:
            check_y(35)
            role = act.get("role", "")
            org = act.get("organization", "")
            desc = act.get("description", "")
            
            draw_text(f"{role} - {org}", margin_left, current_y, 9.5, bold=True)
            current_y -= 13
            
            words = desc.split()
            curr_line = ""
            for w in words:
                if len(curr_line) + len(w) > 94:
                    check_y(15)
                    draw_text(curr_line.rstrip(), margin_left, current_y, 9.5)
                    current_y -= 13
                    curr_line = w + " "
                else:
                    curr_line += w + " "
            if curr_line:
                check_y(15)
                draw_text(curr_line.rstrip(), margin_left, current_y, 9.5)
                current_y -= 13

    if current_page_cmds:
        pages_streams.append("\n".join(current_page_cmds))
        
    num_pages = len(pages_streams)
    objects = []
    
    objects.append("1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj")
    page_refs = " ".join([f"{3 + i*2} 0 R" for i in range(num_pages)])
    objects.append(f"2 0 obj\n<< /Type /Pages /Kids [{page_refs}] /Count {num_pages} >>\nendobj")
    
    font1_obj_num = 3 + num_pages * 2
    font2_obj_num = font1_obj_num + 1
    
    for i in range(num_pages):
        page_obj_num = 3 + i * 2
        stream_obj_num = page_obj_num + 1
        
        footer_cmd = f"BT /F1 8 Tf 0.5 0.5 0.5 rg 306 20 Td (Page {i+1} of {num_pages}) Tj ET"
        stream_content = pages_streams[i] + "\n" + footer_cmd
        
        page_obj = f"{page_obj_num} 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 {font1_obj_num} 0 R /F2 {font2_obj_num} 0 R >> >> /Contents {stream_obj_num} 0 R >>\nendobj"
        stream_obj = f"{stream_obj_num} 0 obj\n<< /Length {len(stream_content)} >>\nstream\n{stream_content}\nendstream\nendobj"
        
        objects.append(page_obj)
        objects.append(stream_obj)
        
    objects.append(f"{font1_obj_num} 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj")
    objects.append(f"{font2_obj_num} 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>\nendobj")
    
    pdf_body = "%PDF-1.4\n"
    offsets = [len(pdf_body)]
    for obj in objects:
        pdf_body += obj + "\n"
        offsets.append(len(pdf_body))
        
    xref_offset = len(pdf_body)
    total_objs = len(objects) + 1
    
    xref = f"xref\n0 {total_objs}\n0000000000 65535 f \n"
    for off in offsets[:-1]:
        xref += f"{off:010d} 00000 n \n"
        
    trailer = f"trailer\n<< /Size {total_objs} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF"
    final_pdf = pdf_body + xref + trailer
    
    with open(filename, "wb") as f:
        f.write(final_pdf.encode('latin1', errors='replace'))
