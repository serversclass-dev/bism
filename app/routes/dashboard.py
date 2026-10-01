from flask import Blueprint, render_template
from app.db import read_db
from app.helpers import login_required

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def index():
    clients = read_db('clients')
    suppliers = read_db('suppliers')
    products = read_db('products')
    orders = read_db('orders')
    purchases = read_db('purchases')
    payments = read_db('payments')
    inventory = read_db('inventory')

    total_clients = len(clients)
    total_suppliers = len(suppliers)
    total_products = len(products)
    total_orders = len(orders)

    active_orders = [o for o in orders if o.get('status') != 'cancelled']
    total_sales = sum(float(o.get('total_sell', 0)) for o in active_orders)
    total_profit = sum(float(o.get('profit', 0)) for o in active_orders)
    total_purchases = sum(float(p.get('total_amount', 0)) for p in purchases)

    client_debt = sum(float(c.get('balance', 0)) for c in clients)
    supplier_debt = sum(float(s.get('balance', 0)) for s in suppliers)

    recent_orders = sorted(orders, key=lambda x: x.get('created_at', ''), reverse=True)[:5]

    for o in recent_orders:
        client = next((c for c in clients if c['id'] == o.get('client_id')), None)
        o['client_name'] = client['name'] if client else 'غير معروف'

    stats = {
        'total_clients': total_clients,
        'total_suppliers': total_suppliers,
        'total_products': total_products,
        'total_orders': total_orders,
        'total_sales': total_sales,
        'total_profit': total_profit,
        'total_purchases': total_purchases,
        'client_debt': client_debt,
        'supplier_debt': supplier_debt,
    }

    return render_template('dashboard/index.html', stats=stats, recent_orders=recent_orders, clients=clients)