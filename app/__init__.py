from flask import Flask, session
from config import Config
from app.db import read_db

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    @app.context_processor
    def inject_company():
        settings = read_db('settings')
        company = settings[0] if settings else {}
        currency = company.get('currency', 'د.ل')
        return dict(company=company, currency=currency)

    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.clients import clients_bp
    from app.routes.suppliers import suppliers_bp
    from app.routes.products import products_bp
    from app.routes.inventory import inventory_bp
    from app.routes.orders import orders_bp
    from app.routes.purchases import purchases_bp
    from app.routes.payments import payments_bp
    from app.routes.settings import settings_bp
    from app.routes.users import users_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(clients_bp)
    app.register_blueprint(suppliers_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(purchases_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(users_bp)

    # ── GitHub Backup ──────────────────────────────────────────────
    from app.github_backup import restore_from_github, start_backup_scheduler
    with app.app_context():
        restore_from_github()      # pull data from GitHub on first run
    start_backup_scheduler()       # auto-backup every 1 hour in background

    return app