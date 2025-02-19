import os
import time
import requests
from datadog_api_client import ApiClient, Configuration
from datadog_api_client.v2.api.key_management_api import KeyManagementApi
from datadog_api_client.v2.model.application_key_create_attributes import ApplicationKeyCreateAttributes
from datadog_api_client.v2.model.application_key_create_data import ApplicationKeyCreateData
from datadog_api_client.v2.model.application_key_create_request import ApplicationKeyCreateRequest
from datadog_api_client.v2.model.application_keys_type import ApplicationKeysType

# Datadog API Base URL (change for US/EU accounts)
DATADOG_API_BASE_URL = "https://api.datadoghq.eu"  # Change to "https://api.datadoghq.com" if using US region

# Load API Key from Environment Variables
API_KEY = os.getenv("DD_API_KEY")
APP_KEY = os.getenv("DD_APP_KEY")

# Validate API Credentials
if not API_KEY or not APP_KEY:
    raise ValueError("Missing API Key or Application Key. Set DD_API_KEY and DD_APP_KEY as environment variables.")

# Unique Application Key Name
unique_app_key_name = f"Scoped-Key-{int(time.time())}"


def create_application_key():
    """
    Create a new application key with dashboard permissions.
    Returns the new app key and its ID.
    """
    body = ApplicationKeyCreateRequest(
        data=ApplicationKeyCreateData(
            type=ApplicationKeysType.APPLICATION_KEYS,
            attributes=ApplicationKeyCreateAttributes(
                name=unique_app_key_name,
                scopes=["dashboards_read", "dashboards_write"],
            ),
        ),
    )

    configuration = Configuration()
    configuration.api_key['apiKeyAuth'] = API_KEY
    configuration.api_key['appKeyAuth'] = APP_KEY

    with ApiClient(configuration) as api_client:
        api_instance = KeyManagementApi(api_client)
        response = api_instance.create_current_user_application_key(body=body)

    new_app_key_id = response.data.id
    new_app_key = response.data.attributes.key

    print(f"✅ Application Key Created: {new_app_key_id} - {new_app_key}")
    return new_app_key_id, new_app_key


def create_dashboard(api_key, app_key):
    """
    Create a Datadog dashboard using the new application key.
    """
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

    response = requests.post(f"{DATADOG_API_BASE_URL}/api/v1/dashboard", headers=headers, json=dashboard_payload)
    
    if response.status_code == 200 or response.status_code == 201:
        dashboard_id = response.json().get("id", "unknown")
        print(f"✅ Dashboard Created Successfully! ID: {dashboard_id}")
        return dashboard_id
    else:
        print(f"❌ Failed to create dashboard. Response: {response.json()}")
        return None


def delete_application_key(app_key_id):
    """
    Delete the application key after the dashboard has been created.
    """
    configuration = Configuration()
    configuration.api_key['apiKeyAuth'] = API_KEY
    configuration.api_key['appKeyAuth'] = APP_KEY

    with ApiClient(configuration) as api_client:
        api_instance = KeyManagementApi(api_client)
        api_instance.delete_current_user_application_key(app_key_id)
    
    print(f"✅ Application Key {app_key_id} Deleted Successfully!")


if __name__ == "__main__":
    try:
        # Step 1: Create Application Key
        new_app_key_id, new_app_key = create_application_key()

        # Step 2: Create Dashboard using the new application key
        dashboard_id = create_dashboard(API_KEY, new_app_key)

        # Step 3: Delete Application Key after use
        delete_application_key(new_app_key_id)

    except Exception as e:
        print(f"❌ Error during API operations: {e}")
