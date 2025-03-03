import os
import functions_framework
from google.cloud import firestore
from flask import jsonify, Request
from .apps import GHL  # Assuming GHL is imported from apps module
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

@functions_framework.http
def vici_to_ghl(request: Request):
    """HTTP Cloud Function to process Vici to GHL data.
    
    Expects query parameters and reads configuration from Firestore.
    """
    try:
        # Validate required query parameters
        required_params = ['firstName', 'lastName', 'dialedNumber', 'locationID']
        missing_params = [p for p in required_params if not request.args.get(p)]
        if missing_params:
            error_msg = f"Missing required query parameters: {', '.join(missing_params)}"
            logging.error(error_msg)
            return jsonify({"error": error_msg}), 400

        # Extract query parameters
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
        location_path = params.get('locationID')
        city = params.get('city')
        state = params.get('state')
        zip_code = params.get('zip')
        country = params.get('country')

        # Initialize Firestore client (optionally specify project if needed)
        fs_client = firestore.Client()

        # Ensure the document path is fully qualified (collection/document)
        # For example, if the collection is "configurations", use that.
        # If the provided location_path doesn't include a slash, add default collection.
        if "/" not in location_path:
            location_path = f"configurations/{location_path}"

        config_ref = fs_client.document(location_path)
        config_snapshot = config_ref.get(timeout=10)  # Using a timeout to avoid hanging
        if not config_snapshot.exists:
            error_msg = f"Configuration document not found: {location_path}"
            logging.error(error_msg)
            return jsonify({"error": error_msg}), 404

        config = config_snapshot.to_dict()
        location_key = config.get('locationApiKey', '')
        user_id = config.get('userID', '')
        # Assume location_id is the document id
        location_id = location_path.split('/')[-1]

        # Instantiate your application instance for external API interaction
        app_instance = GHL(location_key, location_id)
        query = f"phone=+1{dialed_number.strip()}"
        data = {
            "firstName": first_name,
            "lastName": last_name,
            "email": email,
            "phone": f"+1{dialed_number.strip()}",
            "city": city,
            "state": state,
            "postalCode": zip_code,
            "address1": f"{city}, {state} {zip_code}, {country}",
            "customFields": {
                "Vici List ID": list_id,
                "Vici List Description": list_description,
                "Vici Lead ID": lead_id,
                "Vici Subscriber ID": subscriber_id,
            },
            "tags": ["New Lead"],
        }

        # Look up the contact via external API
        contact = app_instance.contact_lookup(query)
        note_data = f"Disposition: {disposition}\nList ID: {list_id}\nTerm Reason: {term_reason}\nCall Note: {call_note}"

        if not contact:
            # Create new contact and add note
            contact_response = app_instance.create_contact(data)
            contact_id = contact_response["contact"]["id"]
            logging.info(f"Contact created: {contact_id}")
            note_response = app_instance.add_notes(contact_id, note_data, user_id)
            if note_response:
                logging.info(f"Note created: {note_response.get('id')}")
            return jsonify({"contact_id": contact_id}), 200
        else:
            # Update existing contact and add note
            contact_id = contact['id']
            contact_response = app_instance.update_contact(contact_id, data)
            logging.info(f"Contact updated: {contact_id}")
            note_response = app_instance.add_notes(contact_id, note_data, user_id)
            if note_response:
                logging.info(f"Note created: {note_response.get('id')}")
            return jsonify({"contact_id": contact_id}), 200

    except firestore.NotFound:
        error_msg = "Firestore document not found or misconfigured."
        logging.exception(error_msg)
        return jsonify({"error": error_msg}), 404
    except Exception as e:
        logging.exception("Unexpected error occurred.")
        return jsonify({"error": str(e)}), 500
