from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.db import read_db, write_db, get_next_id, find_by_id, find_index_by_id
from app.helpers import login_required, now

clients_bp = Blueprint('clients', __name__)

@clients_bp.route('/clients')
@login_required
def index():
    clients = read_db('clients')
    return render_template('clients/index.html', clients=clients)

@clients_bp.route('/clients/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        clients = read_db('clients')
        client = {
            'id': get_next_id(clients),
            'name': request.form.get('name', '').strip(),
            'type': request.form.get('type', '').strip(),
            'address': request.form.get('address', '').strip(),
            'phone': request.form.get('phone', '').strip(),
            'email': request.form.get('email', '').strip(),
            'balance': 0,
            'total_sales': 0,
            'total_paid': 0,
            'notes': request.form.get('notes', '').strip(),
            'created_at': now()
        }
        clients.append(client)
        write_db('clients', clients)
        flash('تم إضافة العميل بنجاح', 'success')
        return redirect(url_for('clients.index'))
    return render_template('clients/form.html', client=None, action='add')

@clients_bp.route('/clients/edit/<id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    clients = read_db('clients')
    client = find_by_id(clients, id)
    if not client:
        flash('العميل غير موجود', 'danger')
        return redirect(url_for('clients.index'))
    if request.method == 'POST':
        idx = find_index_by_id(clients, id)
        clients[idx]['name'] = request.form.get('name', '').strip()
        clients[idx]['type'] = request.form.get('type', '').strip()
        clients[idx]['address'] = request.form.get('address', '').strip()
        clients[idx]['phone'] = request.form.get('phone', '').strip()
        clients[idx]['email'] = request.form.get('email', '').strip()
        clients[idx]['notes'] = request.form.get('notes', '').strip()
        write_db('clients', clients)
        flash('تم تعديل العميل بنجاح', 'success')
        return redirect(url_for('clients.index'))
    return render_template('clients/form.html', client=client, action='edit')

@clients_bp.route('/clients/delete/<id>', methods=['POST'])
@login_required
def delete(id):
    clients = read_db('clients')
    clients = [c for c in clients if c['id'] != str(id)]
    write_db('clients', clients)
    flash('تم حذف العميل بنجاح', 'success')
    return redirect(url_for('clients.index'))

@clients_bp.route('/clients/view/<id>')
@login_required
def view(id):
    clients = read_db('clients')
    client = find_by_id(clients, id)
    if not client:
        flash('العميل غير موجود', 'danger')
        return redirect(url_for('clients.index'))
    orders = read_db('orders')
    payments = read_db('payments')
    client_orders = [o for o in orders if o.get('client_id') == str(id)]
    client_payments = [p for p in payments if p.get('entity_id') == str(id) and p.get('type') == 'client']
    return render_template('clients/view.html', client=client, orders=client_orders, payments=client_payments)