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
        dialed_number = params.get('dialedNumber')
        disposition = params.get('disposition')
        campaign_id = params.get('campaignID')
        term_reason = params.get('termReason')
        call_note = params.get('callNote')
        email = params.get('email')
        list_id = params.get('listID')
        lead_id = params.get('leadID', '0')
        location_path = params.get('locationID')
        city = params.get('city')
        state = params.get('state')
        zip_code = params.get('zip')
        country = params.get('country')
        lead_type = params.get('leadType', '')
        agent_assigned = params.get('agentAssigned', '')
        alt_number = params.get('altNumber', '')
        home_value = params.get('homeValue', '')
        create_date = params.get('createDate', '')
        equity = params.get('equity', '')
        crm_name = params.get('crmName', '')
        contact_link = params.get('contactLink', '')
        build_date = params.get('buildDate', '')
        listing_agent = params.get('listingAgent', '')
        baths = params.get('baths', '')
        buyer_agent = params.get('buyerAgent', '')
        beds = params.get('beds', '')
        lot_size = params.get('lotSize', '')
        sqft = params.get('sqft', '')
        build=params.get('build', '')
        home_value = params.get('homeValue', '')
        sq_ft = params.get('sqFt', '')
        county = params.get('county', '')
        zestimate = params.get('zestimate', '')
        last_submission = params.get('lastSubmission', '')
        tag = params.get('tag', '')
        lead_score = params.get('leadScore', '')
        last_submission_date = params.get('lastSubmissionDate', '')
        estimated_price = params.get('estimatedPrice', '')
        last_number_dialed = params.get('lastNumberDialed', '')
        days_on_market = params.get('daysOnMarket', '')
        final_question = params.get('finalQuestion', '')
        alt_number = params.get('altNumber', '')
        listing_status = params.get('listingStatus', '')
        team_member = params.get('teamMember', '')
        bathrooms = params.get('bathrooms', '')
        motivation = params.get('motivation', '')
        secondary_number = params.get('secondaryNumber', '')
        homeowner= params.get('homeowner', '')
        home_to_sell_or_buy = params.get('homeToSellOrBuy', '')
        areas_of_interest = params.get('areasOfInterest', '')
        pending_repairs = params.get('pendingRepairs', '')
        non_negotiables = params.get('nonNegotiables', '')
        timeframe = params.get('timeframe', '')
        bedrooms = params.get('bedrooms', '')
        lender = params.get('lender', '')
        recent_upgrades = params.get('recentUpgrades', '')

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

        disposition_translated = set_disposition_translated(disposition)

        # Retrieve custom field definitions (assuming this is a method on GHL).
        custom_fields = app_instance.get_custom_fields()
        custom_fields_values = {
            "disposition": disposition_translated,
            "term_reason": term_reason,
            "list_id": list_id,
            "lead_id": lead_id,
            "campaign": campaign_id,
            "lead_type": lead_type,
            "agent_assigned": agent_assigned,
            "alt_number": alt_number,
            "home_value": home_value,
            "create_date": create_date,
            "equity": equity,
            "crm_name": crm_name,
            "contact_link": contact_link,
            "build_date": build_date,
            "listing_agent": listing_agent,
            "baths": baths,
            "buyer_agent": buyer_agent,
            "beds": beds,
            "lot_size": lot_size,
            "sqft": sqft,
            "build": build,
            "home_value": home_value,
            "sq_ft": sq_ft,
            "county": county,
            "zestimate": zestimate,
            "last_submission": last_submission,
            "tag": tag,
            "lead_score": lead_score,
            "last_submission_date": last_submission_date,
            "estimated_price": estimated_price,
            "last_number_dialed": last_number_dialed,
            "days_on_market": days_on_market,
            "final_question": final_question,
            "alt_number": alt_number,
            "listing_status": listing_status,
            "team_member": team_member,
            "bathrooms": bathrooms,
            "motivation": motivation,
            "secondary_number": secondary_number,
            "homeowner": homeowner,
            "home_to_sell_or_buy": home_to_sell_or_buy,
            "areas_of_interest": areas_of_interest,
            "pending_repairs": pending_repairs,
            "non_negotiables": non_negotiables,
            "timeframe": timeframe,
            "bedrooms": bedrooms,
            "lender": lender,
            "recent_upgrades": recent_upgrades,
            "notes": call_note,
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
            "tags": set_tags(disposition, config.get('dispositionTagMapping', {})),
        }

        # Look up existing contact via external API.
        contact = app_instance.contact_lookup(query)
        note_data = (
            f"Disposition: {disposition_translated}\n"
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
                if pipeline['name'] == config.get('pipelineName', 'Main Pipeline'):
                    my_pipeline = pipeline
            if my_pipeline != None:
                my_stage = None
                for stage in my_pipeline['stages']:
                    if stage['name'] == config.get('firstStageName','New Lead'):
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

def set_tags(disposition, disposition_tag_mapping):
    """
    Sets tags for the contact based on provided data.
    This helper function maps provided data to the expected tag format.
    If no tags are added, it defaults to "New Lead".
    """
    result = []
    
    if disposition:
        for tag, values in disposition_tag_mapping.items():
            if disposition in values:
                result.append(tag)
                break

    # Add "New Lead" as a default tag if no tags were added
    if not result:
        result.append("New Lead")

    return result

def set_disposition_translated(disposition):
    """
    Translates the disposition for the contact based on provided data.
    This helper function maps provided data to the expected disposition format.
    """

    dispositions_mapping = {
        "DROP": "No Answer",
        "ADC": "No Answer",
        "PDROP": "Outbound Pre-Routing",
        "A": "Answering Machine",
        "AA": "Answering Machine Auto",
        "AB": "Busy Auto",
        "B": "Busy",
        "CALLBK": "Call Back",
        "CBL": "Call Back Later",
        "DC": "Disconnected Number",
        "DNC": "Do Not Call",
        "Follow": "Follow Up",
        "N": "No Answer",
        "NAU": "No Answer",
        "NA": "No Answer Autodial",
        "NI": "Not Interested",
        "NPRSN": "In Person Appointment",
        "Nurtre": "Nurture",
        "PHNAPT": "Phone Appointment",
        "WN": "Wrong Number"
    }

    result = ""

    if disposition:
        # Iterate through the mapping to find a match
        for key, value in dispositions_mapping.items():
            if disposition.upper().startswith(key.upper()):  # Case-insensitive match
                result = value
                break

    return result