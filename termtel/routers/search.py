from fastapi import APIRouter, Depends, HTTPException, Query
from termtel.helpers.auth_helper import get_current_user
from pathlib import Path
import yaml
import pynetbox

# Initialize NetBox API connection
NETBOX_HOST = 'http://10.0.0.108:8000'  # Non-production instance
NETBOX_TOKEN = '6bb32247828eee4c64f85691ac1c9fe242f7905d'
netbox_api = pynetbox.api(NETBOX_HOST, token=NETBOX_TOKEN)
netbox_api.http_session.verify = False

# Define the router
router = APIRouter()

BASE_WORKSPACE_DIR = Path("./workspaces")

# Session management function (moved from main)
def load_sessions_for_user(username: str, session_file_name: str = "sessions.yaml"):
    user_workspace = BASE_WORKSPACE_DIR / username
    session_file = user_workspace / session_file_name

    # Fallback to global session file if user-specific session file doesn't exist
    if not session_file.exists():
        session_file = Path("./sessions/sessions.yaml")  # Global session file

    if session_file.exists():
        with open(session_file, 'r') as file:
            return yaml.safe_load(file)

    # Return an empty list if no session files are found
    return []

# Search sessions for the authenticated user
@router.get("/search")
async def search_sessions(query: str = Query(None, min_length=3), username: str = Depends(get_current_user)):
    sessions = load_sessions_for_user(username)

    matching_sessions = []
    for folder in sessions:
        for session in folder.get("sessions", []):
            if query.lower() in session.get('display_name', '').lower() or \
               query.lower() in session.get('DeviceType', '').lower() or \
               query.lower() in session.get('Model', '').lower():
                matching_sessions.append(session)

    return matching_sessions

# Search NetBox devices
@router.get("/search-netbox")
async def search_netbox(query: str = Query(None, min_length=3)):
    if query:
        devices = netbox_api.dcim.devices.filter(q=query)
        sessions_result = [
            {
                'DeviceType': str(device.platform),
                'Model': str(device.device_type.model) or '',
                'SerialNumber': str(device.serial) or '',
                'SoftwareVersion': 'unknown',
                'Vendor': str(device.device_type.manufacturer.name) if device.device_type.manufacturer else '',
                'display_name': str(device.name),
                'host': device.primary_ip.address.strip("/32") if device.primary_ip else 'unknown',
                'port': '22'
            }
            for device in devices
        ]
        return sessions_result
    return []
