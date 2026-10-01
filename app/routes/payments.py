from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.db import read_db, write_db, get_next_id, find_by_id, find_index_by_id
from app.helpers import login_required, now

payments_bp = Blueprint('payments', __name__)

@payments_bp.route('/payments')
@login_required
def index():
    payments = read_db('payments')
    clients = read_db('clients')
    suppliers = read_db('suppliers')
    for p in payments:
        if p.get('type') == 'client':
            entity = find_by_id(clients, p.get('entity_id'))
        else:
            entity = find_by_id(suppliers, p.get('entity_id'))
        p['entity_name'] = entity['name'] if entity else 'غير محدد'
    payments = sorted(payments, key=lambda x: x.get('created_at', ''), reverse=True)
    return render_template('payments/index.html', payments=payments)

@payments_bp.route('/payments/add', methods=['GET', 'POST'])
@login_required
def add():
    clients = read_db('clients')
    suppliers = read_db('suppliers')
    if request.method == 'POST':
        payments = read_db('payments')
        ptype = request.form.get('type', 'client')
        entity_id = request.form.get('entity_id', '').strip()
        amount = float(request.form.get('amount', 0))

        payment = {
            'id': get_next_id(payments),
            'type': ptype,
            'entity_id': entity_id,
            'amount': round(amount, 2),
            'method': request.form.get('method', 'cash').strip(),
            'notes': request.form.get('notes', '').strip(),
            'created_by': session['user']['id'],
            'created_at': now()
        }
        payments.append(payment)
        write_db('payments', payments)

        if ptype == 'client':
            clients_db = read_db('clients')
            cidx = find_index_by_id(clients_db, entity_id)
            if cidx >= 0:
                clients_db[cidx]['total_paid'] = float(clients_db[cidx].get('total_paid', 0)) + amount
                clients_db[cidx]['balance'] = float(clients_db[cidx].get('balance', 0)) - amount
                write_db('clients', clients_db)
        else:
            suppliers_db = read_db('suppliers')
            sidx = find_index_by_id(suppliers_db, entity_id)
            if sidx >= 0:
                suppliers_db[sidx]['total_paid'] = float(suppliers_db[sidx].get('total_paid', 0)) + amount
                suppliers_db[sidx]['balance'] = float(suppliers_db[sidx].get('balance', 0)) - amount
                write_db('suppliers', suppliers_db)

        flash('تم تسجيل الدفعة بنجاح', 'success')
        return redirect(url_for('payments.index'))
    return render_template('payments/form.html', clients=clients, suppliers=suppliers, action='add')

@payments_bp.route('/payments/delete/<id>', methods=['POST'])
@login_required
def delete(id):
    payments = read_db('payments')
    payments = [p for p in payments if p['id'] != str(id)]
    write_db('payments', payments)
    flash('تم حذف الدفعة بنجاح', 'success')
    return redirect(url_for('payments.index'))