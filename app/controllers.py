import json, os
from flask import render_template, redirect, url_for, flash, jsonify, request, abort
from app import db, cache, user_create_secret_key
from .forms import LoginForm, CreateUserForm, EditUserForm
from .models import User, Statement
from flask_login import login_user, logout_user, login_required, current_user
from .XeroController import XeroContactRequests, XeroInvoiceRequests
from .BukkuController import BukkuContactRequests, BukkuInvoiceRequests
from functools import wraps
from uuid import uuid4
from datetime import datetime
from marshmallow import Schema, fields, ValidationError, validate, validates_schema

# Admin requirement decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "admin":
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

# Default index load
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login_page'))

# Login page   
def login_page():

    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if request.method == "POST" and form.validate(): 
        attempted_user = User.query.filter_by(username=form.username.data).first()
        if attempted_user and attempted_user.check_password(form.password.data):
            login_user(attempted_user)
            next_page = request.args.get('next')
            if not next_page:
                return redirect(url_for('index'))
            return redirect(next_page)
        else:
            flash('Your username or password is incorrect.')
            return redirect(url_for('login_page'))
        
    return render_template('login.html', form = form)

# API - retrieve all users
@login_required
@admin_required    
def users_data():
    users = User.query.all()
    user_list = []
    for user in users:
        user_list.append({
            'id': user.id,
            'username': user.username,
            'role': user.role,
        })
    return jsonify(user_list)

# Marshmallow Schema - For user creation API validation
class UserSchema(Schema):
    username = fields.Str(required=True)
    password = fields.Str(required=True)
    confirm_password = fields.Str(required=True)
    role = fields.Str(required=True, validate=validate.OneOf(['admin', 'normal']))
    secret_key = fields.Str(required=True)

    @validates_schema
    def validate_passwords(self, data, **kwargs):
        if data.get('password') != data.get('confirm_password'):
            raise ValidationError("Passwords must match", "confirm_password")
        
    @validates_schema
    def validate_secret_key(self, data, **kwargs):
        if data.get('secret_key') != user_create_secret_key:
            raise ValidationError("Wrong entry", "secret_key")

user_schema = UserSchema()

# API - Add user (For first admin user creation)
def users_create():

    try:
        data = user_schema.load(request.get_json())
        username = data['username']
        password = data['password']
        role = data['role']

        if User.query.filter_by(username=username).first():
            return jsonify({"errors": {"username": ["Username already exists"]}}), 400

        new_user = User(username=username, password_hash=password, role=role)
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"user_id": new_user.id, "username": new_user.username, "role": new_user.role}), 201
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400

# API - delete user
@login_required
@admin_required
def users_delete():
    if request.method == 'DELETE':
        data = request.get_json()
        deleted_count = User.query.filter(User.id.in_(data['ids'])).delete(synchronize_session='fetch')
        db.session.commit()

        if deleted_count > 0:
            return jsonify({'success': f"{deleted_count} user(s) deleted."}), 200
        else:
            return jsonify({'message': "No users found with the provided IDs."}), 200

# Dashboard page
@login_required
def dashboard_page():
    return render_template('dashboard.html')

# API - Retrieve Contacts data from Xero, Bukku
@login_required
def contacts_data():

    bypass_cache = request.args.get('bypass_cache', 'false').lower() == 'true'
    
    if bypass_cache:

        response = XeroContactRequests()
        # response.append(BukkuContactRequests())

        cache.set('contacts', response, timeout=1800)

        return response
    
    else:

        cached_response = cache.get('contacts')

        if cached_response:
            
            return cached_response
        
        else:

            response = XeroContactRequests()
            # response.append(BukkuContactRequests())
            
            cache.set('contacts', response, timeout=1800)

            return response
        
    # Old method - Calling the contacts API internally

    # get_url = url_for('api.Xero_Contacts', _external=True)
    # response = requests.get(get_url)
    # json_response = response.json()

    # get_url = url_for('api.Bukku_Contacts', _external=True)
    # response = requests.get(get_url)
    # bukku_response = response.json()
    # json_response.append(bukku_response)

    # return json_response

# Redirect to statement page
@login_required
def redirect_statement():

    data = request.get_json()

    draft_inclusion = request.args.get('draft')

    if data:

        # Old method - Writting the data into a temp file

        # dt = datetime.now()

        # ts = int(str(datetime.timestamp(dt)).replace('.', ''))

        # filename = f'temp_{uuid4()}_{ts}.json'
        # filepath = os.path.join(os.path.abspath(os.getcwd()), "app", "temp", filename)

        # directory = os.path.dirname(filepath)
        # if not os.path.exists(directory):
        #     os.makedirs(directory, exist_ok=True)

        # try:
        #     with open(filepath, 'w') as f:
        #         json.dump(data, f)
        
        # except IOError as e:
        #     return jsonify({'error': f'Error saving data to temporary file: {e}'}), 500
        
        description_dict = {}

        Xero_API = False
        Bukku_API = False

        for item in data:
            contact_name = item.get("ContactName")
            tenant = item.get("Tenant")
            if contact_name and tenant:

                tenant_name = ""

                if tenant == "Macross Consultancy (M) Sdn Bhd":

                    Xero_API = True

                    tenant_name = "Macross"

                elif tenant == "Macross Consultancy Pte Ltd":

                    Xero_API = True

                    tenant_name = "Macross SG"

                elif tenant == "C.T & Co (Ekoflora Branch)":

                    Xero_API = True

                    tenant_name = "C.T & Co"

                elif tenant == "Co Maker Sdn Bhd":

                    Xero_API = True

                    tenant_name = "Co Maker"

                elif tenant == "Cheng & Associates Secretarial PLT":

                    # Bukku_API = True
                    Xero_API = True

                    tenant_name = "Cheng & Associates"

                if tenant_name:
                    if tenant_name not in description_dict:
                        description_dict[tenant_name] = []
                    description_dict[tenant_name].append(contact_name)

        extracted_data = []

        if Xero_API == True:

            xero_response = XeroInvoiceRequests(data, draft_inclusion)

            # Old method - Calling the xero invoices API internally

            # get_url = url_for('api.Xero_Invoices', filename=filename, _external=True)
            # response = requests.get(get_url)
            # json_response = response.json()

            if xero_response:
                for item in xero_response:
                    extracted_item = {}
                    extracted_invoices = []
                    if item.get("Invoices") != []:
                        for invoice in item["Invoices"]:
                            invoice_info = {
                                "AmountCredited": invoice.get("AmountCredited"),
                                "AmountDue": invoice.get("AmountDue"),
                                "AmountPaid": invoice.get("AmountPaid"),
                                "Contact": {
                                    "ContactID": invoice.get("Contact", {}).get("ContactID"),
                                    "Name": invoice.get("Contact", {}).get("Name")
                                },
                                "InvoiceID": invoice.get("InvoiceID"),
                                "InvoiceNumber": invoice.get("InvoiceNumber"),
                                "LineItems": [],
                                "Status": invoice.get("Status")
                            }
                            for line_item in invoice.get("LineItems", []):
                                line_item_info = {
                                    "AccountCode": line_item.get("AccountCode"),
                                    "AccountID": line_item.get("AccountID"),
                                    "Description": line_item.get("Description"),
                                    "Item": {
                                        "Code": line_item.get("Item", {}).get("Code"),
                                        "ItemID": line_item.get("Item", {}).get("ItemID"),
                                        "Name": line_item.get("Item", {}).get("Name")
                                    },
                                    "ItemCode": line_item.get("ItemCode"),
                                    "LineAmount": line_item.get("LineAmount"),
                                    "LineItemID": line_item.get("LineItemID"),
                                    "Quantity": line_item.get("Quantity"),
                                    "TaxAmount": line_item.get("TaxAmount"),
                                    "TaxType": line_item.get("TaxType"),
                                    "Tracking": line_item.get("Tracking")
                                }
                                invoice_info["LineItems"].append(line_item_info)
                            extracted_invoices.append(invoice_info)
                        extracted_item["Invoices"] = extracted_invoices
                        if "Tenant" in item:
                            extracted_item["Tenant"] = item["Tenant"]
                        else:
                            extracted_item["Tenant"] = None # Or some other default value
                        extracted_data.append(extracted_item)

            else:

                return jsonify({'status': 'fail', 'error': 'Failed to retrieve data from Xero API.'}), 500

        if Bukku_API == True:

            bukku_response = BukkuInvoiceRequests(data)

            if bukku_response:
                for item in bukku_response:
                    extracted_item = {}
                    extracted_invoices = []
                    if item.get("transactions") != []:
                        for invoice in item["transactions"]:
                            invoice_info = {
                                "AmountDue": invoice.get("balance"),
                                "Contact": {
                                    "ContactID": invoice.get("contact_id"),
                                    "Name": invoice.get("contact_name")
                                },
                                "InvoiceID": invoice.get("id"),
                                "InvoiceNumber": invoice.get("number"),
                                "LineItems": []
                            }
                            line_item_info = {
                                "Description": invoice.get("description"),
                            }
                            invoice_info["LineItems"].append(line_item_info)
                            extracted_invoices.append(invoice_info)
                        extracted_item["Invoices"] = extracted_invoices
                        if "Tenant" in item:
                            extracted_item["Tenant"] = item["Tenant"]
                        else:
                            extracted_item["Tenant"] = None # Or some other default value
                        extracted_data.append(extracted_item)

            else:

                return jsonify({'status': 'fail', 'error': 'Failed to retrieve data from Bukku API.'}), 500

        dt = datetime.now()

        ts = int(str(datetime.timestamp(dt)).replace('.', ''))

        filename = f'statement_{uuid4()}_{ts}.json'
        filepath = os.path.join(os.path.abspath(os.getcwd()), "app", "data", f'{dt.year}', dt.strftime("%b"), filename)

        directory = os.path.dirname(filepath)
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        try:
            with open(filepath, 'w') as f:

                json.dump(extracted_data, f)

        except FileNotFoundError as e:
            
            print(e)

            return jsonify({'error': f'Error saving data to data file: {e}'}), 500
        
        except IOError as e:
            
            print(e)

            return jsonify({'error': f'Error saving data to data file: {e}'}), 500
        
        except Exception as e:

            print(e)
            return jsonify({'error': f'Error saving data to data file: {e}'}), 500
        
        new_statement = Statement(
                description=json.dumps(description_dict),
                filepath = filepath,
                user_id = current_user.id
            )
        
        db.session.add(new_statement)
        db.session.commit()

        # Redirect to the GET route for displaying the statement, passing the filename
        return jsonify({'redirect_url': url_for('statement_page', statement_id = new_statement.id)}), 200
    
    else:

        return jsonify({'status': 'fail', 'error': 'Failed to retrieve data from contact list.'}), 500
        
# Statement page
@login_required
def statement_page():

    statement_id = request.args.get('statement_id')

    return render_template('statement.html', statement_id = statement_id)

# API - Retrieve a specific statement's data
@login_required
def statement_data():

    statement = Statement.query.get(request.args.get('statement_id'))

    filepath = statement.filepath

    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        
    except FileNotFoundError:
        return jsonify({'status': 'fail', 'error': 'Selected data file not found, please generate the statement again.'}), 500
    except json.JSONDecodeError:
        return jsonify({'status': 'fail', 'error': 'Error decoding data file.'}), 500
    except IOError as e:
        return jsonify({'status': 'fail', 'error': 'Error reading data file.'}), 500
    
    if data:

        return data
    
    else:

        return jsonify([])
        # return jsonify({'status': 'fail', 'error': 'Failed to retrieve data.'}), 500

# History page
@login_required
def history_page():
    return render_template('history.html')

# API - retrieve all generated statements
@login_required    
def history_data():
    histories = Statement.query.all()
    history_list = []
    for history in histories:
        description_string = ""
        try:
            description_dict = json.loads(history.description)
            description_list = []
            for tenant, contacts in description_dict.items():
                description_list.append(f"{tenant} - {', '.join(contacts)}")
            description_string = "<br><br>".join(description_list)
        except json.JSONDecodeError:
            description_string = "Error decoding description data"
        except TypeError:
            description_string = "Invalid description data format"

        history_list.append({
            'id': history.id,
            'description': description_string,
            'filepath': history.filepath,
            'created_at': history.created_at,
            'created_by': history.user.username
        })
    return jsonify(history_list)

# Users page
@login_required
@admin_required
def user_page():
    form = CreateUserForm()
    if request.method == "POST" and form.validate(): 
        new_user = User(username=form.username.data,
                        password_hash=form.password.data,
                        role=form.role.data)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('user_page'))      

    return render_template('users.html', form = form)

# Users editing page
@login_required
@admin_required
def user_edit_page():

    user_id = request.args.get('user_id')

    user = User.query.get(user_id)

    if user:

        form = EditUserForm()

        form.user_id.data = user.id

        if request.method == "POST" and form.validate(): 

            # To check if the fields are empty
            username_input_provided = form.username.data is not None and form.username.data.strip() != '' 
            password_input_provided = form.password.data is not None and form.password.data != ''
            role_input_provided = form.role.data is not None and form.role.data != ''

            changes_made = False

            if not username_input_provided and \
                not password_input_provided and \
                not role_input_provided:
                    
                    flash('All fields are empty.', 'warning')

                    return render_template('edit_user.html', user=user, form=form)
            
            if username_input_provided:
                new_username = form.username.data.strip() # Get the stripped value for comparison
                if user.username != new_username:
                    user.username = new_username
                    changes_made = True

            if password_input_provided:
                # Hash the new password before storing it
                user.password_hash = form.password.data
                changes_made = True
            
            if role_input_provided:
                # Only update if a new role was explicitly selected and it's different from current
                if user.role != form.role.data:
                    user.role = form.role.data
                    changes_made = True
            
            # If no actual changes were detected for valid inputs
            if not changes_made:
                flash('No changes were made to the user.', 'info')
                return render_template('edit_user.html', user=user, form=form)

            try:
                db.session.commit()
                flash(f'User "{user.username}" updated successfully.', 'success')

                return redirect(url_for('user_page'))
            
            except Exception as e:
                db.session.rollback() # Rollback changes if commit fails

                flash(f'Error updating user: {e}', 'danger')
                # Log the error for detailed debugging
                print(f"Database error updating user {user.username}: {e}") 
                # Re-render the form with existing data and any validation errors (though form.validate() passed)
                return render_template('edit_user.html', user=user, form=form)
        
        else:

            return render_template('edit_user.html', user = user, form = form)
        
@login_required
def account_edit_page():

    account_id = request.args.get('account_id')

    if int(account_id) != current_user.id:
        abort(403)

    user = User.query.get(account_id)

    if user:

        form = EditUserForm()

        if request.method == "POST" and form.validate(): 

            # To check if the fields are empty
            password_input_provided = form.password.data is not None and form.password.data != ''

            changes_made = False
                    
            if password_input_provided:
                # Hash the new password before storing it
                user.password_hash = form.password.data
                changes_made = True

            else:
                flash('All fields are empty.', 'warning')

                return render_template('edit_account.html', user=user, form=form)
            
            # If no actual changes were detected for valid inputs
            if not changes_made:
                flash('No changes were made to the user.', 'info')
                return render_template('edit_account.html', user=user, form=form)

            try:
                db.session.commit()
                flash(f'Update has been made successfully.', 'success')

                return redirect(url_for('account_edit_page'), account_id=account_id, user=user, form=form)

            except Exception as e:
                db.session.rollback() # Rollback changes if commit fails

                flash(f'Error updating user: {e}', 'danger')
                # Log the error for detailed debugging
                print(f"Database error updating user {user.username}: {e}") 
                # Re-render the form with existing data and any validation errors (though form.validate() passed)
                return render_template('edit_account.html', user=user, form=form)
        
        else:

            return render_template('edit_account.html', user = user, form = form)

# Logout user
@login_required
def logout_page():
    logout_user()
    return redirect(url_for('index'))
