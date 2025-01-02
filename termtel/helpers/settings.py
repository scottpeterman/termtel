"""
Settings management for Termtel application.
Handles app and terminal theme preferences.
"""
import os
import sys
import logging
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)

DEFAULT_SETTINGS = {
    'themes': {
        'app_theme': 'cyberpunk',  # Default app theme
        'term_theme': 'Cyberpunk'  # Default terminal theme
    },
'view_settings': {  # New section for view settings
        'telemetry_visible': True
    }
}

class SettingsManager:
    """Manages application settings with focus on theme preferences."""

    def __init__(self, app_name: str = "Termtel"):
        self.app_name = app_name
        self.config_dir = self._get_config_dir()
        self.settings_path = self.config_dir / "settings.yaml"
        self._settings = {}
        self.load_settings()

    def _get_config_dir(self) -> Path:
        """Get the appropriate configuration directory for the current platform."""
        if sys.platform == "win32":
            base_dir = Path(os.environ["APPDATA"])
        elif sys.platform == "darwin":
            base_dir = Path.home() / "Library" / "Application Support"
        else:  # Linux and other Unix-like
            base_dir = Path.home() / ".config"

        config_dir = base_dir / self.app_name
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir

    def load_settings(self) -> None:
        """Load settings from file, creating default if none exists."""
        try:
            if self.settings_path.exists():
                with open(self.settings_path) as f:
                    loaded_settings = yaml.safe_load(f) or {}
                    # Merge with defaults to ensure all required settings exist
                    self._settings = DEFAULT_SETTINGS.copy()
                    # Update themes section
                    self._settings['themes'].update(loaded_settings.get('themes', {}))
                    # Update view_settings section
                    if 'view_settings' in loaded_settings:
                        self._settings['view_settings'].update(loaded_settings.get('view_settings', {}))
            else:
                logger.info("No settings file found, creating with defaults")
                self._settings = DEFAULT_SETTINGS.copy()
                self.save_settings()

        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            self._settings = DEFAULT_SETTINGS.copy()

    def save_settings(self) -> bool:
        """Save current settings to file."""
        try:
            with open(self.settings_path, 'w') as f:
                yaml.safe_dump(self._settings, f, default_flow_style=False)
                print(self._settings)
            return True
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            return False

    def get_app_theme(self) -> str:
        """Get the current app theme."""
        return self._settings['themes'].get('app_theme', DEFAULT_SETTINGS['themes']['app_theme'])

    def get_term_theme(self) -> str:
        """Get the current terminal theme."""
        return self._settings['themes'].get('term_theme', DEFAULT_SETTINGS['themes']['term_theme'])

    def set_app_theme(self, theme: str) -> bool:
        """Set the app theme."""
        try:
            self._settings['themes']['app_theme'] = theme
            return self.save_settings()
        except Exception as e:
            logger.error(f"Failed to set app theme: {e}")
            return False

    def set_term_theme(self, theme: str) -> bool:
        """Set the terminal theme."""
        try:
            self._settings['themes']['term_theme'] = theme
            return self.save_settings()
        except Exception as e:
            logger.error(f"Failed to set terminal theme: {e}")
            return False

    def reset_to_defaults(self) -> bool:
        """Reset all settings to defaults."""
        try:
            self._settings = DEFAULT_SETTINGS.copy()

            return self.save_settings()
        except Exception as e:
            logger.error(f"Failed to reset settings: {e}")
            return False

    def get_view_setting(self, key: str, default: any = None) -> any:
        """Get a view-related setting."""
        try:
            return self._settings.get('view_settings', {}).get(key, default)
        except Exception as e:
            logger.error(f"Failed to get view setting {key}: {e}")
            return default

    def set_view_setting(self, key: str, value: any) -> bool:
        """Set a view-related setting."""
        try:
            # Ensure view_settings section exists
            if 'view_settings' not in self._settings:
                self._settings['view_settings'] = {}
            self._settings['view_settings'][key] = value
            return self.save_settings()
        except Exception as e:
            logger.error(f"Failed to set view setting {key}: {e}")
            return False

