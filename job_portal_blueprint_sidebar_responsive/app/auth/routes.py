from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import bcrypt
from app.database import get_db

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name     = request.form['name']
        email    = request.form['email']
        password = request.form['password']
        role     = request.form['role']
        hashed   = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        db = get_db(); cur = db.cursor(dictionary=True)
        cur.execute("SELECT id FROM users WHERE email=%s", (email,))
        if cur.fetchone():
            flash('Email already registered.', 'danger')
            cur.close(); db.close()
            return redirect(url_for('auth.signup'))
        cur.execute("INSERT INTO users (name,email,password,role) VALUES (%s,%s,%s,%s)",
                    (name, email, hashed, role))
        user_id = cur.lastrowid
        if role == 'jobseeker':
            cur.execute("INSERT INTO jobseeker_profiles (user_id,full_name) VALUES (%s,%s)",
                        (user_id, name))
        elif role == 'employer':
            cur.execute("INSERT INTO employer_profiles (user_id,company_name) VALUES (%s,%s)",
                        (user_id, name))
        db.commit(); cur.close(); db.close()
        flash('Account created! Please login.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/signup.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email    = request.form['email']
        password = request.form['password']
        db = get_db(); cur = db.cursor(dictionary=True)
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
        cur.close(); db.close()
        if user and bcrypt.checkpw(password.encode(), user['password'].encode()):
            session['user_id'] = user['id']
            session['role']    = user['role']
            session['name']    = user['name']
            session['email']   = user['email']
            if user['role'] == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif user['role'] == 'employer':
                return redirect(url_for('employer.dashboard'))
            else:
                return redirect(url_for('jobseeker.dashboard'))
        flash('Invalid credentials.', 'danger')
    return render_template('auth/login.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('main.index'))
