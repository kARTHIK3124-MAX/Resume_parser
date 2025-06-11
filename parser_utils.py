import spacy
import re
import docx2txt
from pdfminer.high_level import extract_text
import tempfile

# ✅ Lazy-load spaCy model
def get_nlp():
    try:
        return spacy.load("en_core_web_sm")
    except OSError:
        import os
        os.system("python -m spacy download en_core_web_sm")
        return spacy.load("en_core_web_sm")

# -----------------------------------------------
def extract_text_from_file(file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=file.name.split('.')[-1]) as tmp:
        tmp.write(file.read())
        tmp_path = tmp.name

    if file.name.endswith('.pdf'):
        return extract_text(tmp_path), tmp_path
    elif file.name.endswith('.docx'):
        return docx2txt.process(tmp_path), tmp_path
    else:
        return "", ""

# -----------------------------------------------
def extract_email(text):
    match = re.search(r'\b[\w\.-]+@[\w\.-]+\.\w+\b', text)
    return match.group(0) if match else "N/A"

def extract_phone(text):
    match = re.search(r'\b[6-9]\d{9}\b', text)
    return match.group(0) if match else "N/A"

def extract_dob(text):
    match = re.search(r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b', text)
    return f"{match.group(1)}-{match.group(2)}-{match.group(3)}" if match else "N/A"

def extract_pan(text):
    match = re.search(r'\b[A-Z]{5}[0-9]{4}[A-Z]\b', text)
    return match.group(0) if match else "N/A"

# -----------------------------------------------
def extract_name_from_heading(text):
    lines = text.strip().split('\n')
    for line in lines:
        line = line.strip()
        if len(line.split()) <= 4 and line.replace(" ", "").isalpha() and line.isupper():
            return line.title()
    return None

def extract_name(text):
    heading_name = extract_name_from_heading(text)
    if heading_name:
        return heading_name

    nlp = get_nlp()  # ✅ lazy-load it here
    doc = nlp(text[:1000])
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text
    return "N/A"

# -----------------------------------------------
def extract_links(text):
    urls = re.findall(r'(https?://[^\s\]\)>,]+|www\.[^\s\]\)>,]+)', text)
    categorized = []
    for url in urls:
        clean_url = url.strip().rstrip(".,);")
        if clean_url.startswith("www."):
            clean_url = "https://" + clean_url
        if "linkedin.com" in clean_url.lower():
            categorized.append(f"LinkedIn: {clean_url}")
        elif "github.com" in clean_url.lower():
            categorized.append(f"GitHub: {clean_url}")
        elif "behance.net" in clean_url.lower():
            categorized.append(f"Behance: {clean_url}")
        elif any(ext in clean_url.lower() for ext in [".me", ".dev", ".design", "portfolio"]):
            categorized.append(f"Portfolio: {clean_url}")
    return ' | '.join(categorized) if categorized else "N/A"

# -----------------------------------------------
def extract_skills(text):
    skill_list = [
        "Python", "Java", "C++", "SQL", "Power BI", "Tableau", "Excel",
        "SEO", "Google Ads", "Content Marketing", "Social Media", "Branding",
        "Financial Analysis", "Budgeting", "Forecasting", "Accounting", "Tally",
        "Photoshop", "Illustrator", "Figma", "UI/UX", "Canva",
        "Recruitment", "Payroll", "Employee Engagement", "Onboarding", "HRIS"
    ]
    found = [skill for skill in skill_list if re.search(rf'\b{re.escape(skill)}\b', text, re.IGNORECASE)]
    return ' | '.join(found) if found else "N/A"

# -----------------------------------------------
def extract_section(text, keywords, limit=700):
    pattern = rf'(?i)\b({keywords})\b[\s:–\-]*\n?(.*?)(?=\n[A-Z][^\n]*?:|\n\n|\Z)'
    matches = re.findall(pattern, text, re.DOTALL)
    if matches:
        content = " ".join([m[1].strip() for m in matches if m[1].strip()])
        content = re.sub(r'\s+', ' ', content)
        return content[:limit] + "..." if len(content) > limit else content
    return "N/A"

# -----------------------------------------------
def extract_highest_education(text):
    section = extract_section(text, "academic profile|education|qualification", limit=1000)
    if section == "N/A":
        return "N/A"
    degrees = [
        r"(post\s*graduate|pg|p\.g\.)",
        r"(master(?:'s)?|msc|m\.sc|mba|mca|mtech|m\.tech)",
        r"(bachelor(?:'s)?|b\.?sc|bsc|b\.?tech|bba|bcom|b\.?com|ba|b\.?a)",
        r"(diploma)",
        r"(inter|hsc|12th|10\+2)",
        r"(10th|ssc|matriculation)"
    ]
    for pattern in degrees:
        match = re.search(rf".*({pattern}).*", section, re.IGNORECASE)
        if match:
            return match.group(0).strip()
    return section[:100] + "..." if len(section) > 100 else section

# -----------------------------------------------
def match_score(resume_skills, jd_text):
    if resume_skills == "N/A" or not jd_text.strip():
        return 0
    jd_keywords = set(re.findall(r'\b\w+\b', jd_text.lower()))
    resume_keywords = set([skill.strip().lower() for skill in resume_skills.split('|')])
    match_count = len(resume_keywords & jd_keywords)
    return round((match_count / len(resume_keywords)) * 100) if resume_keywords else 0

# -----------------------------------------------
def parse_resume(file):
    try:
        text, _ = extract_text_from_file(file)
        if not text or len(text.strip()) < 50:
            return {"Error": "Resume text is empty or unreadable."}
        return {
            "Name": extract_name(text),
            "Email": extract_email(text),
            "Phone": extract_phone(text),
            "Date of Birth": extract_dob(text),
            "PAN Number": extract_pan(text),
            "Professional Links (LinkedIn | GitHub | Portfolio)": extract_links(text),
            "Top Skills": extract_skills(text),
            "Career Objective / Summary": extract_section(text, "objective|summary", limit=600),
            "Experience Section": extract_section(text, "experience|employment|projects|responsibilities", limit=500),
            "Highest Education": extract_highest_education(text),
        }
    except Exception as e:
        return {"Error": f"Parsing failed: {e}"}




