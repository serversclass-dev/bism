from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.db import read_db, write_db, find_index_by_id
from app.helpers import login_required
import base64
import os

settings_bp = Blueprint('settings', __name__)

def get_company():
    settings = read_db('settings')
    return settings[0] if settings else {
        'id': '1', 'name': 'BIMS', 'logo': '',
        'address': '', 'phone': '', 'email': '', 'tax_number': ''
    }

@settings_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def index():
    company = get_company()
    users = read_db('users')
    if request.method == 'POST':
        action = request.form.get('action', 'company')

        if action == 'company':
            name = request.form.get('name', '').strip()
            address = request.form.get('address', '').strip()
            phone = request.form.get('phone', '').strip()
            email = request.form.get('email', '').strip()
            tax_number = request.form.get('tax_number', '').strip()
            logo = company.get('logo', '')
            logo_file = request.files.get('logo')
            if logo_file and logo_file.filename:
                ext = os.path.splitext(logo_file.filename)[1].lower()
                if ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg']:
                    data = logo_file.read()
                    b64 = base64.b64encode(data).decode('utf-8')
                    mime = 'image/svg+xml' if ext == '.svg' else ('image/png' if ext == '.png' else 'image/jpeg')
                    logo = f"data:{mime};base64,{b64}"
            currency       = request.form.get('currency', 'دج').strip()
            invoice_prefix = request.form.get('invoice_prefix', 'INV').strip()
            invoice_notes  = request.form.get('invoice_notes', '').strip()
            updated = {
                'id': '1', 'name': name, 'logo': logo,
                'address': address, 'phone': phone,
                'email': email, 'tax_number': tax_number,
                'currency': currency,
                'invoice_prefix': invoice_prefix,
                'invoice_notes': invoice_notes
            }
            write_db('settings', [updated])
            flash('تم حفظ إعدادات الشركة بنجاح ✅', 'success')

        elif action == 'password':
            user_id = session['user']['id']
            current_pw = request.form.get('current_password', '').strip()
            new_pw = request.form.get('new_password', '').strip()
            confirm_pw = request.form.get('confirm_password', '').strip()
            users = read_db('users')
            idx = find_index_by_id(users, user_id)
            if idx < 0:
                flash('المستخدم غير موجود', 'danger')
            elif users[idx]['password'] != current_pw:
                flash('كلمة المرور الحالية غير صحيحة', 'danger')
            elif new_pw != confirm_pw:
                flash('كلمة المرور الجديدة وتأكيدها غير متطابقين', 'danger')
            elif len(new_pw) < 4:
                flash('كلمة المرور يجب أن تكون 4 أحرف على الأقل', 'danger')
            else:
                users[idx]['password'] = new_pw
                write_db('users', users)
                flash('تم تغيير كلمة المرور بنجاح ✅', 'success')

        return redirect(url_for('settings.index'))

    return render_template('settings/index.html', company=company, users=users)