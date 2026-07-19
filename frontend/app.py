import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000/analyze"

st.set_page_config(
    page_title="AI Recruitment Copilot",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 AI Recruitment Copilot")

st.write(
    "Upload a Resume PDF and a Job Description PDF to analyze the candidate."
)

st.divider()

resume = st.file_uploader(
    "Upload Resume",
    type=["pdf"]
)

jd = st.file_uploader(
    "Upload Job Description",
    type=["pdf"]
)

if st.button("Analyze Candidate"):

    if resume is None or jd is None:
        st.error("Please upload both files.")
        st.stop()

    with st.spinner("Analyzing..."):

        files = {
            "resume": (
                resume.name,
                resume,
                "application/pdf"
            ),
            "jd": (
                jd.name,
                jd,
                "application/pdf"
            )
        }

        response = requests.post(
            API_URL,
            files=files
        )

    if response.status_code == 200:

        result = response.json()

        st.success("Analysis Complete ✅")

        st.divider()

        # -------------------------
        # Resume Analysis
        # -------------------------
        resume = result["resume_analysis"]

        st.header("📄 Resume Analysis")

        st.write(f"**Candidate Name:** {resume['candidate_name']}")

        st.write(f"**Experience:** {resume['experience_years']} years")

        st.write(f"**Education:** {resume['education']}")

        st.subheader("Skills")

        for skill in resume["skills"]:
            st.write(f"✅ {skill}")

        st.subheader("Projects")

        for project in resume["projects"]:
            st.write(f"• {project}")

        st.divider()

        # -------------------------
        # Job Description
        # -------------------------

        jd = result["job_description"]

        st.header("📋 Job Description")

        st.subheader("Required Skills")

        for skill in jd["required_skills"]:
            st.write(f"✅ {skill}")

        st.subheader("Preferred Skills")

        for skill in jd["preferred_skills"]:
            st.write(f"⭐ {skill}")

        st.write(
            f"**Minimum Experience:** {jd['minimum_experience']} years"
        )

        st.subheader("Responsibilities")

        for responsibility in jd["responsibilities"]:
            st.write(f"• {responsibility}")

        st.divider()

        # -------------------------
        # Match Result
        # -------------------------

        match = result["match_result"]

        # st.write(result)
        # st.stop()

        st.header("🎯 Match Result")

        st.metric(
            "Match Score",
            f"{match['match_percentage']}%"
        )

        st.subheader("Summary")

        st.write(match["summary"])

        st.subheader("Recommendation")

        st.success(match["recommendation"])

        st.subheader("Matched Skills")

        for skill in match["matched_skills"]:
            st.write(f"✅ {skill}")

        st.subheader("Missing Skills")

        for skill in match["missing_skills"]:
            st.write(f"❌ {skill}")

        st.write(
            f"**Experience Match:** {match['experience_match']}"
        )

        st.divider()

        # -------------------------
        # Interview Questions
        # -------------------------
        st.header("💬 Interview Questions")

        questions = result["interview_questions"]

        st.markdown(result["interview_questions"])

    else:

        st.error("Backend Error")

        st.write(response.text)