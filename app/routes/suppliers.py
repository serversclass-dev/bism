from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.db import read_db, write_db, get_next_id, find_by_id, find_index_by_id
from app.helpers import login_required, now

suppliers_bp = Blueprint('suppliers', __name__)

@suppliers_bp.route('/suppliers')
@login_required
def index():
    suppliers = read_db('suppliers')
    return render_template('suppliers/index.html', suppliers=suppliers)

@suppliers_bp.route('/suppliers/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        suppliers = read_db('suppliers')
        supplier = {
            'id': get_next_id(suppliers),
            'name': request.form.get('name', '').strip(),
            'type': request.form.get('type', '').strip(),
            'address': request.form.get('address', '').strip(),
            'phone': request.form.get('phone', '').strip(),
            'email': request.form.get('email', '').strip(),
            'balance': 0,
            'total_purchases': 0,
            'total_paid': 0,
            'notes': request.form.get('notes', '').strip(),
            'created_at': now()
        }
        suppliers.append(supplier)
        write_db('suppliers', suppliers)
        flash('تم إضافة المورد بنجاح', 'success')
        return redirect(url_for('suppliers.index'))
    return render_template('suppliers/form.html', supplier=None, action='add')

@suppliers_bp.route('/suppliers/edit/<id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    suppliers = read_db('suppliers')
    supplier = find_by_id(suppliers, id)
    if not supplier:
        flash('المورد غير موجود', 'danger')
        return redirect(url_for('suppliers.index'))
    if request.method == 'POST':
        idx = find_index_by_id(suppliers, id)
        suppliers[idx]['name'] = request.form.get('name', '').strip()
        suppliers[idx]['type'] = request.form.get('type', '').strip()
        suppliers[idx]['address'] = request.form.get('address', '').strip()
        suppliers[idx]['phone'] = request.form.get('phone', '').strip()
        suppliers[idx]['email'] = request.form.get('email', '').strip()
        suppliers[idx]['notes'] = request.form.get('notes', '').strip()
        write_db('suppliers', suppliers)
        flash('تم تعديل المورد بنجاح', 'success')
        return redirect(url_for('suppliers.index'))
    return render_template('suppliers/form.html', supplier=supplier, action='edit')

@suppliers_bp.route('/suppliers/delete/<id>', methods=['POST'])
@login_required
def delete(id):
    suppliers = read_db('suppliers')
    suppliers = [s for s in suppliers if s['id'] != str(id)]
    write_db('suppliers', suppliers)
    flash('تم حذف المورد بنجاح', 'success')
    return redirect(url_for('suppliers.index'))

@suppliers_bp.route('/suppliers/view/<id>')
@login_required
def view(id):
    suppliers = read_db('suppliers')
    supplier = find_by_id(suppliers, id)
    if not supplier:
        flash('المورد غير موجود', 'danger')
        return redirect(url_for('suppliers.index'))
    purchases = read_db('purchases')
    payments = read_db('payments')
    supplier_purchases = [p for p in purchases if p.get('supplier_id') == str(id)]
    supplier_payments = [p for p in payments if p.get('entity_id') == str(id) and p.get('type') == 'supplier']
    return render_template('suppliers/view.html', supplier=supplier, purchases=supplier_purchases, payments=supplier_payments)