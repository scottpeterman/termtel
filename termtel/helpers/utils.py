import socket

import yaml
from fastapi import Path

from termtel.routers.workspace import create_workspace_for_user


# Session management
def load_sessions_for_user(username: str):
    user_workspace = create_workspace_for_user(username)
    session_file = user_workspace / "sessions.yaml"

    # Fallback to global session file if user-specific session file doesn't exist
    if not session_file.exists():
        session_file = Path("./sessions/sessions.yaml")  # Global session file

    if session_file.exists():
        with open(session_file, 'r') as file:
            return yaml.safe_load(file)

    # Return an empty list if no session files are found
    return []

def find_available_port(start_port=8000, end_port=9000):
    for port in range(start_port, end_port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except socket.error:
                continue
    raise RuntimeError(f"No available port found between {start_port} and {end_port}")
