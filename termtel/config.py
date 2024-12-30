"""Configuration and shared settings for the Termtel application"""
from pkg_resources import resource_filename
from pathlib import Path

db_path = resource_filename('termtel', 'templates.db')

# Get paths from package
static_path = resource_filename('termtel', 'static')
templates_path = resource_filename('termtel', 'templates')

# Default settings
settings = {
    'theme': "default",
    'sessions': None,
    'sessionfile': 'sessions.yaml'
}