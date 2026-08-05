import zipfile
import html
import re

def json_to_docx(data: dict, filename: str):
    """
    Creates a highly professional CV Word document (.docx) directly from structured JSON data.
    """
    body_xml = []
    
    # Candidate Name (Header)
    name = data.get("name", "Muhammad Abdullah Bilal")
    body_xml.append(f"""
    <w:p>
      <w:pPr>
        <w:jc w:val="left"/>
        <w:spacing w:before="0" w:after="40"/>
      </w:pPr>
      <w:r>
        <w:rPr>
          <w:b/>
          <w:sz w:val="36"/>
          <w:color w:val="1F4E78"/>
          <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
        </w:rPr>
        <w:t>{html.escape(name)}</w:t>
      </w:r>
    </w:p>""")
    
    # Title
    title = data.get("title", "AI/ML Engineer")
    body_xml.append(f"""
    <w:p>
      <w:pPr>
        <w:jc w:val="left"/>
        <w:spacing w:before="0" w:after="80"/>
      </w:pPr>
      <w:r>
        <w:rPr>
          <w:b/>
          <w:sz w:val="22"/>
          <w:color w:val="595959"/>
          <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
        </w:rPr>
        <w:t>{html.escape(title)}</w:t>
      </w:r>
    </w:p>""")
    
    # Contact Details Line
    contact = data.get("contact", {})
    contact_parts = []
    if contact.get("location"): contact_parts.append(contact["location"])
    if contact.get("phone"): contact_parts.append(contact["phone"])
    if contact.get("email"): contact_parts.append(contact["email"])
    if contact.get("linkedin"): contact_parts.append(f"LinkedIn: {contact['linkedin']}")
    if contact.get("github"): contact_parts.append(f"GitHub: {contact['github']}")
    
    contact_str = "  |  ".join(contact_parts)
    body_xml.append(f"""
    <w:p>
      <w:pPr>
        <w:jc w:val="left"/>
        <w:spacing w:before="0" w:after="240"/>
      </w:pPr>
      <w:r>
        <w:rPr>
          <w:sz w:val="18"/>
          <w:color w:val="595959"/>
          <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
        </w:rPr>
        <w:t>{html.escape(contact_str)}</w:t>
      </w:r>
    </w:p>""")
    
    def add_section_heading(heading_text: str):
        body_xml.append(f"""
        <w:p>
          <w:pPr>
            <w:spacing w:before="240" w:after="80"/>
            <w:pBdr>
              <w:bottom w:val="single" w:sz="6" w:space="4" w:color="1F4E78"/>
            </w:pBdr>
          </w:pPr>
          <w:r>
            <w:rPr>
              <w:b/>
              <w:sz w:val="24"/>
              <w:color w:val="1F4E78"/>
              <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
            </w:rPr>
            <w:t>{html.escape(heading_text)}</w:t>
          </w:r>
        </w:p>""")

    # --- Summary ---
    if data.get("summary"):
        add_section_heading("Professional Summary")
        body_xml.append(f"""
        <w:p>
          <w:pPr>
            <w:spacing w:before="40" w:after="120" w:line="240" w:lineRule="auto"/>
          </w:pPr>
          <w:r>
            <w:rPr>
              <w:sz w:val="20"/>
              <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
            </w:rPr>
            <w:t>{html.escape(data["summary"])}</w:t>
          </w:r>
        </w:p>""")
        
    # --- Skills ---
    if data.get("skills"):
        add_section_heading("Technical Skills")
        for cat, items in data["skills"].items():
            skill_str = ", ".join(items)
            body_xml.append(f"""
            <w:p>
              <w:pPr>
                <w:spacing w:before="40" w:after="60"/>
              </w:pPr>
              <w:r>
                <w:rPr>
                  <w:b/>
                  <w:sz w:val="20"/>
                  <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
                </w:rPr>
                <w:t>{html.escape(cat)}: </w:t>
              </w:r>
              <w:r>
                <w:rPr>
                  <w:sz w:val="20"/>
                  <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
                </w:rPr>
                <w:t>{html.escape(skill_str)}</w:t>
              </w:r>
            </w:p>""")
            
    # --- Experience ---
    if data.get("experience"):
        add_section_heading("Professional Experience")
        for exp in data["experience"]:
            role = exp.get("role", "")
            comp = exp.get("company", "")
            dur = exp.get("duration", "")
            body_xml.append(f"""
            <w:p>
              <w:pPr>
                <w:spacing w:before="120" w:after="40"/>
              </w:pPr>
              <w:r>
                <w:rPr>
                  <w:b/>
                  <w:sz w:val="21"/>
                  <w:color w:val="262626"/>
                  <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
                </w:rPr>
                <w:t>{html.escape(role)} – {html.escape(comp)}</w:t>
              </w:r>
              <w:r>
                <w:rPr>
                  <w:sz w:val="20"/>
                  <w:color w:val="595959"/>
                  <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
                </w:rPr>
                <w:tab/>
                <w:t>{html.escape(dur)}</w:t>
              </w:r>
            </w:p>""")
            
            for bullet in exp.get("bullets", []):
                body_xml.append(f"""
                <w:p>
                  <w:pPr>
                    <w:ind w:left="360"/>
                    <w:spacing w:before="20" w:after="20"/>
                  </w:pPr>
                  <w:r>
                    <w:rPr>
                      <w:sz w:val="20"/>
                      <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
                    </w:rPr>
                    <w:t>•  {html.escape(bullet)}</w:t>
                  </w:r>
                </w:p>""")

    # --- Projects ---
    if data.get("projects"):
        add_section_heading("Key Projects")
        for proj in data["projects"]:
            p_name = proj.get("name", "")
            p_bullets = proj.get("bullets", [])
            p_techs = proj.get("technologies", [])
            body_xml.append(f"""
            <w:p>
              <w:pPr>
                <w:spacing w:before="120" w:after="40"/>
              </w:pPr>
              <w:r>
                <w:rPr>
                  <w:b/>
                  <w:sz w:val="21"/>
                  <w:color w:val="262626"/>
                  <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
                </w:rPr>
                <w:t>{html.escape(p_name)}</w:t>
              </w:r>
            </w:p>""")
            
            for bullet in p_bullets:
                body_xml.append(f"""
                <w:p>
                  <w:pPr>
                    <w:ind w:left="360"/>
                    <w:spacing w:before="20" w:after="20"/>
                  </w:pPr>
                  <w:r>
                    <w:rPr>
                      <w:sz w:val="20"/>
                      <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
                    </w:rPr>
                    <w:t>•  {html.escape(bullet)}</w:t>
                  </w:r>
                </w:p>""")
                
            if p_techs:
                techs_str = ", ".join(p_techs)
                body_xml.append(f"""
                <w:p>
                  <w:pPr>
                    <w:ind w:left="360"/>
                    <w:spacing w:before="40" w:after="80"/>
                  </w:pPr>
                  <w:r>
                    <w:rPr>
                      <w:b/>
                      <w:sz w:val="20"/>
                      <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
                    </w:rPr>
                    <w:t>Technologies Used: </w:t>
                  </w:r>
                  <w:r>
                    <w:rPr>
                      <w:sz w:val="20"/>
                      <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
                    </w:rPr>
                    <w:t>{html.escape(techs_str)}</w:t>
                  </w:r>
                </w:p>""")

    # --- Education ---
    if data.get("education"):
        add_section_heading("Education")
        for edu in data["education"]:
            deg = edu.get("degree", "")
            inst = edu.get("institution", "")
            dur = edu.get("duration", "")
            body_xml.append(f"""
            <w:p>
              <w:pPr>
                <w:spacing w:before="100" w:after="60"/>
              </w:pPr>
              <w:r>
                <w:rPr>
                  <w:b/>
                  <w:sz w:val="20"/>
                  <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
                </w:rPr>
                <w:t>{html.escape(deg)} – {html.escape(inst)}</w:t>
              </w:r>
              <w:r>
                <w:rPr>
                  <w:sz w:val="20"/>
                  <w:color w:val="595959"/>
                  <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
                </w:rPr>
                <w:tab/>
                <w:t>{html.escape(dur)}</w:t>
              </w:r>
            </w:p>""")

    # --- Certifications ---
    if data.get("certifications"):
        add_section_heading("Certifications & Achievements")
        for cert in data["certifications"]:
            body_xml.append(f"""
            <w:p>
              <w:pPr>
                <w:ind w:left="360"/>
                <w:spacing w:before="30" w:after="30"/>
              </w:pPr>
              <w:r>
                <w:rPr>
                  <w:sz w:val="20"/>
                  <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
                </w:rPr>
                <w:t>•  {html.escape(cert)}</w:t>
              </w:r>
            </w:p>""")

    # --- Activities ---
    if data.get("activities"):
        add_section_heading("Activities")
        for act in data["activities"]:
            role = act.get("role", "")
            org = act.get("organization", "")
            desc = act.get("description", "")
            body_xml.append(f"""
            <w:p>
              <w:pPr>
                <w:spacing w:before="100" w:after="40"/>
              </w:pPr>
              <w:r>
                <w:rPr>
                  <w:b/>
                  <w:sz w:val="20"/>
                  <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
                </w:rPr>
                <w:t>{html.escape(role)} – {html.escape(org)}</w:t>
              </w:r>
            </w:p>
            <w:p>
              <w:pPr>
                <w:spacing w:before="0" w:after="80"/>
              </w:pPr>
              <w:r>
                <w:rPr>
                  <w:sz w:val="20"/>
                  <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
                </w:rPr>
                <w:t>{html.escape(desc)}</w:t>
              </w:r>
            </w:p>""")

    document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    {"".join(body_xml)}
    <w:sectPr>
      <w:pgSz w:w="12240" w:h="15840"/>
      <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/>
    </w:sectPr>
  </w:body>
</w:document>"""

    content_types_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""

    rels_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

    with zipfile.ZipFile(filename, 'w', zipfile.ZIP_DEFLATED) as docx:
        docx.writestr('[Content_Types].xml', content_types_xml)
        docx.writestr('_rels/.rels', rels_xml)
        docx.writestr('word/document.xml', document_xml)

def text_to_docx(text: str, filename: str, doc_title: str = ""):
    """
    Standard text to docx converter (useful for cover letters).
    """
    lines = text.splitlines()
    body_xml = []
    
    for line in lines:
        s = line.strip()
        if not s:
            body_xml.append('<w:p><w:pPr><w:spacing w:before="0" w:after="80"/></w:pPr></w:p>')
            continue
            
        body_xml.append(f"""
        <w:p>
          <w:pPr>
            <w:spacing w:before="40" w:after="80" w:line="240" w:lineRule="auto"/>
          </w:pPr>
          <w:r>
            <w:rPr>
              <w:sz w:val="21"/>
              <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
            </w:rPr>
            <w:t>{html.escape(s)}</w:t>
          </w:r>
        </w:p>""")
        
    document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    {"".join(body_xml)}
    <w:sectPr>
      <w:pgSz w:w="12240" w:h="15840"/>
      <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/>
    </w:sectPr>
  </w:body>
</w:document>"""

    content_types_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""

    rels_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

    with zipfile.ZipFile(filename, 'w', zipfile.ZIP_DEFLATED) as docx:
        docx.writestr('[Content_Types].xml', content_types_xml)
        docx.writestr('_rels/.rels', rels_xml)
        docx.writestr('word/document.xml', document_xml)
