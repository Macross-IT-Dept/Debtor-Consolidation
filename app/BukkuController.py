import requests
from . import bukku_token, bukku_subdomain

# Bukku API - Retrieve contacts
def BukkuContactRequests():

    get_url = 'https://api.bukku.my/contacts?page_size=500&type=customer'
    response = requests.get(get_url,
                            headers = {
                                'Authorization': 'Bearer ' + bukku_token,
                                'Company-Subdomain': bukku_subdomain,
                                'Accept': 'application/json'
                            })
    json_response = response.json()
    json_response["Tenant"] = "Cheng & Associates Secretarial PLT"

    transformed_json_response = {}

    if 'contacts' in json_response:
        new_contacts_list = []
        for contact in json_response['contacts']:
            new_contact = {}
            for key, value in contact.items():
                # 2. Change 'legal_name' to 'Name'
                if key == 'legal_name':
                    new_contact['Name'] = value
                # 3. Change 'id' to 'ContactID'
                elif key == 'id':
                    new_contact['ContactID'] = value
                else:
                    new_contact[key] = value
            new_contacts_list.append(new_contact)
        transformed_json_response['Contacts'] = new_contacts_list

    # Copy over other top-level keys like 'paging'
    for key, value in json_response.items():
        if key != 'contacts':
            transformed_json_response[key] = value

    return transformed_json_response

# Bukku API - Retrieve invoices from selected contacts
def BukkuInvoiceRequests(data):
        
    if data:

        final_response = []

        for contact in data:

            if contact["Tenant"] == "Cheng & Associates Secretarial PLT":

                get_url = f"https://api.bukku.my/sales/invoices?payment_status=OUTSTANDING&page_size=500&contact_id={contact['ContactID']}"
                response = requests.get(get_url,
                                    headers = {
                                        'Authorization': 'Bearer ' + bukku_token,
                                        'Company-Subdomain': bukku_subdomain,
                                        'Accept': 'application/json'
                                    })
                
                json_response = response.json()
                json_response["Tenant"] = contact['Tenant']
                final_response.append(json_response)
            
        return final_response
