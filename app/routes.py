from flask import Blueprint
from app import app
from .controllers import index, dashboard_page, contacts_data, user_page, user_edit_page, login_page, logout_page, account_edit_page, users_data, users_create, users_delete, redirect_statement, statement_page, statement_data, history_page, history_data
from .XeroController import XeroContactRequests, XeroInvoiceRequests, XeroDownloadInvoice
from .BukkuController import BukkuContactRequests

app.add_url_rule('/', view_func=index, methods=['GET'], endpoint='index')
app.add_url_rule('/login', view_func=login_page, methods=['GET', 'POST'], endpoint='login_page')
app.add_url_rule('/logout', view_func=logout_page, methods=['GET', 'POST'], endpoint='logout_page')
app.add_url_rule('/account/edit', view_func=account_edit_page, methods=['GET', 'POST'], endpoint='account_edit_page')
app.add_url_rule('/dashboard', view_func=dashboard_page, methods=['GET'], endpoint='dashboard')
app.add_url_rule('/redirect_statement', view_func=redirect_statement, methods=['POST'], endpoint='redirect_statement')
app.add_url_rule('/statement', view_func=statement_page, methods=['GET'], endpoint='statement_page')
app.add_url_rule('/history', view_func=history_page, methods=['GET'], endpoint='history_page')

app.add_url_rule('/users', view_func=user_page, methods=['GET', 'POST'], endpoint='user_page')
app.add_url_rule('/users/edit', view_func=user_edit_page, methods=['GET', 'POST'], endpoint='user_edit_page')

api_bp = Blueprint('api', __name__, url_prefix='/api')
api_bp.add_url_rule('/users', view_func=users_data, methods=['GET'], endpoint='users')
api_bp.add_url_rule('/users/create', view_func=users_create, methods=['POST'], endpoint='users_create')
api_bp.add_url_rule('/users/delete', view_func=users_delete, methods=['DELETE'], endpoint='users_delete')
api_bp.add_url_rule('/contacts', view_func=contacts_data, methods=['GET'], endpoint='contacts')
api_bp.add_url_rule('/history', view_func=history_data, methods=['GET'], endpoint='history')
api_bp.add_url_rule('/statement', view_func=statement_data, methods=['GET'], endpoint='statement')
api_bp.add_url_rule('/xero/contacts', view_func=XeroContactRequests, methods=['GET'], endpoint='Xero_Contacts')
# api_bp.add_url_rule('/xero/invoices', view_func=XeroInvoiceRequests, methods=['GET'], endpoint='Xero_Invoices')
api_bp.add_url_rule('/xero/invoices/pdf/<tenant>/<invoice_id>', view_func=XeroDownloadInvoice, methods=['GET'], endpoint='Xero_Invoices_PDF')
api_bp.add_url_rule('/bukku/contacts', view_func=BukkuContactRequests, methods=['GET'], endpoint='Bukku_Contacts')








