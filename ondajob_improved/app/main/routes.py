from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.database import get_db

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT COUNT(*) as c FROM jobs WHERE status='active'")
    job_count = cur.fetchone()['c']
    cur.execute("SELECT COUNT(*) as c FROM users WHERE role='employer'")
    emp_count = cur.fetchone()['c']
    cur.execute("SELECT COUNT(*) as c FROM users WHERE role='jobseeker'")
    js_count = cur.fetchone()['c']
    cur.execute("""SELECT j.*, e.company_name FROM jobs j
                   JOIN employer_profiles e ON j.employer_id=e.user_id
                   WHERE j.status='active' ORDER BY j.created_at DESC LIMIT 6""")
    featured_jobs = cur.fetchall()
    cur.close(); db.close()
    return render_template('index.html', job_count=job_count,
                           emp_count=emp_count, js_count=js_count,
                           featured_jobs=featured_jobs)


@main_bp.route('/jobs')
def jobs():
    db = get_db()
    cur = db.cursor(dictionary=True)
    keyword    = request.args.get('keyword', '')
    location   = request.args.get('location', '')
    category   = request.args.get('category', '')
    job_type   = request.args.get('job_type', '')
    salary_min = request.args.get('salary_min', '')
    salary_max = request.args.get('salary_max', '')
    experience = request.args.get('experience', '')
    saved_ids = []
    if 'user_id' in session and session['role'] == 'jobseeker':
        cur.execute("SELECT job_id FROM saved_jobs WHERE user_id=%s", (session['user_id'],))
        saved_ids = [r['job_id'] for r in cur.fetchall()]
    query = """SELECT j.*, e.company_name, e.logo_url FROM jobs j
               JOIN employer_profiles e ON j.employer_id=e.user_id
               WHERE j.status='active'"""
    params = []
    if keyword:
        query += " AND (j.title LIKE %s OR j.description LIKE %s OR j.required_skills LIKE %s)"
        params += [f'%{keyword}%'] * 3
    if location:
        query += " AND j.location LIKE %s"; params.append(f'%{location}%')
    if category:
        query += " AND j.category=%s"; params.append(category)
    if job_type:
        query += " AND j.job_type=%s"; params.append(job_type)
    if salary_min:
        query += " AND j.salary_max >= %s"; params.append(salary_min)
    if salary_max:
        query += " AND j.salary_min <= %s"; params.append(salary_max)
    if experience:
        query += " AND j.experience_level=%s"; params.append(experience)
    query += " ORDER BY j.created_at DESC"
    cur.execute(query, params)
    all_jobs = cur.fetchall()
    cur.execute("SELECT DISTINCT category FROM jobs WHERE status='active' AND category IS NOT NULL")
    categories = [r['category'] for r in cur.fetchall()]
    cur.close(); db.close()
    return render_template('jobs.html', jobs=all_jobs, categories=categories,
                           saved_ids=saved_ids, filters=request.args)


@main_bp.route('/job/<int:job_id>')
def job_detail(job_id):
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("""SELECT j.*, e.company_name, e.company_description, e.website,
                   e.logo_url, e.location as company_location
                   FROM jobs j JOIN employer_profiles e ON j.employer_id=e.user_id
                   WHERE j.id=%s""", (job_id,))
    job = cur.fetchone()
    if not job:
        cur.close(); db.close()
        flash('Job not found.', 'danger')
        return redirect(url_for('main.jobs'))
    is_saved = False
    has_applied = False
    if 'user_id' in session and session['role'] == 'jobseeker':
        cur.execute("SELECT id FROM saved_jobs WHERE user_id=%s AND job_id=%s",
                    (session['user_id'], job_id))
        is_saved = bool(cur.fetchone())
        cur.execute("SELECT id FROM applications WHERE job_id=%s AND applicant_id=%s",
                    (job_id, session['user_id']))
        has_applied = bool(cur.fetchone())
    cur.execute("""SELECT j.id, j.title, e.company_name FROM jobs j
                   JOIN employer_profiles e ON j.employer_id=e.user_id
                   WHERE j.employer_id=%s AND j.status='active' AND j.id!=%s LIMIT 4""",
                (job['employer_id'], job_id))
    related = cur.fetchall()
    cur.close(); db.close()
    return render_template('job_detail.html', job=job, is_saved=is_saved,
                           has_applied=has_applied, related=related)
