from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.db import read_db
import hashlib, os

auth_bp = Blueprint('auth', __name__)

def _get_company():
    settings = read_db('settings')
    return settings[0] if settings else {}

@auth_bp.route('/')
def root():
    if 'user' in session:
        return redirect(url_for('dashboard.index'))
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('dashboard.index'))

    company = _get_company()

    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '').strip()
        remember = request.form.get('remember') == 'on'

        users = read_db('users')
        user  = next((u for u in users
                      if u.get('username', '').lower() == username
                      and u['password'] == password), None)

        if user:
            session.permanent = remember
            session['user'] = {
                'id':          user['id'],
                'name':        user['name'],
                'email':       user.get('email', ''),
                'role':        user.get('role', 'user'),
                'permissions': user.get('permissions', [])
            }
            flash(f"مرحباً، {user['name']}!", 'success')
            return redirect(url_for('dashboard.index'))
        else:
            flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'danger')

    return render_template('auth/login.html', company=company)

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('تم تسجيل الخروج بنجاح', 'success')
    return redirect(url_for('auth.login'))