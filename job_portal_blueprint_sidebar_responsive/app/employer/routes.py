from datetime import datetime
from flask import (Blueprint, render_template, request, redirect,
                   url_for, session, flash)
from app.database import get_db
from app.utils import login_required, role_required
from app.extensions import mail
from flask_mail import Message

employer_bp = Blueprint('employer', __name__)


@employer_bp.route('/employer/dashboard')
@login_required
@role_required('employer')
def dashboard():
    db = get_db(); cur = db.cursor(dictionary=True)
    uid = session['user_id']
    cur.execute("SELECT COUNT(*) as c FROM jobs WHERE employer_id=%s AND status='active'", (uid,))
    active_jobs = cur.fetchone()['c']
    cur.execute("""SELECT COUNT(*) as c FROM applications a
                   JOIN jobs j ON a.job_id=j.id WHERE j.employer_id=%s""", (uid,))
    total_apps = cur.fetchone()['c']
    cur.execute("""SELECT COUNT(*) as c FROM applications a
                   JOIN jobs j ON a.job_id=j.id
                   WHERE j.employer_id=%s AND a.status='interview'""", (uid,))
    interviews = cur.fetchone()['c']
    cur.execute("""SELECT j.id, j.title, j.created_at, COUNT(a.id) as app_count
                   FROM jobs j LEFT JOIN applications a ON a.job_id=j.id
                   WHERE j.employer_id=%s GROUP BY j.id
                   ORDER BY j.created_at DESC LIMIT 5""", (uid,))
    recent_jobs = cur.fetchall()
    cur.execute("""SELECT a.*, jp.full_name, jp.skills, u.email, j.title as job_title
                   FROM applications a
                   JOIN jobseeker_profiles jp ON a.applicant_id=jp.user_id
                   JOIN users u ON a.applicant_id=u.id
                   JOIN jobs j ON a.job_id=j.id
                   WHERE j.employer_id=%s ORDER BY a.applied_at DESC LIMIT 5""", (uid,))
    recent_apps = cur.fetchall()
    cur.execute("""SELECT m.*, u.name as sender_name FROM messages m
                   JOIN users u ON m.sender_id=u.id
                   WHERE m.receiver_id=%s AND m.is_read=0
                   ORDER BY m.created_at DESC LIMIT 5""", (uid,))
    unread_msgs = cur.fetchall()
    cur.close(); db.close()
    return render_template('employer/dashboard.html',
                           active_jobs=active_jobs, total_apps=total_apps,
                           interviews=interviews, recent_jobs=recent_jobs,
                           recent_apps=recent_apps, unread_msgs=unread_msgs)


@employer_bp.route('/employer/profile', methods=['GET', 'POST'])
@login_required
@role_required('employer')
def profile():
    db = get_db(); cur = db.cursor(dictionary=True)
    uid = session['user_id']
    if request.method == 'POST':
        fields = ['company_name', 'industry', 'company_size', 'website',
                  'location', 'phone', 'company_description']
        vals = [request.form.get(f, '') for f in fields]
        cur.execute("""UPDATE employer_profiles SET
                    company_name=%s, industry=%s, company_size=%s, website=%s,
                    location=%s, phone=%s, company_description=%s
                    WHERE user_id=%s""", vals + [uid])
        db.commit()
        flash('Profile updated!', 'success')
        return redirect(url_for('employer.profile'))
    cur.execute("SELECT * FROM employer_profiles WHERE user_id=%s", (uid,))
    profile_data = cur.fetchone()
    cur.close(); db.close()
    return render_template('employer/profile.html', profile=profile_data)


@employer_bp.route('/employer/post-job', methods=['GET', 'POST'])
@login_required
@role_required('employer')
def post_job():
    db = get_db(); cur = db.cursor(dictionary=True)
    uid = session['user_id']
    if request.method == 'POST':
        data = {
            'employer_id':      uid,
            'title':            request.form['title'],
            'category':         request.form.get('category', ''),
            'job_type':         request.form['job_type'],
            'experience_level': request.form.get('experience_level', ''),
            'location':         request.form['location'],
            'salary_min':       request.form.get('salary_min') or None,
            'salary_max':       request.form.get('salary_max') or None,
            'required_skills':  request.form.get('required_skills', ''),
            'description':      request.form['description'],
            'requirements':     request.form.get('requirements', ''),
            'benefits':         request.form.get('benefits', ''),
            'deadline':         request.form.get('deadline') or None,
            'slots':            request.form.get('slots', 1),
            'status':           'active'
        }
        cur.execute("""INSERT INTO jobs
                    (employer_id,title,category,job_type,experience_level,
                     location,salary_min,salary_max,required_skills,description,
                     requirements,benefits,deadline,slots,status)
                    VALUES
                    (%(employer_id)s,%(title)s,%(category)s,%(job_type)s,%(experience_level)s,
                     %(location)s,%(salary_min)s,%(salary_max)s,%(required_skills)s,%(description)s,
                     %(requirements)s,%(benefits)s,%(deadline)s,%(slots)s,%(status)s)""", data)
        db.commit()
        flash('Job posted successfully!', 'success')
        cur.close(); db.close()
        return redirect(url_for('employer.manage_jobs'))
    cur.close(); db.close()
    return render_template('employer/post_job.html')


@employer_bp.route('/employer/jobs')
@login_required
@role_required('employer')
def manage_jobs():
    db = get_db(); cur = db.cursor(dictionary=True)
    uid = session['user_id']
    cur.execute("""SELECT j.*, COUNT(a.id) as app_count FROM jobs j
                   LEFT JOIN applications a ON a.job_id=j.id
                   WHERE j.employer_id=%s GROUP BY j.id
                   ORDER BY j.created_at DESC""", (uid,))
    jobs = cur.fetchall()
    cur.close(); db.close()
    return render_template('employer/manage_jobs.html', jobs=jobs, now=datetime.now().date())


@employer_bp.route('/employer/job/<int:job_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('employer')
def edit_job(job_id):
    db = get_db(); cur = db.cursor(dictionary=True)
    uid = session['user_id']
    cur.execute("SELECT * FROM jobs WHERE id=%s AND employer_id=%s", (job_id, uid))
    job = cur.fetchone()
    if not job:
        flash('Job not found.', 'danger'); cur.close(); db.close()
        return redirect(url_for('employer.manage_jobs'))
    if request.method == 'POST':
        cur.execute("""UPDATE jobs SET
                    title=%s, category=%s, job_type=%s, experience_level=%s,
                    location=%s, salary_min=%s, salary_max=%s, required_skills=%s,
                    description=%s, requirements=%s, benefits=%s,
                    deadline=%s, slots=%s, status=%s
                    WHERE id=%s""",
                    (request.form['title'], request.form.get('category', ''),
                     request.form['job_type'], request.form.get('experience_level', ''),
                     request.form['location'],
                     request.form.get('salary_min') or None,
                     request.form.get('salary_max') or None,
                     request.form.get('required_skills', ''),
                     request.form['description'], request.form.get('requirements', ''),
                     request.form.get('benefits', ''),
                     request.form.get('deadline') or None,
                     request.form.get('slots', 1),
                     request.form.get('status', 'active'), job_id))
        db.commit()
        flash('Job updated!', 'success')
        cur.close(); db.close()
        return redirect(url_for('employer.manage_jobs'))
    cur.close(); db.close()
    return render_template('employer/post_job.html', job=job, edit=True)


@employer_bp.route('/employer/job/<int:job_id>/delete', methods=['POST'])
@login_required
@role_required('employer')
def delete_job(job_id):
    db = get_db(); cur = db.cursor()
    cur.execute("DELETE FROM jobs WHERE id=%s AND employer_id=%s",
                (job_id, session['user_id']))
    db.commit(); cur.close(); db.close()
    flash('Job deleted.', 'success')
    return redirect(url_for('employer.manage_jobs'))


@employer_bp.route('/employer/job/<int:job_id>/applicants')
@login_required
@role_required('employer')
def view_applicants(job_id):
    db = get_db(); cur = db.cursor(dictionary=True)
    uid = session['user_id']
    cur.execute("SELECT * FROM jobs WHERE id=%s AND employer_id=%s", (job_id, uid))
    job = cur.fetchone()
    if not job:
        flash('Unauthorized.', 'danger'); cur.close(); db.close()
        return redirect(url_for('employer.manage_jobs'))
    status_filter = request.args.get('status', '')
    query = """SELECT a.*, jp.full_name, jp.phone, jp.skills, jp.experience_years,
               jp.resume_path, jp.location as applicant_location, u.email, a.match_score
               FROM applications a
               JOIN jobseeker_profiles jp ON a.applicant_id=jp.user_id
               JOIN users u ON a.applicant_id=u.id
               WHERE a.job_id=%s"""
    params = [job_id]
    if status_filter:
        query += " AND a.status=%s"; params.append(status_filter)
    query += " ORDER BY a.match_score DESC, a.applied_at DESC"
    cur.execute(query, params)
    applicants = cur.fetchall()
    cur.close(); db.close()
    return render_template('employer/applicants.html', job=job,
                           applicants=applicants, status_filter=status_filter)


@employer_bp.route('/employer/application/<int:app_id>/status', methods=['POST'])
@login_required
@role_required('employer')
def update_application_status(app_id):
    db = get_db(); cur = db.cursor(dictionary=True)
    new_status      = request.form['status']
    interview_date  = request.form.get('interview_date', '')
    interview_notes = request.form.get('interview_notes', '')
    cur.execute("""UPDATE applications SET status=%s, interview_date=%s, interview_notes=%s
                   WHERE id=%s""", (new_status, interview_date or None, interview_notes, app_id))
    db.commit()
    cur.execute("""SELECT a.applicant_id, j.title, u.email FROM applications a
                   JOIN jobs j ON a.job_id=j.id
                   JOIN users u ON a.applicant_id=u.id
                   WHERE a.id=%s""", (app_id,))
    info = cur.fetchone()
    if info:
        try:
            msg_body = (f'Your application for "{info["title"]}" has been updated to: '
                        f'{new_status.upper()}')
            if interview_date:
                msg_body += f'\nInterview scheduled: {interview_date}'
            m = Message(f'Application Update - {info["title"]}',
                        recipients=[info['email']], body=msg_body)
            mail.send(m)
        except Exception:
            pass
    cur.close(); db.close()
    flash('Status updated!', 'success')
    return redirect(request.referrer or url_for('employer.dashboard'))


@employer_bp.route('/employer/analytics')
@login_required
@role_required('employer')
def analytics():
    db = get_db(); cur = db.cursor(dictionary=True)
    uid = session['user_id']
    cur.execute("""SELECT j.title, j.id, COUNT(a.id) as total,
                   SUM(CASE WHEN a.status='pending'  THEN 1 ELSE 0 END) as pending,
                   SUM(CASE WHEN a.status='reviewed' THEN 1 ELSE 0 END) as reviewed,
                   SUM(CASE WHEN a.status='interview'THEN 1 ELSE 0 END) as interview,
                   SUM(CASE WHEN a.status='hired'    THEN 1 ELSE 0 END) as hired,
                   SUM(CASE WHEN a.status='rejected' THEN 1 ELSE 0 END) as rejected,
                   AVG(a.match_score) as avg_score
                   FROM jobs j LEFT JOIN applications a ON a.job_id=j.id
                   WHERE j.employer_id=%s GROUP BY j.id ORDER BY total DESC""", (uid,))
    analytics_data = cur.fetchall()
    cur.close(); db.close()
    return render_template('employer/analytics.html', analytics=analytics_data)
