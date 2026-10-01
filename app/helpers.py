from datetime import datetime
from functools import wraps
from flask import session, redirect, url_for, flash

def now():
    return datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            flash('يجب تسجيل الدخول أولاً', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('auth.login'))
        if session['user'].get('role') != 'admin':
            flash('ليس لديك صلاحية للوصول', 'danger')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated

def format_currency(amount):
    try:
        return "{:,.2f}".format(float(amount))
    except:
        return "0.00"