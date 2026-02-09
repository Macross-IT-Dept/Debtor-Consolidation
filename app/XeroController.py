import requests, base64, os, time
from flask import request, jsonify, make_response
from . import xero_client_id, xero_client_secret, redis_client

b64_id_secret = base64.b64encode(bytes(xero_client_id + ':' + xero_client_secret, 'utf-8')).decode('utf-8')
token_filepath = os.path.join(os.path.abspath(os.getcwd()), 'app', 'refresh_token', 'refresh_token.txt')

# To retrieve users' IP Address
def get_client_ip():

    # If user used proxy
    if 'X-Forwarded-For' in request.headers:
        return request.headers['X-Forwarded-For'].split(',')[0].strip()
    return request.remote_addr # Fallback if no proxy is used

# Sliding Window API Rate Limit (Decorator) - For invoice download API
def sliding_window_rate_limit(limit=15, window=60):
    def decorator(f):
        def wrapper(*args, **kwargs):
            ip = get_client_ip()
            now = time.time() + 1e-6 # 1 Microsecond
            key = f"ratelimit:{ip}:logs"
            window_start = now - window
            
            # Remove outdated timestamps
            redis_client.zremrangebyscore(key, '-inf', f'({window_start}')
            
            # Get current count
            current_count = redis_client.zcount(key, f'({window_start}', now)
            if current_count >= limit:
                return jsonify(error="Invoice download rate limit exceeded, please try again after a while."), 429
                
            # Add new request timestamp
            redis_client.zadd(key, {now: now})
            redis_client.expire(key, window)
            
            return f(*args, **kwargs)
        return wrapper
    return decorator

# Xero API - Retrieve Tenants
def XeroTenants(access_token):
    connections_url = 'https://api.xero.com/connections'
    response = requests.get(connections_url,
                           headers = {
                               'Authorization': 'Bearer ' + access_token,
                               'Content-Type': 'application/json'
                           })
    json_response = response.json()
    # print(json_response)
    
    Macross = None
    Macross_SG = None
    CoMaker = None
    CT_Co = None
    ChengAssociates = None
    Mea = None
    Macross_Holding = None
    Macross_TA = None

    for tenant in json_response:
        if tenant['tenantName'] == 'Macross Consultancy (M) Sdn Bhd':
            Macross = tenant
        elif tenant['tenantName'] == 'Macross Consultancy Pte Ltd':
            Macross_SG = tenant
        elif tenant['tenantName'] == 'Co Maker Sdn Bhd':
            CoMaker = tenant
        elif tenant['tenantName'] == 'C.T & Co (Ekoflora Branch)':
            CT_Co = tenant
        elif tenant['tenantName'] == 'Cheng & Associates Secretarial PLT':
            ChengAssociates = tenant
        elif tenant['tenantName'] == 'MEA | Macross Entrepreneurs Academy Sdn Bhd':
            Mea = tenant
        elif tenant['tenantName'] == 'MH | Macross Holding Sdn Bhd':
            Macross_Holding = tenant
        elif tenant['tenantName'] == 'MTA | Macross T&A Sdn Bhd':
            Macross_TA = tenant

    return {"Macross": Macross, "Macross SG": Macross_SG, "Co Maker": CoMaker, "C.T & Co": CT_Co, "Cheng & Associates": ChengAssociates, "MEA": Mea, "Macross Holding": Macross_Holding, "Macross T&A": Macross_TA}

# Xero API - Refresh Auth Token
def XeroRefreshToken(refresh_token):
    token_refresh_url = 'https://identity.xero.com/connect/token'
    response = requests.post(token_refresh_url,
                            headers = {
                                'Authorization' : 'Basic ' + b64_id_secret,
                                'Content-Type': 'application/x-www-form-urlencoded'
                            },
                            data = {
                                'grant_type' : 'refresh_token',
                                'refresh_token' : f"{refresh_token}"
                            })
    json_response = response.json()
    # print(json_response)
    
    new_refresh_token = json_response['refresh_token']
    rt_file = open(token_filepath, 'w')
    rt_file.write(new_refresh_token)
    rt_file.close()
    
    return [json_response['access_token'], json_response['refresh_token']]

# Xero API - Retrieve Contacts
def XeroContactRequests():
    
    with open(token_filepath, 'r') as f:
        old_refresh_token = f.read()

    new_tokens = XeroRefreshToken(old_refresh_token)
    xero_tenant= XeroTenants(new_tokens[0])

    session = requests.Session()
    session.headers.update({
        'Authorization': f'Bearer {new_tokens[0]}',
        'Accept': 'application/json'
    })
    
    get_url = 'https://api.xero.com/api.xro/2.0/Contacts?where=IsCustomer=true'
    final_response = []

    for key in xero_tenant:

        session.headers.update({'Xero-tenant-id': xero_tenant[key]['tenantId']})
        response = session.get(get_url)
        
        json_response = response.json()
        json_response["Tenant"] = xero_tenant[key]['tenantName']
        final_response.append(json_response)

    return final_response

# # Xero API - Retrieve Contacts
# def XeroContactGroupRequests():

#     with open(token_filepath, 'r') as f:
#         old_refresh_token = f.read()

#     new_tokens = XeroRefreshToken(old_refresh_token)
#     xero_tenant= XeroTenants(new_tokens[0])

#     get_url = 'https://api.xero.com/api.xro/2.0/ContactGroups'
#     final_response = []

#     for key in xero_tenant:
#         response = requests.get(get_url,
#                             headers = {
#                                 'Authorization': 'Bearer ' + new_tokens[0],
#                                 'Xero-tenant-id': xero_tenant[key]['tenantId'],
#                                 'Accept': 'application/json'
#                             })
        
#         json_response = response.json()
#         json_response["Tenant"] = xero_tenant[key]['tenantName']
#         json_response["TenantID"] = xero_tenant[key]['tenantId']
#         final_response.append(json_response)

#     return final_response

# Xero API - Retrieve Contacts
def XeroContactGroupRequests():

    with open(token_filepath, 'r') as f:
        old_refresh_token = f.read()

    new_tokens = XeroRefreshToken(old_refresh_token)
    xero_tenant= XeroTenants(new_tokens[0])

    session = requests.Session()
    session.headers.update({
        'Authorization': f'Bearer {new_tokens[0]}',
        'Accept': 'application/json'
    })

    get_url = 'https://api.xero.com/api.xro/2.0/ContactGroups'
    final_response = []

    for key in xero_tenant:

        session.headers.update({'Xero-tenant-id': xero_tenant[key]['tenantId']})

        try:
            response = session.get(get_url)
            response.raise_for_status() # Check for 401, 403, 500 errors
            
            json_response = response.json()

            if "ContactGroups" in json_response:
                for group in json_response["ContactGroups"]:
                    # Flatten the data: Inject Tenant info directly into the group object
                    group["Tenant"] = xero_tenant[key]['tenantName']
                    group["TenantID"] = xero_tenant[key]['tenantId']
                
                final_response.extend(json_response["ContactGroups"])

            # tenant_object = {
            #     "Tenant": xero_tenant[key]['tenantName'],
            #     "TenantID": xero_tenant[key]['tenantId'],
            #     "ContactGroups": json_response.get("ContactGroups", []) # Empty list if no groups found
            # }
        
            # final_response.append(tenant_object)
                
        except requests.exceptions.RequestException as e:
            # Log the error but keep processing other tenants
            print(f"Error fetching for tenant {xero_tenant[key]['tenantName']}: {e}")

    return final_response

def XeroContactGroupMembers(tenant_id, group_id, tenant_name):

    try:
        # 1. Get a valid token (Reuse your existing token logic)
        with open(token_filepath, 'r') as f:
            old_refresh_token = f.read().strip()
        new_tokens = XeroRefreshToken(old_refresh_token)

        # 2. Call Xero API
        url = f'https://api.xero.com/api.xro/2.0/ContactGroups/{group_id}'
        headers = {
            'Authorization': f'Bearer {new_tokens[0]}',
            'Xero-tenant-id': tenant_id,
            'Accept': 'application/json'
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            contacts = []
            # Xero returns a list, we want the first group
            group_data = response.json().get('ContactGroups', [{}])[0]
            
            # Extract contacts and format them to match your existing data structure
            for c in group_data.get('Contacts', []):
                contacts.append({
                    "ContactID": c['ContactID'],
                    "ContactName": c['Name'],
                    "Tenant": tenant_name 
                })
            return contacts
            
    except Exception as e:
        print(f"Error fetching group {group_id}: {e}")
        
    return []

# Xero API - Retrieve invoices from selected contacts
def XeroInvoiceRequests(data, draft_inclusion):

    # Old method - Reading the data from temp file (Called by the invoice function from controller through API internally)

    # filename = request.args.get('filename')
    # filepath = os.path.join(os.path.abspath(os.getcwd()), "app", "temp", filename)

    # if filepath:

    #     try:
    #         with open(filepath, 'r') as f:
    #             data = json.load(f)
    #         # Optionally, delete the temporary file after reading
    #         os.remove(filepath)
    #     except FileNotFoundError:
    #         return jsonify({'status': 'fail', 'error': 'Selected data file not found, please generate the statement again.'}), 500
    #     except json.JSONDecodeError:
    #         return jsonify({'status': 'fail', 'error': 'Error decoding data file.'}), 500
    #     except IOError as e:
    #         return jsonify({'status': 'fail', 'error': 'Error reading data file.'}), 500
        
    if data:

        with open(token_filepath, 'r') as f:
            old_refresh_token = f.read()

        new_tokens = XeroRefreshToken(old_refresh_token)
        xero_tenant= XeroTenants(new_tokens[0])

        final_response = []

        for contact in data:

            xero_tenant_id = ''

            if contact['Tenant'] == "Macross Consultancy (M) Sdn Bhd":

                xero_tenant_id = xero_tenant['Macross']['tenantId']
            
            elif contact['Tenant'] == "Macross Consultancy Pte Ltd":

                xero_tenant_id = xero_tenant['Macross SG']['tenantId']

            elif contact['Tenant'] == "Co Maker Sdn Bhd":

                xero_tenant_id = xero_tenant['Co Maker']['tenantId']
            
            elif contact['Tenant'] == "C.T & Co (Ekoflora Branch)":

                xero_tenant_id = xero_tenant['C.T & Co']['tenantId']

            elif contact['Tenant'] == "Cheng & Associates Secretarial PLT":

                # continue
                xero_tenant_id = xero_tenant['Cheng & Associates']['tenantId']
            
            elif contact['Tenant'] == "MEA | Macross Entrepreneurs Academy Sdn Bhd":

                xero_tenant_id = xero_tenant['MEA']['tenantId']
            
            elif contact['Tenant'] == "MH | Macross Holding Sdn Bhd":

                xero_tenant_id = xero_tenant['Macross Holding']['tenantId']

            elif contact['Tenant'] == "MTA | Macross T&A Sdn Bhd":

                xero_tenant_id = xero_tenant['Macross T&A']['tenantId']

            get_url = ''

            if draft_inclusion == 'true':

                get_url = f"https://api.xero.com/api.xro/2.0/invoices?Statuses=AUTHORISED,DRAFT&ContactIDs={contact['ContactID']}&where=AmountDue>0 AND Type==\"ACCREC\""

            elif draft_inclusion == 'false':

                get_url = f"https://api.xero.com/api.xro/2.0/invoices?Statuses=AUTHORISED&ContactIDs={contact['ContactID']}&where=AmountDue>0 AND Type==\"ACCREC\""

            response = requests.get(get_url,
                                headers = {
                                    'Authorization': 'Bearer ' + new_tokens[0],
                                    'Xero-tenant-id': xero_tenant_id,
                                    'Accept': 'application/json'
                                })
            
            json_response = response.json()
            json_response["Tenant"] = contact['Tenant']
            final_response.append(json_response)
            
        return final_response

# Xero API - Download invoice as PDF
@sliding_window_rate_limit(limit=15, window=60)
def XeroDownloadInvoice(tenant, invoice_id):

    with open(token_filepath, 'r') as f:
        old_refresh_token = f.read()

    new_tokens = XeroRefreshToken(old_refresh_token)
    xero_tenant= XeroTenants(new_tokens[0])
    
    get_url = f'https://api.xero.com/api.xro/2.0/Invoices/{invoice_id}'

    response = requests.get(get_url,
                           headers = {
                               'Authorization': 'Bearer ' + new_tokens[0],
                               'Xero-tenant-id': xero_tenant[tenant]['tenantId'],
                               'Accept': 'application/pdf'
                           })
    
    pdf_data = response.content

    if pdf_data:

        response = requests.get(get_url,
                           headers = {
                               'Authorization': 'Bearer ' + new_tokens[0],
                               'Xero-tenant-id': xero_tenant[tenant]['tenantId'],
                               'Accept': 'application/json'
                           })
        
        invoice_no = response.json()['Invoices'][0]['InvoiceNumber']

        response_pdf = make_response(pdf_data)
        response_pdf.headers['Content-Type'] = 'application/pdf'
        response_pdf.headers['Content-Disposition'] = f'attachment; filename="{invoice_no}.pdf"'
        return response_pdf

    else:

        return jsonify({'status': 'fail', 'error': 'Failed to retrieve the PDF.'}), 500