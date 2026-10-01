from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.db import read_db, write_db, get_next_id, find_by_id, find_index_by_id
from app.helpers import login_required, now

purchases_bp = Blueprint('purchases', __name__)

def get_company():
    settings = read_db('settings')
    return settings[0] if settings else {'name': 'BIMS', 'logo': '', 'address': '', 'phone': '', 'email': '', 'tax_number': ''}

@purchases_bp.route('/purchases')
@login_required
def index():
    purchases = read_db('purchases')
    suppliers = read_db('suppliers')
    for p in purchases:
        supplier = next((s for s in suppliers if s['id'] == p.get('supplier_id')), None)
        p['supplier_name'] = supplier['name'] if supplier else 'غير محدد'
    purchases = sorted(purchases, key=lambda x: x.get('created_at', ''), reverse=True)
    return render_template('purchases/index.html', purchases=purchases)

@purchases_bp.route('/purchases/add', methods=['GET', 'POST'])
@login_required
def add():
    suppliers = read_db('suppliers')
    products = read_db('products')
    if request.method == 'POST':
        purchases = read_db('purchases')
        inventory = read_db('inventory')
        items_raw = request.form.getlist('product_id')
        quantities_raw = request.form.getlist('quantity')
        prices_raw = request.form.getlist('price')
        purchase_items = []
        total_amount = 0

        for i, pid in enumerate(items_raw):
            if not pid:
                continue
            qty = float(quantities_raw[i] if i < len(quantities_raw) else 0 or 0)
            price = float(prices_raw[i] if i < len(prices_raw) else 0 or 0)
            product = find_by_id(products, pid)
            item_total = round(qty * price, 2)
            purchase_items.append({
                'product_id': pid,
                'product_name': product['name'] if product else '',
                'quantity': qty,
                'price': price,
                'total': item_total
            })
            total_amount += qty * price

            # AUTO ADD / UPDATE INVENTORY
            supplier_id = request.form.get('supplier_id', '').strip()
            existing = next((iv for iv in inventory
                             if iv.get('product_id') == pid
                             and iv.get('supplier_id') == supplier_id), None)
            if existing:
                idx = find_index_by_id(inventory, existing['id'])
                new_qty = float(inventory[idx].get('quantity', 0)) + qty
                new_remaining = float(inventory[idx].get('quantity_remaining', 0)) + qty
                new_total_cost = round(price * new_qty, 2)
                sell_price = float(inventory[idx].get('sell_price', price))
                inventory[idx]['quantity'] = new_qty
                inventory[idx]['quantity_remaining'] = new_remaining
                inventory[idx]['total_cost'] = new_total_cost
                inventory[idx]['purchase_price'] = price
                inventory[idx]['profit_margin'] = round(
                    ((sell_price - price) / price * 100) if price > 0 else 0, 2)
            else:
                sell_price = float(product['default_sell_price']) if product and product.get('default_sell_price') else price
                profit_margin = round(((sell_price - price) / price * 100) if price > 0 else 0, 2)
                inventory.append({
                    'id': get_next_id(inventory),
                    'product_id': pid,
                    'supplier_id': supplier_id,
                    'purchase_price': price,
                    'sell_price': sell_price,
                    'quantity': qty,
                    'quantity_sold': 0,
                    'quantity_remaining': qty,
                    'total_cost': round(price * qty, 2),
                    'profit_margin': profit_margin,
                    'notes': '',
                    'created_at': now()
                })

        write_db('inventory', inventory)

        paid_amount = float(request.form.get('paid_amount', 0))
        remaining = total_amount - paid_amount

        purchase = {
            'id': get_next_id(purchases),
            'supplier_id': request.form.get('supplier_id', '').strip(),
            'items': purchase_items,
            'total_amount': round(total_amount, 2),
            'paid_amount': round(paid_amount, 2),
            'remaining': round(remaining, 2),
            'notes': request.form.get('notes', '').strip(),
            'created_by': session['user']['id'],
            'created_at': now()
        }
        purchases.append(purchase)
        write_db('purchases', purchases)

        suppliers_db = read_db('suppliers')
        sidx = find_index_by_id(suppliers_db, purchase['supplier_id'])
        if sidx >= 0:
            suppliers_db[sidx]['total_purchases'] = float(suppliers_db[sidx].get('total_purchases', 0)) + total_amount
            suppliers_db[sidx]['total_paid'] = float(suppliers_db[sidx].get('total_paid', 0)) + paid_amount
            suppliers_db[sidx]['balance'] = float(suppliers_db[sidx].get('balance', 0)) + remaining
            write_db('suppliers', suppliers_db)

        flash('تم تسجيل المشتريات وتحديث المخزون تلقائياً ✅', 'success')
        return redirect(url_for('purchases.view', id=purchase['id']))
    return render_template('purchases/form.html', suppliers=suppliers, products=products, action='add')

@purchases_bp.route('/purchases/edit/<id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    purchases = read_db('purchases')
    suppliers = read_db('suppliers')
    products = read_db('products')
    purchase = find_by_id(purchases, id)
    if not purchase:
        flash('عملية الشراء غير موجودة', 'danger')
        return redirect(url_for('purchases.index'))
    if request.method == 'POST':
        inventory = read_db('inventory')
        items_raw = request.form.getlist('product_id')
        quantities_raw = request.form.getlist('quantity')
        prices_raw = request.form.getlist('price')
        purchase_items = []
        total_amount = 0

        for i, pid in enumerate(items_raw):
            if not pid:
                continue
            qty = float(quantities_raw[i] if i < len(quantities_raw) else 0 or 0)
            price = float(prices_raw[i] if i < len(prices_raw) else 0 or 0)
            product = find_by_id(products, pid)
            item_total = round(qty * price, 2)
            purchase_items.append({
                'product_id': pid,
                'product_name': product['name'] if product else '',
                'quantity': qty,
                'price': price,
                'total': item_total
            })
            total_amount += qty * price

        paid_amount = float(request.form.get('paid_amount', 0))
        remaining = total_amount - paid_amount

        idx = find_index_by_id(purchases, id)
        purchases[idx]['supplier_id'] = request.form.get('supplier_id', '').strip()
        purchases[idx]['items'] = purchase_items
        purchases[idx]['total_amount'] = round(total_amount, 2)
        purchases[idx]['paid_amount'] = round(paid_amount, 2)
        purchases[idx]['remaining'] = round(remaining, 2)
        purchases[idx]['notes'] = request.form.get('notes', '').strip()
        write_db('purchases', purchases)
        flash('تم تعديل عملية الشراء بنجاح ✅', 'success')
        return redirect(url_for('purchases.view', id=id))
    return render_template('purchases/form.html', suppliers=suppliers, products=products,
                           action='edit', purchase=purchase)

@purchases_bp.route('/purchases/view/<id>')
@login_required
def view(id):
    purchases = read_db('purchases')
    purchase = find_by_id(purchases, id)
    if not purchase:
        flash('عملية الشراء غير موجودة', 'danger')
        return redirect(url_for('purchases.index'))
    suppliers = read_db('suppliers')
    supplier = find_by_id(suppliers, purchase.get('supplier_id'))
    purchase['supplier_name'] = supplier['name'] if supplier else 'غير محدد'
    purchase_items = purchase.get('items', [])
    return render_template('purchases/view.html', purchase=purchase, purchase_items=purchase_items)

@purchases_bp.route('/purchases/print/<id>')
@login_required
def print_bill(id):
    purchases = read_db('purchases')
    purchase = find_by_id(purchases, id)
    if not purchase:
        flash('عملية الشراء غير موجودة', 'danger')
        return redirect(url_for('purchases.index'))
    suppliers = read_db('suppliers')
    supplier = find_by_id(suppliers, purchase.get('supplier_id'))
    purchase['supplier_name'] = supplier['name'] if supplier else 'غير محدد'
    purchase_items = purchase.get('items', [])
    company = get_company()
    return render_template('purchases/print.html', purchase=purchase,
                           purchase_items=purchase_items, company=company)

@purchases_bp.route('/purchases/update_status/<id>/<status>', methods=['POST'])
@login_required
def update_status(id, status):
    purchases = read_db('purchases')
    idx = find_index_by_id(purchases, id)
    if idx >= 0:
        purchases[idx]['status'] = status
        write_db('purchases', purchases)
        flash('تم تحديث حالة الطلب بنجاح ✅', 'success')
    else:
        flash('عملية الشراء غير موجودة', 'danger')
    return redirect(url_for('purchases.index'))

@purchases_bp.route('/purchases/delete/<id>', methods=['POST'])
@login_required
def delete(id):
    purchases = read_db('purchases')
    purchases = [p for p in purchases if p['id'] != str(id)]
    write_db('purchases', purchases)
    flash('تم حذف عملية الشراء بنجاح', 'success')
    return redirect(url_for('purchases.index'))