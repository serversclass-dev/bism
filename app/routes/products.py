from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.db import read_db, write_db, get_next_id, find_by_id, find_index_by_id
from app.helpers import login_required, now

products_bp = Blueprint('products', __name__)

@products_bp.route('/products')
@login_required
def index():
    products = read_db('products')
    return render_template('products/index.html', products=products)

@products_bp.route('/products/add', methods=['GET', 'POST'])
@login_required
def add():
    suppliers = read_db('suppliers')
    products = read_db('products')
    # collect unique categories from existing products
    categories = sorted(set(p['category'] for p in products if p.get('category')))
    units = sorted(set(p['unit'] for p in products if p.get('unit')))
    if request.method == 'POST':
        product = {
            'id': get_next_id(products),
            'name': request.form.get('name', '').strip(),
            'category': request.form.get('category', '').strip(),
            'unit': request.form.get('unit', '').strip(),
            'description': request.form.get('description', '').strip(),
            'supplier_id': request.form.get('supplier_id', '').strip(),
            'default_purchase_price': float(request.form.get('default_purchase_price', 0)),
            'default_sell_price': float(request.form.get('default_sell_price', 0)),
            'created_at': now()
        }
        products.append(product)
        write_db('products', products)
        flash('تم إضافة المنتج بنجاح ✅', 'success')
        return redirect(url_for('products.add'))
    return render_template('products/form.html', product=None, suppliers=suppliers,
                           categories=categories, units=units, action='add')

@products_bp.route('/products/edit/<id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    products = read_db('products')
    suppliers = read_db('suppliers')
    categories = sorted(set(p['category'] for p in products if p.get('category')))
    units = sorted(set(p['unit'] for p in products if p.get('unit')))
    product = find_by_id(products, id)
    if not product:
        flash('المنتج غير موجود', 'danger')
        return redirect(url_for('products.index'))
    if request.method == 'POST':
        idx = find_index_by_id(products, id)
        products[idx]['name'] = request.form.get('name', '').strip()
        products[idx]['category'] = request.form.get('category', '').strip()
        products[idx]['unit'] = request.form.get('unit', '').strip()
        products[idx]['description'] = request.form.get('description', '').strip()
        products[idx]['supplier_id'] = request.form.get('supplier_id', '').strip()
        products[idx]['default_purchase_price'] = float(request.form.get('default_purchase_price', 0))
        products[idx]['default_sell_price'] = float(request.form.get('default_sell_price', 0))
        write_db('products', products)
        flash('تم تعديل المنتج بنجاح ✅', 'success')
        return redirect(url_for('products.index'))
    return render_template('products/form.html', product=product, suppliers=suppliers,
                           categories=categories, units=units, action='edit')

@products_bp.route('/products/delete/<id>', methods=['POST'])
@login_required
def delete(id):
    products = read_db('products')
    products = [p for p in products if p['id'] != str(id)]
    write_db('products', products)
    flash('تم حذف المنتج بنجاح', 'success')
    return redirect(url_for('products.index'))