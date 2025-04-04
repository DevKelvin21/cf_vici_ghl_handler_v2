import os
import functions_framework
from google.cloud import firestore
from flask import jsonify, Request
from .apps import GHL  # Assuming GHL is imported from the apps module
import logging

# Configure logging for structured output (could be extended to use Stackdriver if needed)
logging.basicConfig(level=logging.INFO)

@functions_framework.http
def vici_to_ghl(request: Request):
    """
    HTTP Cloud Function to process Vici data and integrate with GHL.
    It extracts query parameters, retrieves configuration from Firestore,
    interacts with an external API via GHL, and logs each step.
    """
    try:
        # Validate required query parameters.
        required_params = ['firstName', 'lastName', 'dialedNumber', 'locationID']
        missing_params = [p for p in required_params if not request.args.get(p)]
        if missing_params:
            error_msg = f"Missing required query parameters: {', '.join(missing_params)}"
            logging.error(error_msg)
            return jsonify({"error": error_msg}), 400

        # Extract and normalize query parameters.
        params = request.args
        first_name = params.get('firstName')
        last_name = params.get('lastName')
        list_description = params.get('listDescription')
        dialed_number = params.get('dialedNumber')
        disposition = params.get('disposition')
        campaign_id = params.get('campaignID')
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

        # Initialize Firestore client.
        fs_client = firestore.Client()

        # Ensure the document path is fully qualified (e.g., "configurations/{locationID}")
        if "/" not in location_path:
            location_path = f"configurations/{location_path}"

        # Retrieve configuration with a timeout.
        config_ref = fs_client.document(location_path)
        config_snapshot = config_ref.get(timeout=10)
        if not config_snapshot.exists:
            error_msg = f"Configuration document not found: {location_path}"
            logging.error(error_msg)
            return jsonify({"error": error_msg}), 404

        config = config_snapshot.to_dict()
        location_key = config.get('locationApiKey', '')
        user_id = config.get('userID', '')
        # Derive a simple location ID from the document path.
        location_id = location_path.split('/')[-1]

        # Instantiate the GHL client for external API interaction.
        app_instance = GHL(location_key, location_id)

        # Build the query for contact lookup.
        query = f"phone=+1{dialed_number.strip()}"

        # Retrieve custom field definitions (assuming this is a method on GHL).
        custom_fields = app_instance.get_custom_fields()
        custom_fields_values = {
            "disposition": disposition,
            "term_reason": term_reason,
            "list_id": list_id,
            "lead_id": lead_id,
            "campaign": campaign_id,
        }

        # Prepare contact data with custom fields.
        data = {
            "firstName": first_name,
            "lastName": last_name,
            "email": email,
            "phone": f"+1{dialed_number.strip()}",
            "city": city,
            "state": state,
            "postalCode": zip_code,
            "address1": f"{city}, {state} {zip_code}, {country}",
            "customField": set_custom_fields(custom_fields_values, custom_fields),
            "tags": ["New Lead"],
        }

        # Look up existing contact via external API.
        contact = app_instance.contact_lookup(query)
        note_data = (
            f"Disposition: {disposition}\n"
            f"List ID: {list_id}\n"
            f"Term Reason: {term_reason}\n"
            f"Call Note: {call_note}"
        )

        if not contact:
            # Create new contact and add a note.
            contact_response = app_instance.create_contact(data)
            contact_id = contact_response["contact"]["id"]
            logging.info(f"Contact created: {contact_id}")
            note_response = app_instance.add_notes(contact_id, note_data, user_id)
            if note_response:
                logging.info(f"Note created: {note_response.get('id')}")

            pipelines=app_instance.get_pipelines()
            my_pipeline = None
            for pipeline in pipelines:
                if pipeline['name'] == config.get('pipelineName', 'Expireds and FSBO'):
                    my_pipeline = pipeline
            if my_pipeline != None:
                my_stage = None
                for stage in my_pipeline['stages']:
                    if stage['name'] == config.get('firstStageName','New'):
                        my_stage = stage
                if my_stage != None:
                    opportunity_data = {
                        "status": "open",
                        "title": f"{first_name} {last_name}",
                        "stageId": my_stage['id'],
                        "contactId": contact_id
                    }
                    my_opportunity_response = app_instance.create_opportunity(my_pipeline['id'], opportunity_data)
                    if my_opportunity_response:
                        logging.info(f"Opportunity Created: {my_opportunity_response['id']} {my_opportunity_response['name']}")
            return jsonify({"contact_id": contact_id}), 200
        else:
            # Update existing contact and add a note.
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


def set_custom_fields(data, custom_fields):
    """
    Constructs the custom field dictionary based on provided values and definitions.
    This helper function maps provided data to the expected custom field format.
    """
    result = {}
    for field in custom_fields:
        # Assumes fieldKey follows the format "prefix.fieldName"
        try:
            custom_field = field['fieldKey'].split(".")[1]
        except IndexError:
            logging.warning(f"Invalid fieldKey format: {field.get('fieldKey')}")
            continue

        if custom_field in data and data[custom_field]:
            # Special handling for disposition field.
            if custom_field == "disposition":
                # Assuming 'is_disposition_set' is a method on GHL instance; adjust as needed.
                current_disposition = field.get('currentValue')  # Replace with actual lookup if available.
                if current_disposition and data[custom_field] == current_disposition.replace(".", ""):
                    result[field['id']] = current_disposition + "."
                else:
                    result[field['id']] = data[custom_field]
            else:
                result[field['id']] = data[custom_field]
    return result
