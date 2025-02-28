import functions_framework
from google.cloud import firestore
from flask import Flask, request, jsonify
from .apps import *
import os
import requests

@functions_framework.http
def vici_to_ghl(request: functions_framework.Request):
    try:
        # Extract query parameters from the request
        params = request.args
        first_name = params.get('firstName')
        last_name = params.get('lastName')
        list_description = params.get('listDescription')
        dialed_number = params.get('dialedNumber')
        disposition = params.get('disposition')
        talk_time = params.get('talkTime')
        term_reason = params.get('termReason')
        call_note = params.get('callNote')
        email = params.get('email')
        list_id = params.get('listID')
        lead_id = params.get('leadID', '0')
        subscriber_id = params.get('subscriberID')
        location_id = params.get('locationID')
        city = params.get('city')
        state = params.get('state')
        zip_code = params.get('zip')
        country = params.get('country')


        fs_client = firestore.Client()
        # Fetch configuration document from Firestore.
        config_ref = fs_client.document(location_id)
        config_snapshot = config_ref.get()
        if not config_snapshot.exists:
            print(f"Configuration document not found: {location_id}")
            return
        config = config_snapshot.to_dict()

        location_key = config.get('locationApiKey', '')

        app_instance = GHL(location_key, location_id)
        query = f"phone=+1{dialed_number.strip()}"

        data = {
            "firstName": first_name,
            "lastName": last_name,
            "email": email,
            "phone": "+1" + dialed_number.strip(),
            "city": city,
            "state": state,
            "zip": zip_code,
            "country": country,
            "address1": f"{city}, {state} {zip_code}",
        }

        contact = app_instance.contact_lookup(query)
        if not contact:
            contact_response = app_instance.create_contact(data)
            print(f"Contact created: {contact_response["id"]}")

        else:
            contact_id = contact['id']
            contact_response = app_instance.update_contact(contact_id, data)
            print(f"Contact updated: {contact_response["id"]}")


    except Exception as e:
        return jsonify({"error": str(e)}), 400