from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.db import read_db, write_db, get_next_id, find_by_id, find_index_by_id
from app.helpers import login_required, now

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/inventory')
@login_required
def index():
    inventory = read_db('inventory')
    products = read_db('products')
    suppliers = read_db('suppliers')
    for item in inventory:
        product = next((p for p in products if p['id'] == item.get('product_id')), None)
        supplier = next((s for s in suppliers if s['id'] == item.get('supplier_id')), None)
        item['product_name'] = product['name'] if product else 'غير محدد'
        item['supplier_name'] = supplier['name'] if supplier else 'غير محدد'
        purchase_price = float(item.get('purchase_price', 0))
        sell_price = float(item.get('sell_price', 0))
        quantity = float(item.get('quantity', 0))
        item['profit_margin'] = round(((sell_price - purchase_price) / purchase_price * 100) if purchase_price > 0 else 0, 2)
        item['total_cost'] = round(purchase_price * quantity, 2)
    return render_template('inventory/index.html', inventory=inventory)

@inventory_bp.route('/inventory/add', methods=['GET', 'POST'])
@login_required
def add():
    products = read_db('products')
    suppliers = read_db('suppliers')
    if request.method == 'POST':
        inventory = read_db('inventory')
        purchase_price = float(request.form.get('purchase_price', 0))
        sell_price = float(request.form.get('sell_price', 0))
        quantity = float(request.form.get('quantity', 0))
        profit_margin = round(((sell_price - purchase_price) / purchase_price * 100) if purchase_price > 0 else 0, 2)
        item = {
            'id': get_next_id(inventory),
            'product_id': request.form.get('product_id', '').strip(),
            'supplier_id': request.form.get('supplier_id', '').strip(),
            'purchase_price': purchase_price,
            'sell_price': sell_price,
            'quantity': quantity,
            'quantity_sold': 0,
            'quantity_remaining': quantity,
            'total_cost': round(purchase_price * quantity, 2),
            'profit_margin': profit_margin,
            'notes': request.form.get('notes', '').strip(),
            'created_at': now()
        }
        inventory.append(item)
        write_db('inventory', inventory)
        flash('تم إضافة المنتج للمخزون بنجاح', 'success')
        return redirect(url_for('inventory.index'))
    return render_template('inventory/form.html', item=None, products=products, suppliers=suppliers, action='add')

@inventory_bp.route('/inventory/edit/<id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    inventory = read_db('inventory')
    products = read_db('products')
    suppliers = read_db('suppliers')
    item = find_by_id(inventory, id)
    if not item:
        flash('العنصر غير موجود', 'danger')
        return redirect(url_for('inventory.index'))
    if request.method == 'POST':
        idx = find_index_by_id(inventory, id)
        purchase_price = float(request.form.get('purchase_price', 0))
        sell_price = float(request.form.get('sell_price', 0))
        quantity = float(request.form.get('quantity', 0))
        sold = float(inventory[idx].get('quantity_sold', 0))
        profit_margin = round(((sell_price - purchase_price) / purchase_price * 100) if purchase_price > 0 else 0, 2)
        inventory[idx]['product_id'] = request.form.get('product_id', '').strip()
        inventory[idx]['supplier_id'] = request.form.get('supplier_id', '').strip()
        inventory[idx]['purchase_price'] = purchase_price
        inventory[idx]['sell_price'] = sell_price
        inventory[idx]['quantity'] = quantity
        inventory[idx]['quantity_remaining'] = quantity - sold
        inventory[idx]['total_cost'] = round(purchase_price * quantity, 2)
        inventory[idx]['profit_margin'] = profit_margin
        inventory[idx]['notes'] = request.form.get('notes', '').strip()
        write_db('inventory', inventory)
        flash('تم تعديل المخزون بنجاح', 'success')
        return redirect(url_for('inventory.index'))
    return render_template('inventory/form.html', item=item, products=products, suppliers=suppliers, action='edit')

@inventory_bp.route('/inventory/delete/<id>', methods=['POST'])
@login_required
def delete(id):
    inventory = read_db('inventory')
    inventory = [i for i in inventory if i['id'] != str(id)]
    write_db('inventory', inventory)
    flash('تم حذف العنصر من المخزون بنجاح', 'success')
    return redirect(url_for('inventory.index'))