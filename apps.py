from typing import Any
import requests
import json
from .exceptions import ApiError

class GHL:

    def __init__(self, agency_api_key, location_id) -> None:
        self.agency_api_key = agency_api_key
        self.location_id = location_id
        self.location_api_key = None
        self.get_location_ep = f'https://rest.gohighlevel.com/v1/locations/{self.location_id}'
        self.contact_ep = 'https://rest.gohighlevel.com/v1/contacts/{}'
        self.contact_lookup_ep = 'https://rest.gohighlevel.com/v1/contacts/lookup?'
        self.custom_fields_ep = "https://rest.gohighlevel.com/v1/custom-fields/"
        self.notes_ep = "https://rest.gohighlevel.com/v1/contacts/{}/notes/"
        self.pipelines_ep = "https://rest.gohighlevel.com/v1/pipelines/"
        self.opportunities_ep = "https://rest.gohighlevel.com/v1/pipelines/{}/opportunities"

    def get_location(self):
        headers = {
            'Authorization': f'Bearer {self.agency_api_key}'
        }
        request = requests.get(url=self.get_location_ep,
                               headers=headers)
        if request.status_code == 200:
            return request.json()
        raise ApiError(request.status_code, list(request.json().values())[0]["message"] + " status code: {}")

    def get_custom_fields(self):
        custom_fields_data = []
        self.location_api_key = self.get_location(
        )['apiKey'] if self.location_api_key is None else self.location_api_key
        headers = {
            'Authorization': f'Bearer {self.location_api_key}'
        }
        response = requests.get(url=self.custom_fields_ep, headers=headers)
        if response.status_code != 200:
            raise ApiError(response.status_code)
        if 'customFields' in response.json():
            custom_fields_data = response.json()
        if len(custom_fields_data) == 0:
            return None
        return custom_fields_data['customFields']

    def contact_lookup(self, query_params):
        contact_data = []
        self.location_api_key = self.get_location(
        )['apiKey'] if self.location_api_key is None else self.location_api_key
        headers = {
            'Authorization': f'Bearer {self.location_api_key}'
        }
        url = self.contact_lookup_ep + query_params
        response = requests.get(url=url, headers=headers)
        if response.status_code != 200:
            if response.status_code == 422:
                return None
            raise ApiError(response.status_code)
        if 'contacts' in response.json():
            contact_data = response.json()['contacts']
        if len(contact_data) == 0:
            return None
        return contact_data[0]

    def update_contact(self, contact_id, data):
        contact_data = []
        self.location_api_key = self.get_location(
        )['apiKey'] if self.location_api_key is None else self.location_api_key
        headers = {
            'Authorization': f'Bearer {self.location_api_key}',
            'Content-Type': 'application/json'
        }
        url = self.contact_ep.format(contact_id)
        payload = json.dumps(data)
        response = requests.put(url=url, headers=headers, data=payload)
        if response.status_code != 200:
            raise ApiError(response.status_code)
        contact_data = response.json()
        return contact_data

    def create_contact(self, data):
        contact_data = []
        self.location_api_key = self.get_location(
        )['apiKey'] if self.location_api_key is None else self.location_api_key
        headers = {
            'Authorization': f'Bearer {self.location_api_key}',
            'Content-Type': 'application/json'
        }
        url = self.contact_ep.format('')
        payload = json.dumps(data)
        response = requests.post(url=url, headers=headers, data=payload)
        if response.status_code != 200:
            raise ApiError(response.status_code)
        contact_data = response.json()
        return contact_data

    def add_notes(self, contact_id, notes, user_id):
        notes_data = []
        self.location_api_key = self.get_location(
        )['apiKey'] if self.location_api_key is None else self.location_api_key
        headers = {
            'Authorization': f'Bearer {self.location_api_key}',
            'Content-Type': 'application/json'
        }
        url = self.notes_ep.format(contact_id)
        payload = json.dumps({
            "body": notes,
            "userID": user_id
        })
        response = requests.post(url=url, headers=headers, data=payload)
        if response.status_code != 200:
            raise ApiError(response.status_code)
        notes_data = response.json()
        return notes_data

    def get_pipelines(self):
        pipelines_data = []
        self.location_api_key = self.get_location(
        )['apiKey'] if self.location_api_key is None else self.location_api_key
        headers = { 'Authorization': f'Bearer {self.location_api_key}' }
        url = self.pipelines_ep
        response = requests.get(url=url, headers=headers)
        if response.status_code != 200:
            raise ApiError(response.status_code)
        if 'pipelines' in response.json():
            pipelines_data = response.json()['pipelines']
        if len(pipelines_data) == 0:
            return None
        return pipelines_data

    def get_opportunities(self, pipeline_id, query_params=None):
        opportunities_data = []
        self.location_api_key = self.get_location(
        )['apiKey'] if self.location_api_key is None else self.location_api_key
        headers = { 'Authorization': f'Bearer {self.location_api_key}' }
        url = self.opportunities_ep.format(pipeline_id) + '?query=' + query_params if query_params else self.opportunities_ep.format(pipeline_id)
        response = requests.get(url=url, headers=headers)
        if response.status_code != 200:
            raise ApiError(response.status_code)
        if 'opportunities' in response.json():
            opportunities_data = response.json()['opportunities']
        if len(opportunities_data) == 0:
            return None
        return opportunities_data

    def create_opportunity(self, pipeline_id, data):
        opportunity_data = []
        self.location_api_key = self.get_location(
        )['apiKey'] if self.location_api_key is None else self.location_api_key
        headers = {
            'Authorization': f'Bearer {self.location_api_key}',
            'Content-Type': 'application/json'
        }
        url = self.opportunities_ep.format(pipeline_id) + '/'
        payload = json.dumps(data)
        response = requests.post(url=url, headers=headers, data=payload)
        if response.status_code != 200:
            raise ApiError(response.status_code)
        opportunity_data = response.json()
        return opportunity_data

    def update_opportunity(self, pipeline_id, opportunity_id, data):
        opportunity_data = []
        self.location_api_key = self.get_location(
        )['apiKey'] if self.location_api_key is None else self.location_api_key
        headers = {
            'Authorization': f'Bearer {self.location_api_key}',
            'Content-Type': 'application/json'
        }
        url = self.opportunities_ep.format(pipeline_id) + '/' + str(opportunity_id)
        payload = json.dumps(data)
        response = requests.put(url=url, headers=headers, data=payload)
        if response.status_code != 200:
            raise ApiError(response.status_code)
        opportunity_data = response.json()
        return opportunity_data
    