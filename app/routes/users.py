from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.db import read_db, write_db, get_next_id, find_by_id, find_index_by_id
from app.helpers import login_required, admin_required, now

users_bp = Blueprint('users', __name__)

PERMISSIONS = [
    {'key': 'view_buy_price',   'label': 'عرض سعر الشراء'},
    {'key': 'view_sell_price',  'label': 'عرض سعر البيع'},
    {'key': 'view_profit',      'label': 'عرض الأرباح'},
    {'key': 'order_from_supplier', 'label': 'إنشاء طلبات من المورد'},
    {'key': 'manage_purchases', 'label': 'إدارة المشتريات'},
    {'key': 'manage_payments',  'label': 'إدارة المدفوعات'},
    {'key': 'manage_clients',   'label': 'إدارة العملاء'},
    {'key': 'manage_suppliers', 'label': 'إدارة الموردين'},
    {'key': 'manage_products',  'label': 'إدارة المنتجات'},
    {'key': 'manage_inventory', 'label': 'إدارة المخزون'},
    {'key': 'view_dashboard',   'label': 'عرض لوحة التحكم'},
]

def get_user_permissions(user):
    if user.get('role') == 'admin':
        return ['all']
    return user.get('permissions', [])

def has_perm(perm):
    user = session.get('user', {})
    if user.get('role') == 'admin':
        return True
    perms = user.get('permissions', [])
    return 'all' in perms or perm in perms

@users_bp.route('/users')
@admin_required
def index():
    users = read_db('users')
    return render_template('users/index.html', users=users, all_permissions=PERMISSIONS)

@users_bp.route('/users/add', methods=['GET', 'POST'])
@admin_required
def add():
    if request.method == 'POST':
        users = read_db('users')
        email = request.form.get('email', '').strip().lower()
        if any(u['email'].lower() == email for u in users):
            flash('البريد الإلكتروني مستخدم بالفعل', 'danger')
            return redirect(url_for('users.add'))
        username = request.form.get('username', '').strip().lower()
        if any(u.get('username', '').lower() == username for u in users):
            flash('اسم المستخدم مستخدم بالفعل', 'danger')
            return redirect(url_for('users.add'))
        perms = request.form.getlist('permissions')
        user = {
            'id': get_next_id(users),
            'name': request.form.get('name', '').strip(),
            'username': username,
            'email': email,
            'password': request.form.get('password', '').strip(),
            'role': 'user',
            'permissions': perms,
            'created_at': now()
        }
        users.append(user)
        write_db('users', users)
        flash('تم إنشاء الحساب بنجاح', 'success')
        return redirect(url_for('users.index'))
    return render_template('users/form.html', user=None, action='add', all_permissions=PERMISSIONS)

@users_bp.route('/users/edit/<id>', methods=['GET', 'POST'])
@admin_required
def edit(id):
    users = read_db('users')
    user = find_by_id(users, id)
    if not user:
        flash('المستخدم غير موجود', 'danger')
        return redirect(url_for('users.index'))
    if user.get('role') == 'admin' and str(id) == '1':
        flash('لا يمكن تعديل حساب المدير الرئيسي من هنا', 'warning')
        return redirect(url_for('users.index'))
    if request.method == 'POST':
        idx = find_index_by_id(users, id)
        perms = request.form.getlist('permissions')
        users[idx]['name']     = request.form.get('name', '').strip()
        users[idx]['username'] = request.form.get('username', '').strip().lower()
        users[idx]['email']    = request.form.get('email', '').strip().lower()
        users[idx]['permissions'] = perms
        new_pw = request.form.get('password', '').strip()
        if new_pw:
            users[idx]['password'] = new_pw
        write_db('users', users)
        flash('تم تعديل الحساب بنجاح', 'success')
        return redirect(url_for('users.index'))
    return render_template('users/form.html', user=user, action='edit', all_permissions=PERMISSIONS)

@users_bp.route('/users/delete/<id>', methods=['POST'])
@admin_required
def delete(id):
    if str(id) == '1':
        flash('لا يمكن حذف حساب المدير الرئيسي', 'danger')
        return redirect(url_for('users.index'))
    users = read_db('users')
    users = [u for u in users if u['id'] != str(id)]
    write_db('users', users)
    flash('تم حذف الحساب بنجاح', 'success')
    return redirect(url_for('users.index'))