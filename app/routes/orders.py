from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.db import read_db, write_db, get_next_id, find_by_id, find_index_by_id
from app.helpers import login_required, now

orders_bp = Blueprint('orders', __name__)

def get_company():
    settings = read_db('settings')
    return settings[0] if settings else {'name': 'BIMS', 'logo': '', 'address': '', 'phone': '', 'email': '', 'tax_number': ''}

# ── helpers ──────────────────────────────────────────────────────────────────

def _apply_sale_effects(order, inventory):
    """Deduct inventory & add to client balance for a real sale order."""
    for item in order.get('items', []):
        if item.get('source') == 'stock':
            pid = item.get('product_id')
            qty = float(item.get('quantity', 0))
            inv_item = next((iv for iv in inventory if iv['product_id'] == pid), None)
            if inv_item:
                iidx = find_index_by_id(inventory, inv_item['id'])
                inventory[iidx]['quantity_sold']      = float(inventory[iidx].get('quantity_sold', 0)) + qty
                inventory[iidx]['quantity_remaining'] = float(inventory[iidx].get('quantity_remaining', 0)) - qty
    write_db('inventory', inventory)

    total_sell = float(order.get('total_sell', 0))
    client_id  = order.get('client_id')
    if client_id:
        clients_db = read_db('clients')
        cidx = find_index_by_id(clients_db, client_id)
        if cidx >= 0:
            clients_db[cidx]['total_sales'] = float(clients_db[cidx].get('total_sales', 0)) + total_sell
            clients_db[cidx]['balance']     = float(clients_db[cidx].get('balance', 0)) + total_sell
            write_db('clients', clients_db)

def _reverse_sale_effects(order, inventory):
    """Restore inventory & reverse client balance for a real sale order."""
    for item in order.get('items', []):
        if item.get('source') == 'stock':
            pid = item.get('product_id')
            qty = float(item.get('quantity', 0))
            inv_item = next((iv for iv in inventory if iv['product_id'] == pid), None)
            if inv_item:
                iidx = find_index_by_id(inventory, inv_item['id'])
                inventory[iidx]['quantity_sold']      = max(0, float(inventory[iidx].get('quantity_sold', 0)) - qty)
                inventory[iidx]['quantity_remaining'] = float(inventory[iidx].get('quantity_remaining', 0)) + qty
    write_db('inventory', inventory)

    total_sell = float(order.get('total_sell', 0))
    client_id  = order.get('client_id')
    if client_id:
        clients_db = read_db('clients')
        cidx = find_index_by_id(clients_db, client_id)
        if cidx >= 0:
            clients_db[cidx]['total_sales'] = max(0, float(clients_db[cidx].get('total_sales', 0)) - total_sell)
            clients_db[cidx]['balance']     = float(clients_db[cidx].get('balance', 0)) - total_sell
            write_db('clients', clients_db)

# ── routes ────────────────────────────────────────────────────────────────────

@orders_bp.route('/orders')
@login_required
def index():
    orders  = read_db('orders')
    clients = read_db('clients')
    for o in orders:
        client = next((c for c in clients if c['id'] == o.get('client_id')), None)
        o['client_name'] = client['name'] if client else 'غير محدد'
    orders = sorted(orders, key=lambda x: x.get('created_at', ''), reverse=True)
    return render_template('orders/index.html', orders=orders)


@orders_bp.route('/orders/add', methods=['GET', 'POST'])
@login_required
def add():
    clients   = read_db('clients')
    suppliers = read_db('suppliers')
    products  = read_db('products')
    inventory = read_db('inventory')

    # order_type comes from query param on GET, hidden field on POST
    order_type = request.args.get('type', 'sale')

    if request.method == 'POST':
        order_type = request.form.get('order_type', 'sale')
        orders     = read_db('orders')
        items_raw  = request.form.getlist('product_id')
        order_items = []
        total_cost  = 0
        total_sell  = 0

        for i, pid in enumerate(items_raw):
            qty            = float(request.form.getlist('quantity')[i] or 0)
            purchase_price = float(request.form.getlist('purchase_price')[i] or 0)
            sell_price     = float(request.form.getlist('sell_price')[i] or 0)
            source         = request.form.getlist('source')[i]
            supplier_id    = request.form.getlist('supplier_id')[i]
            product        = find_by_id(products, pid)
            item = {
                'product_id':     pid,
                'product_name':   product['name'] if product else '',
                'supplier_id':    supplier_id,
                'quantity':       qty,
                'purchase_price': purchase_price,
                'sell_price':     sell_price,
                'source':         source
            }
            order_items.append(item)
            total_cost += purchase_price * qty
            total_sell += sell_price     * qty

        profit = total_sell - total_cost
        order  = {
            'id':         get_next_id(orders),
            'order_type': order_type,          # 'quote' or 'sale'
            'client_id':  request.form.get('client_id', '').strip(),
            'status':     'new',
            'items':      order_items,
            'total_cost': round(total_cost, 2),
            'total_sell': round(total_sell, 2),
            'profit':     round(profit, 2),
            'notes':      request.form.get('notes', '').strip(),
            'created_by': session['user']['id'],
            'created_at': now()
        }
        orders.append(order)
        write_db('orders', orders)

        # Only apply real effects for sale orders
        if order_type == 'sale':
            inventory = read_db('inventory')
            # deduct inventory per item (source == stock)
            for i, pid in enumerate(request.form.getlist('product_id')):
                source = request.form.getlist('source')[i]
                if source == 'stock':
                    qty      = float(request.form.getlist('quantity')[i] or 0)
                    inv_item = next((iv for iv in inventory if iv['product_id'] == pid), None)
                    if inv_item:
                        idx2 = find_index_by_id(inventory, inv_item['id'])
                        inventory[idx2]['quantity_sold']      = float(inventory[idx2].get('quantity_sold', 0)) + qty
                        inventory[idx2]['quantity_remaining'] = float(inventory[idx2].get('quantity_remaining', 0)) - qty
            write_db('inventory', inventory)

            clients_db = read_db('clients')
            cidx = find_index_by_id(clients_db, order['client_id'])
            if cidx >= 0:
                clients_db[cidx]['total_sales'] = float(clients_db[cidx].get('total_sales', 0)) + total_sell
                clients_db[cidx]['balance']     = float(clients_db[cidx].get('balance', 0))     + total_sell
                write_db('clients', clients_db)

            flash('تم إنشاء أمر البيع بنجاح ✅', 'success')
        else:
            flash('تم إنشاء طلب عرض السعر بنجاح ✅', 'success')

        return redirect(url_for('orders.view', id=order['id']))

    return render_template('orders/form.html',
                           clients=clients, suppliers=suppliers,
                           products=products, inventory=inventory,
                           action='add', order_type=order_type)


@orders_bp.route('/orders/view/<id>')
@login_required
def view(id):
    orders = read_db('orders')
    order  = find_by_id(orders, id)
    if not order:
        flash('الطلب غير موجود', 'danger')
        return redirect(url_for('orders.index'))
    clients = read_db('clients')
    client  = find_by_id(clients, order.get('client_id'))
    order['client_name'] = client['name'] if client else 'غير محدد'
    order_items = order.get('items', [])
    return render_template('orders/view.html', order=order, order_items=order_items)


@orders_bp.route('/orders/print/<id>')
@login_required
def print_bill(id):
    orders = read_db('orders')
    order  = find_by_id(orders, id)
    if not order:
        flash('الطلب غير موجود', 'danger')
        return redirect(url_for('orders.index'))
    clients = read_db('clients')
    client  = find_by_id(clients, order.get('client_id'))
    order['client_name'] = client['name'] if client else 'غير محدد'
    order_items = order.get('items', [])
    company     = get_company()
    return render_template('orders/print.html',
                           order=order, order_items=order_items, company=company)


@orders_bp.route('/orders/convert/<id>', methods=['POST'])
@login_required
def convert_to_sale(id):
    """Convert a price quote → real sale order."""
    orders = read_db('orders')
    idx    = find_index_by_id(orders, id)
    if idx < 0:
        flash('الطلب غير موجود', 'danger')
        return redirect(url_for('orders.index'))

    order = orders[idx]
    if order.get('order_type') != 'quote':
        flash('هذا الطلب ليس عرض سعر', 'warning')
        return redirect(url_for('orders.view', id=id))

    orders[idx]['order_type'] = 'sale'
    write_db('orders', orders)

    # Apply real effects
    inventory = read_db('inventory')
    _apply_sale_effects(orders[idx], inventory)

    flash('تم تحويل عرض السعر إلى أمر بيع حقيقي ✅', 'success')
    return redirect(url_for('orders.view', id=id))


@orders_bp.route('/orders/status/<id>/<status>', methods=['POST'])
@login_required
def update_status(id, status):
    orders = read_db('orders')
    idx    = find_index_by_id(orders, id)
    if idx >= 0:
        old_status = orders[idx].get('status', '')
        order_type = orders[idx].get('order_type', 'sale')
        orders[idx]['status'] = status
        write_db('orders', orders)

        # Only real sale orders affect inventory / client balance
        if order_type == 'sale':
            if status == 'cancelled' and old_status != 'cancelled':
                inventory = read_db('inventory')
                _reverse_sale_effects(orders[idx], inventory)

            elif old_status == 'cancelled' and status != 'cancelled':
                inventory = read_db('inventory')
                _apply_sale_effects(orders[idx], inventory)

        flash('تم تحديث حالة الطلب ✅', 'success')
    return redirect(url_for('orders.view', id=id))


@orders_bp.route('/orders/delete/<id>', methods=['POST'])
@login_required
def delete(id):
    orders = read_db('orders')
    order  = find_by_id(orders, id)
    if order:
        order_type        = order.get('order_type', 'sale')
        already_cancelled = order.get('status') == 'cancelled'

        # Only reverse for real sale orders that were NOT already cancelled
        if order_type == 'sale' and not already_cancelled:
            inventory = read_db('inventory')
            _reverse_sale_effects(order, inventory)

    orders = [o for o in orders if o['id'] != str(id)]
    write_db('orders', orders)
    flash('تم حذف الطلب بنجاح', 'success')
    return redirect(url_for('orders.index'))