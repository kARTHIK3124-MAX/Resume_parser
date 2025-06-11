import os
os.system("python -m spacy download en_core_web_sm")

import streamlit as st
import pandas as pd
from parser_utils import parse_resume, match_score

st.set_page_config(page_title="Smart Resume Matcher", layout="wide")
st.title("Smart Applicant Screener And Role Fit Analyzer")

st.markdown("""
Upload multiple resumes (**PDF/DOCX**) and paste a **Job Description** or keywords 
(e.g. `Python`, `Power BI`). You'll see matched resumes in a clean table with CSV export.
""")

# Input: JD / keyword filter
jd_text = st.text_area("📄 Paste Job Description or keywords:")

# Upload resumes
uploaded_files = st.file_uploader("📂 Upload Resume(s)", type=["pdf", "docx"], accept_multiple_files=True)

# Define consistent column structure
expected_columns = [
    "File Name", "Name", "Email", "Phone", "Date of Birth", "PAN Number",
    "Professional Links (LinkedIn | GitHub | Portfolio)", "Top Skills",
    "Career Objective / Summary", "Experience Section", "Highest Education",
    "Match Score (%)"
]

results = []

if uploaded_files:
    st.info("⏳ Parsing resumes...")

    for file in uploaded_files:
        parsed = parse_resume(file)

        # Skip errored resumes
        if "Error" in parsed:
            st.error(f"❌ {file.name} - {parsed['Error']}")
            continue

        # Add file name & match score
        parsed["File Name"] = file.name
        parsed["Match Score (%)"] = match_score(parsed.get("Top Skills", ""), jd_text)

        # Ensure all expected columns exist (fill missing with "N/A")
        for col in expected_columns:
            parsed.setdefault(col, "N/A")

        results.append(parsed)

    if results:
        # Ensure all dicts have same keys
        df = pd.DataFrame(results)[expected_columns]

        # Smart keyword filtering
        if jd_text.strip():
            keywords = [word.lower() for word in jd_text.split() if len(word) > 2]

            def skill_match(skills):
                if isinstance(skills, str):
                    skills = skills.lower()
                    return any(kw in skills for kw in keywords)
                return False

            df = df[df["Top Skills"].apply(skill_match)]

        if not df.empty:
            st.success(f"✅ Showing {len(df)} matching resume(s).")
            st.dataframe(df)

            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download Filtered Results as CSV",
                data=csv,
                file_name="filtered_resumes.csv",
                mime="text/csv"
            )
        else:
            st.warning("⚠️ No resumes matched the filter.")
    else:
        st.warning("⚠️ No valid resumes were parsed.")
else:
    st.info("📥 Upload resumes to get started.")

