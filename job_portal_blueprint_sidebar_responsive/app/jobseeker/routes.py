import os
import json
from datetime import datetime
from flask import (Blueprint, render_template, request, redirect,
                   url_for, session, flash, jsonify, current_app)
from werkzeug.utils import secure_filename
from app.database import get_db
from app.utils import (login_required, role_required, allowed_file,
                       extract_text_from_pdf, parse_resume_text,
                       score_resume_against_job, get_job_recommendations)
from app.extensions import mail
from flask_mail import Message

jobseeker_bp = Blueprint('jobseeker', __name__)


@jobseeker_bp.route('/jobseeker/dashboard')
@login_required
@role_required('jobseeker')
def dashboard():
    db = get_db(); cur = db.cursor(dictionary=True)
    uid = session['user_id']
    cur.execute("""SELECT a.*, j.title, j.location, e.company_name, j.job_type
                   FROM applications a JOIN jobs j ON a.job_id=j.id
                   JOIN employer_profiles e ON j.employer_id=e.user_id
                   WHERE a.applicant_id=%s ORDER BY a.applied_at DESC LIMIT 5""", (uid,))
    recent_apps = cur.fetchall()
    cur.execute("SELECT COUNT(*) as c FROM applications WHERE applicant_id=%s", (uid,))
    app_count = cur.fetchone()['c']
    cur.execute("SELECT COUNT(*) as c FROM saved_jobs WHERE user_id=%s", (uid,))
    saved_count = cur.fetchone()['c']
    cur.execute("SELECT COUNT(*) as c FROM applications WHERE applicant_id=%s AND status='interview'", (uid,))
    interview_count = cur.fetchone()['c']
    recommended = get_job_recommendations(uid)
    cur.execute("SELECT * FROM jobseeker_profiles WHERE user_id=%s", (uid,))
    profile = cur.fetchone()
    cur.execute("""SELECT m.*, u.name as sender_name FROM messages m
                   JOIN users u ON m.sender_id=u.id
                   WHERE m.receiver_id=%s AND m.is_read=0
                   ORDER BY m.created_at DESC LIMIT 5""", (uid,))
    unread_msgs = cur.fetchall()
    cur.close(); db.close()
    return render_template('jobseeker/dashboard.html',
                           recent_apps=recent_apps, app_count=app_count,
                           saved_count=saved_count, interview_count=interview_count,
                           recommended=recommended, profile=profile,
                           unread_msgs=unread_msgs)


@jobseeker_bp.route('/jobseeker/profile', methods=['GET', 'POST'])
@login_required
@role_required('jobseeker')
def profile():
    db = get_db(); cur = db.cursor(dictionary=True)
    uid = session['user_id']
    if request.method == 'POST':
        fields = ['full_name', 'phone', 'location', 'preferred_location', 'skills',
                  'experience_years', 'education', 'bio', 'linkedin_url', 'github_url']
        vals = [request.form.get(f, '') for f in fields]
        cur.execute("""UPDATE jobseeker_profiles SET
                    full_name=%s, phone=%s, location=%s, preferred_location=%s, skills=%s,
                    experience_years=%s, education=%s, bio=%s, linkedin_url=%s, github_url=%s
                    WHERE user_id=%s""", vals + [uid])
        if 'resume' in request.files:
            file = request.files['resume']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(f"resume_{uid}_{int(datetime.now().timestamp())}.pdf")
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                text   = extract_text_from_pdf(filepath)
                parsed = parse_resume_text(text)
                cur.execute("""UPDATE jobseeker_profiles SET resume_path=%s, resume_text=%s
                               WHERE user_id=%s""", (filename, parsed['raw_text'], uid))
                if not request.form.get('skills') and parsed['skills']:
                    cur.execute("UPDATE jobseeker_profiles SET skills=%s WHERE user_id=%s",
                                (parsed['skills'], uid))
        db.commit()
        flash('Profile updated!', 'success')
        return redirect(url_for('jobseeker.profile'))
    cur.execute("SELECT * FROM jobseeker_profiles WHERE user_id=%s", (uid,))
    profile_data = cur.fetchone()
    cur.close(); db.close()
    return render_template('jobseeker/profile.html', profile=profile_data)


@jobseeker_bp.route('/jobseeker/resume-builder', methods=['GET', 'POST'])
@login_required
@role_required('jobseeker')
def resume_builder():
    db = get_db(); cur = db.cursor(dictionary=True)
    uid = session['user_id']
    if request.method == 'POST':
        resume_data = {
            'objective':       request.form.get('objective', ''),
            'work_experience': request.form.get('work_experience', ''),
            'education':       request.form.get('education', ''),
            'skills':          request.form.get('skills', ''),
            'certifications':  request.form.get('certifications', ''),
            'languages':       request.form.get('languages', ''),
            'references':      request.form.get('references', '')
        }
        cur.execute("UPDATE jobseeker_profiles SET resume_builder_data=%s WHERE user_id=%s",
                    (json.dumps(resume_data), uid))
        db.commit()
        flash('Resume saved!', 'success')
        return redirect(url_for('jobseeker.resume_builder'))
    cur.execute("SELECT * FROM jobseeker_profiles WHERE user_id=%s", (uid,))
    profile_data = cur.fetchone()
    resume_data = {}
    if profile_data and profile_data.get('resume_builder_data'):
        try:
            resume_data = json.loads(profile_data['resume_builder_data'])
        except Exception:
            pass
    cur.close(); db.close()
    return render_template('jobseeker/resume_builder.html',
                           profile=profile_data, resume_data=resume_data)


@jobseeker_bp.route('/jobseeker/applications')
@login_required
@role_required('jobseeker')
def my_applications():
    db = get_db(); cur = db.cursor(dictionary=True)
    uid = session['user_id']
    cur.execute("""SELECT a.*, j.title, j.location, j.job_type, j.salary_min, j.salary_max,
                   e.company_name, e.logo_url
                   FROM applications a JOIN jobs j ON a.job_id=j.id
                   JOIN employer_profiles e ON j.employer_id=e.user_id
                   WHERE a.applicant_id=%s ORDER BY a.applied_at DESC""", (uid,))
    apps = cur.fetchall()
    cur.close(); db.close()
    return render_template('jobseeker/applications.html', applications=apps)


@jobseeker_bp.route('/apply/<int:job_id>', methods=['GET', 'POST'])
@login_required
@role_required('jobseeker')
def apply_job(job_id):
    db = get_db(); cur = db.cursor(dictionary=True)
    uid = session['user_id']
    cur.execute("SELECT id FROM applications WHERE job_id=%s AND applicant_id=%s", (job_id, uid))
    if cur.fetchone():
        flash('You have already applied for this job.', 'warning')
        cur.close(); db.close()
        return redirect(url_for('main.job_detail', job_id=job_id))
    cur.execute("SELECT * FROM jobs WHERE id=%s AND status='active'", (job_id,))
    job = cur.fetchone()
    if not job:
        flash('Job not found.', 'danger')
        cur.close(); db.close()
        return redirect(url_for('main.jobs'))
    if request.method == 'POST':
        cover_letter = request.form.get('cover_letter', '')
        cur.execute("SELECT * FROM jobseeker_profiles WHERE user_id=%s", (uid,))
        profile_data = cur.fetchone()
        resume_text  = profile_data.get('resume_text', '') if profile_data else ''
        score = 0
        if resume_text:
            score = score_resume_against_job(resume_text, job['title'],
                                             job.get('description', ''),
                                             job.get('required_skills', ''))
        cur.execute("""INSERT INTO applications (job_id,applicant_id,cover_letter,match_score,status)
                       VALUES (%s,%s,%s,%s,'pending')""", (job_id, uid, cover_letter, score))
        db.commit()
        cur.execute("SELECT * FROM users WHERE id=%s", (job['employer_id'],))
        employer_user = cur.fetchone()
        if employer_user:
            try:
                msg = Message(f'New Application: {job["title"]}',
                              recipients=[employer_user['email']],
                              body=f'You have a new applicant for {job["title"]}. Match score: {score}%')
                mail.send(msg)
            except Exception:
                pass
        flash(f'Application submitted! Your match score: {score}%', 'success')
        cur.close(); db.close()
        return redirect(url_for('jobseeker.my_applications'))
    cur.execute("SELECT * FROM jobseeker_profiles WHERE user_id=%s", (uid,))
    profile_data = cur.fetchone()
    cur.close(); db.close()
    return render_template('jobseeker/apply.html', job=job, profile=profile_data)


@jobseeker_bp.route('/save-job/<int:job_id>', methods=['POST'])
@login_required
@role_required('jobseeker')
def save_job(job_id):
    db = get_db(); cur = db.cursor(dictionary=True)
    uid = session['user_id']
    cur.execute("SELECT id FROM saved_jobs WHERE user_id=%s AND job_id=%s", (uid, job_id))
    if cur.fetchone():
        cur.execute("DELETE FROM saved_jobs WHERE user_id=%s AND job_id=%s", (uid, job_id))
        db.commit(); cur.close(); db.close()
        return jsonify({'saved': False})
    cur.execute("INSERT INTO saved_jobs (user_id,job_id) VALUES (%s,%s)", (uid, job_id))
    db.commit(); cur.close(); db.close()
    return jsonify({'saved': True})


@jobseeker_bp.route('/jobseeker/saved-jobs')
@login_required
@role_required('jobseeker')
def saved_jobs():
    db = get_db(); cur = db.cursor(dictionary=True)
    uid = session['user_id']
    cur.execute("""SELECT j.*, e.company_name, e.logo_url FROM saved_jobs s
                   JOIN jobs j ON s.job_id=j.id
                   JOIN employer_profiles e ON j.employer_id=e.user_id
                   WHERE s.user_id=%s ORDER BY s.saved_at DESC""", (uid,))
    jobs = cur.fetchall()
    cur.close(); db.close()
    return render_template('jobseeker/saved_jobs.html', jobs=jobs)
