#!/usr/bin/env python3
import os
import yaml

# Paths for the main config and the integrations configuration directory.
DATADOG_CONFIG_PATH = '/etc/datadog-agent/datadog.yaml'
CONF_DIR = '/etc/datadog-agent/conf.d'

# Mapping of integration names to a list of file paths that indicate the integration is installed.
DETECTION_FILES = {
    'apache': ['/usr/sbin/httpd', '/etc/httpd/conf/httpd.conf'],
    'ibm_mq': ['/opt/mqm/bin/dspmq'],  # Example detection file for IBM MQ
    # Add additional integrations and detection file paths as needed.
}

def is_integration_installed(integration_name):
    """Return True if any of the detection files for the integration exist."""
    file_paths = DETECTION_FILES.get(integration_name, [])
    for path in file_paths:
        if os.path.exists(path):
            return True
    return False

def update_integration_configs():
    # Read the main datadog.yaml configuration file.
    try:
        with open(DATADOG_CONFIG_PATH, 'r') as f:
            main_config = yaml.safe_load(f)
    except Exception as e:
        print(f"Error reading {DATADOG_CONFIG_PATH}: {e}")
        return

    # Get the datadog_checks section which contains integration configurations.
    datadog_checks = main_config.get('datadog_checks', {})
    if not datadog_checks:
        print("No datadog_checks section found in the configuration.")
        return

    # Process each integration defined in datadog_checks.
    for integration, config in datadog_checks.items():
        # Check if the integration's installation files are present on the instance.
        if not is_integration_installed(integration):
            print(f"Installation for integration '{integration}' not detected. Skipping configuration update.")
            continue

        # Construct the path to the integration's config directory.
        integration_dir = os.path.join(CONF_DIR, integration)
        conf_file_path = os.path.join(integration_dir, 'conf.yaml')

        # Check if the integration folder exists.
        if os.path.isdir(integration_dir):
            try:
                # Write (or overwrite) the integration configuration to conf.yaml.
                with open(conf_file_path, 'w') as conf_file:
                    yaml.dump(config, conf_file, default_flow_style=False)
                print(f"Updated configuration for integration '{integration}' at {conf_file_path}")
            except Exception as e:
                print(f"Error updating {conf_file_path} for integration '{integration}': {e}")
        else:
            print(f"Directory for integration '{integration}' not found at {integration_dir}. Skipping update.")

if __name__ == "__main__":
    update_integration_configs()
