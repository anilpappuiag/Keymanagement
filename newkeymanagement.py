import os
import time
import logging
import requests
from datadog_api_client import ApiClient, Configuration
from datadog_api_client.v2.api.key_management_api import KeyManagementApi
from datadog_api_client.v2.model.application_key_create_attributes import ApplicationKeyCreateAttributes
from datadog_api_client.v2.model.application_key_create_data import ApplicationKeyCreateData
from datadog_api_client.v2.model.application_key_create_request import ApplicationKeyCreateRequest
from datadog_api_client.v2.model.application_keys_type import ApplicationKeysType

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Datadog API Base URL (Change for US/EU accounts)
DATADOG_API_BASE_URL = "https://api.datadoghq.eu"  # Use "https://api.datadoghq.com" for US region
API_KEY_ENDPOINT = f"{DATADOG_API_BASE_URL}/api/v2/current_user/application_keys"
DASHBOARD_ENDPOINT = f"{DATADOG_API_BASE_URL}/api/v1/dashboard"


def get_api_keys():
    """Retrieve API keys securely from environment variables."""
    api_key = os.getenv("DD_API_KEY")
    app_key = os.getenv("DD_APP_KEY")

    if not api_key or not app_key:
        raise ValueError("Missing API Key or Application Key. Set DD_API_KEY and DD_APP_KEY as environment variables.")
    
    return api_key, app_key


def create_application_key(api_key, app_key):
    """Create a new application key with dashboard permissions."""
    unique_app_key_name = f"Scoped-Key-{int(time.time())}"
    payload = {
        "data": {
            "type": "application_keys",
            "attributes": {
                "name": unique_app_key_name,
                "scopes": ["dashboards_read", "dashboards_write"]
            }
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "DD-API-KEY": api_key,
        "DD-APPLICATION-KEY": app_key
    }

    try:
        response = requests.post(API_KEY_ENDPOINT, headers=headers, json=payload)
        response.raise_for_status()

        new_app_key_id = response.json()["data"]["id"]
        new_app_key = response.json()["data"]["attributes"]["key"]

        logging.info(f"✅ Application Key Created: {new_app_key_id}")
        return new_app_key_id, new_app_key

    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Failed to create application key: {e}")
        return None, None


def create_dashboard(api_key, app_key):
    """Create a Datadog dashboard using the new application key."""
    headers = {
        "Content-Type": "application/json",
        "DD-API-KEY": api_key,
        "DD-APPLICATION-KEY": app_key,
    }

    dashboard_payload = {
        "title": "Automated Dashboard",
        "description": "Created using an API script",
        "widgets": [
            {
                "definition": {
                    "type": "note",
                    "content": "This dashboard was created programmatically.",
                    "font_size": "16",
                    "text_align": "center"
                }
            }
        ],
        "layout_type": "ordered",
        "is_read_only": False
    }

    try:
        response = requests.post(DASHBOARD_ENDPOINT, headers=headers, json=dashboard_payload)
        response.raise_for_status()
        dashboard_id = response.json().get("id", "unknown")
        logging.info(f"✅ Dashboard Created Successfully! ID: {dashboard_id}")
        return dashboard_id

    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Failed to create dashboard: {e}")
        return None


def delete_application_key(api_key, app_key, app_key_id):
    """Delete the application key after the dashboard has been created."""
    delete_endpoint = f"{API_KEY_ENDPOINT}/{app_key_id}"

    headers = {
        "DD-API-KEY": api_key,
        "DD-APPLICATION-KEY": app_key
    }

    try:
        response = requests.delete(delete_endpoint, headers=headers)
        response.raise_for_status()
        logging.info(f"✅ Application Key {app_key_id} Deleted Successfully!")

    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Failed to delete application key {app_key_id}: {e}")


if __name__ == "__main__":
    try:
        # Load API Keys
        API_KEY, APP_KEY = get_api_keys()

        # Step 1: Create Application Key
        new_app_key_id, new_app_key = create_application_key(API_KEY, APP_KEY)
        if not new_app_key_id or not new_app_key:
            raise RuntimeError("Application Key creation failed. Aborting process.")

        # Step 2: Create Dashboard using the new application key
        dashboard_id = create_dashboard(API_KEY, new_app_key)

        # Step 3: Delete Application Key after use
        if new_app_key_id:
            delete_application_key(API_KEY, APP_KEY, new_app_key_id)

    except Exception as e:
        logging.error(f"❌ Error during API operations: {e}")
