import json
import yaml
import os
import argparse
from collections import defaultdict
from typing import Dict, List


def read_topology_files(directory: str) -> Dict:
    """Recursively read all JSON files from the specified directory and its subdirectories."""
    topology_data = {}
    for root, _, files in os.walk(directory):
        for filename in files:
            if filename.endswith('.json'):
                file_path = os.path.join(root, filename)
                try:
                    with open(file_path, 'r') as f:
                        topology_data.update(json.load(f))
                except json.JSONDecodeError as e:
                    print(f"Error reading {file_path}: {e}")
                except Exception as e:
                    print(f"Unexpected error reading {file_path}: {e}")
    return topology_data


def get_location_prefix(device_name: str) -> str:
    """Extract location prefix from device name."""
    return device_name.split('-')[0]


def create_device_session(device_name: str, node_details: Dict) -> Dict:
    """Create a session entry for a device."""
    return {
        'DeviceType': '',  # Could be populated if you have this info
        'Model': node_details.get('platform', ''),
        'SerialNumber': '',  # Could be populated if you have this info
        'SoftwareVersion': '',  # Could be populated if you have this info
        'Vendor': '',  # Could be populated if you have this info
        'credsid': '1',  # Default value, adjust as needed
        'display_name': device_name,
        'host': node_details.get('ip', device_name)
    }


def process_topology(topology_data: Dict) -> List[Dict]:
    """Process topology data and organize it by location."""
    locations = defaultdict(list)

    # Group devices by location prefix
    for device_name, details in topology_data.items():
        location = get_location_prefix(device_name)
        node_details = details.get('node_details', {})
        session = create_device_session(device_name, node_details)
        locations[location].append(session)

    # Create final YAML structure
    result = []
    for location, sessions in sorted(locations.items()):
        result.append({
            'folder_name': location,
            'sessions': sessions
        })

    return result


def main():
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(
        description='Convert topology JSON files to YAML format'
    )
    parser.add_argument(
        '-i', '--input',
        required=True,
        help='Input directory containing JSON topology files'
    )
    parser.add_argument(
        '-o', '--output',
        required=True,
        help='Output YAML file path'
    )

    args = parser.parse_args()

    # Verify input directory exists
    if not os.path.isdir(args.input):
        print(f"Error: Input directory '{args.input}' does not exist")
        return 1

    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Read topology files
    topology_data = read_topology_files(args.input)

    # Process topology data
    yaml_data = process_topology(topology_data)

    # Write YAML file
    try:
        with open(args.output, 'w') as f:
            yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)
        print(f"Successfully wrote output to {args.output}")
    except Exception as e:
        print(f"Error writing output file: {e}")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())