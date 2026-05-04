import os
import re
import json
from functools import wraps
from flask import session, flash, redirect, url_for, current_app
import PyPDF2
from app.database import get_db

# ── Auth Decorators ───────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to continue.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'role' not in session or session['role'] not in roles:
                flash('Unauthorized access.', 'danger')
                return redirect(url_for('main.index'))
            return f(*args, **kwargs)
        return decorated
    return decorator


# ── File helpers ──────────────────────────────────────────────────────────────

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ── PDF Parser ────────────────────────────────────────────────────────────────

def extract_text_from_pdf(filepath):
    text = ""
    try:
        with open(filepath, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() or ""
    except Exception:
        pass
    return text


def parse_resume_text(text):
    data = {}
    email_match = re.search(r'[\w.+-]+@[\w-]+\.[a-z]{2,}', text, re.I)
    data['email'] = email_match.group(0) if email_match else ''
    phone_match = re.search(r'(\+?\d[\d\s\-().]{7,}\d)', text)
    data['phone'] = phone_match.group(0).strip() if phone_match else ''
    skills_keywords = [
        'Python', 'Java', 'JavaScript', 'PHP', 'SQL', 'HTML', 'CSS', 'React',
        'Node', 'Django', 'Flask', 'MySQL', 'MongoDB', 'AWS', 'Docker', 'Git',
        'C++', 'C#', 'Ruby', 'Swift', 'Kotlin', 'Excel', 'PowerPoint',
        'Communication', 'Leadership', 'Management'
    ]
    found_skills = [s for s in skills_keywords if s.lower() in text.lower()]
    data['skills'] = ', '.join(found_skills)
    data['raw_text'] = text[:3000]
    return data


# ── AI Resume Scoring ─────────────────────────────────────────────────────────

def score_resume_against_job(resume_text, job_title, job_description, required_skills):
    score = 0
    resume_lower = (resume_text or '').lower()
    title_words = (job_title or '').lower().split()
    title_matches = sum(1 for w in title_words if w in resume_lower)
    score += min(title_matches * 5, 20)
    if job_description:
        desc_words = [w for w in job_description.lower().split() if len(w) > 4]
        desc_matches = sum(1 for w in desc_words if w in resume_lower)
        score += min(desc_matches * 2, 30)
    if required_skills:
        skills_list = [s.strip().lower() for s in required_skills.split(',')]
        skill_matches = sum(1 for s in skills_list if s in resume_lower)
        score += int((skill_matches / max(len(skills_list), 1)) * 50)
    return min(score, 100)


# ── Job Recommendations ───────────────────────────────────────────────────────

def get_job_recommendations(user_id):
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute(
        "SELECT skills, preferred_location, experience_years "
        "FROM jobseeker_profiles WHERE user_id=%s", (user_id,)
    )
    profile = cur.fetchone()
    if not profile:
        cur.execute(
            "SELECT * FROM jobs WHERE status='active' ORDER BY created_at DESC LIMIT 6"
        )
        jobs = cur.fetchall()
        cur.close(); db.close()
        return jobs
    skills   = (profile.get('skills') or '').lower()
    location = (profile.get('preferred_location') or '').lower()
    cur.execute("""
        SELECT j.*, e.company_name FROM jobs j
        JOIN employer_profiles e ON j.employer_id = e.user_id
        WHERE j.status = 'active' ORDER BY j.created_at DESC LIMIT 50
    """)
    all_jobs = cur.fetchall()
    cur.close(); db.close()
    scored = []
    for job in all_jobs:
        s = 0
        if skills:
            req = (job.get('required_skills') or '').lower()
            skill_list = [x.strip() for x in skills.split(',')]
            s += sum(5 for sk in skill_list if sk and sk in req)
        if location and location in (job.get('location') or '').lower():
            s += 20
        scored.append((s, job))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [j for _, j in scored[:6]]
