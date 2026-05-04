from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash)
from app.database import get_db
from app.utils import login_required, role_required

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/admin/dashboard')
@login_required
@role_required('admin')
def dashboard():
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("SELECT COUNT(*) as c FROM users WHERE role='jobseeker'"); js  = cur.fetchone()['c']
    cur.execute("SELECT COUNT(*) as c FROM users WHERE role='employer'");  emp = cur.fetchone()['c']
    cur.execute("SELECT COUNT(*) as c FROM jobs WHERE status='active'");   jobs = cur.fetchone()['c']
    cur.execute("SELECT COUNT(*) as c FROM applications");                 apps = cur.fetchone()['c']
    cur.execute("""SELECT u.*, COUNT(a.id) as app_count FROM users u
                   LEFT JOIN applications a ON u.id=a.applicant_id
                   WHERE u.role='jobseeker' GROUP BY u.id
                   ORDER BY u.created_at DESC LIMIT 5""")
    recent_js = cur.fetchall()
    cur.execute("""SELECT u.*, COUNT(j.id) as job_count FROM users u
                   LEFT JOIN jobs j ON u.id=j.employer_id
                   WHERE u.role='employer' GROUP BY u.id
                   ORDER BY u.created_at DESC LIMIT 5""")
    recent_emp = cur.fetchall()
    cur.execute("""SELECT j.*, e.company_name, COUNT(a.id) as app_count FROM jobs j
                   JOIN employer_profiles e ON j.employer_id=e.user_id
                   LEFT JOIN applications a ON a.job_id=j.id
                   GROUP BY j.id ORDER BY j.created_at DESC LIMIT 5""")
    recent_jobs = cur.fetchall()
    cur.close(); db.close()
    return render_template('admin/dashboard.html', js_count=js, emp_count=emp,
                           job_count=jobs, app_count=apps,
                           recent_js=recent_js, recent_emp=recent_emp,
                           recent_jobs=recent_jobs)


@admin_bp.route('/admin/jobseekers')
@login_required
@role_required('admin')
def jobseekers():
    db = get_db(); cur = db.cursor(dictionary=True)
    search = request.args.get('search', '')
    query = """SELECT u.*, jp.full_name, jp.skills, COUNT(a.id) as app_count
               FROM users u
               LEFT JOIN jobseeker_profiles jp ON u.id=jp.user_id
               LEFT JOIN applications a ON u.id=a.applicant_id
               WHERE u.role='jobseeker'"""
    params = []
    if search:
        query += " AND (u.name LIKE %s OR u.email LIKE %s)"; params += [f'%{search}%'] * 2
    query += " GROUP BY u.id ORDER BY u.created_at DESC"
    cur.execute(query, params)
    users = cur.fetchall()
    cur.close(); db.close()
    return render_template('admin/jobseekers.html', users=users, search=search)


@admin_bp.route('/admin/employers')
@login_required
@role_required('admin')
def employers():
    db = get_db(); cur = db.cursor(dictionary=True)
    search = request.args.get('search', '')
    query = """SELECT u.*, ep.company_name, ep.industry, COUNT(j.id) as job_count
               FROM users u
               LEFT JOIN employer_profiles ep ON u.id=ep.user_id
               LEFT JOIN jobs j ON u.id=j.employer_id
               WHERE u.role='employer'"""
    params = []
    if search:
        query += " AND (u.name LIKE %s OR ep.company_name LIKE %s)"
        params += [f'%{search}%'] * 2
    query += " GROUP BY u.id ORDER BY u.created_at DESC"
    cur.execute(query, params)
    users = cur.fetchall()
    cur.close(); db.close()
    return render_template('admin/employers.html', users=users, search=search)


@admin_bp.route('/admin/jobs')
@login_required
@role_required('admin')
def jobs():
    db = get_db(); cur = db.cursor(dictionary=True)
    search        = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    query = """SELECT j.*, e.company_name, COUNT(a.id) as app_count FROM jobs j
               JOIN employer_profiles e ON j.employer_id=e.user_id
               LEFT JOIN applications a ON a.job_id=j.id
               WHERE 1=1"""
    params = []
    if search:
        query += " AND (j.title LIKE %s OR e.company_name LIKE %s)"
        params += [f'%{search}%'] * 2
    if status_filter:
        query += " AND j.status=%s"; params.append(status_filter)
    query += " GROUP BY j.id ORDER BY j.created_at DESC"
    cur.execute(query, params)
    all_jobs = cur.fetchall()
    cur.close(); db.close()
    return render_template('admin/jobs.html', jobs=all_jobs,
                           search=search, status_filter=status_filter)


@admin_bp.route('/admin/user/<int:user_id>/toggle', methods=['POST'])
@login_required
@role_required('admin')
def toggle_user(user_id):
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("SELECT is_active FROM users WHERE id=%s", (user_id,))
    u = cur.fetchone()
    if u:
        cur.execute("UPDATE users SET is_active=%s WHERE id=%s",
                    (not u['is_active'], user_id))
        db.commit()
    cur.close(); db.close()
    flash('User status updated.', 'success')
    return redirect(request.referrer or url_for('admin.dashboard'))


@admin_bp.route('/admin/job/<int:job_id>/toggle', methods=['POST'])
@login_required
@role_required('admin')
def toggle_job(job_id):
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("SELECT status FROM jobs WHERE id=%s", (job_id,))
    j = cur.fetchone()
    if j:
        new_status = 'inactive' if j['status'] == 'active' else 'active'
        cur.execute("UPDATE jobs SET status=%s WHERE id=%s", (new_status, job_id))
        db.commit()
    cur.close(); db.close()
    flash('Job status updated.', 'success')
    return redirect(request.referrer or url_for('admin.jobs'))
