"""
Termtel - UI Setup Module
Handles menu system and dialog setup
"""
import yaml
from PyQt6.QtGui import QActionGroup, QAction
from PyQt6.QtWidgets import (
    QMenuBar, QMenu, QFileDialog, QDialog,
    QVBoxLayout, QLabel, QWidget, QGroupBox, QPushButton
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl, Qt
import logging
import os

from termtel.napalm_dashboard import DeviceDashboardWidget
from .credential_manager import CredentialManagerDialog
from .nbtosession import App as NetboxExporter

logger = logging.getLogger('termtel.setup')

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About Termtel")
        self.setMinimumSize(600, 400)

        layout = QVBoxLayout()

        web_view = QWebEngineView()
        about_html = """
        <html>
        <body style="background-color: #1e1e1e; color: #ffffff; font-family: Arial, sans-serif; margin: 20px;">
            <div style="text-align: center;">
                <img src="static/images/logo.png" alt="Termtel Logo" style="max-width: 200px;"/>
                <h1>Termtel</h1>
                <p>Version 1.0.0</p>
                <p>A modern terminal emulator with advanced telemetry capabilities.</p>
                <hr>
                <p>Features:</p>
                <ul style="list-style-type: none; padding: 0;">
                    <li>✓ Multi-session support</li>
                    <li>✓ Secure credential management</li>
                    <li>✓ Session telemetry</li>
                    <li>✓ Custom themes</li>
                </ul>
                <p>© 2024 Your Company</p>
            </div>
        </body>
        </html>
        """
        web_view.setHtml(about_html)
        layout.addWidget(web_view)
        self.setLayout(layout)


class TelemetryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Telemetry Settings")
        self.setMinimumSize(500, 400)

        layout = QVBoxLayout()

        # Data Collection Group
        collection_group = QGroupBox("Data Collection")
        collection_layout = QVBoxLayout()
        # TODO: Add data collection settings
        collection_group.setLayout(collection_layout)

        # Export Group
        export_group = QGroupBox("Data Export")
        export_layout = QVBoxLayout()
        export_btn = QPushButton("Export Telemetry Data")
        export_btn.clicked.connect(self.export_telemetry)
        export_layout.addWidget(export_btn)
        export_group.setLayout(export_layout)

        layout.addWidget(collection_group)
        layout.addWidget(export_group)
        self.setLayout(layout)

    def export_telemetry(self):
        # TODO: Implement telemetry export
        logger.info("Telemetry export requested")
        pass


def setup_menus(window):
    """Setup menu system for the main window"""
    menubar = window.menuBar()

    # File Menu
    file_menu = menubar.addMenu("&File")

    open_action = file_menu.addAction("&Open Sessions...")
    open_action.triggered.connect(lambda: handle_open_sessions(window))

    file_menu.addSeparator()
    exit_action = file_menu.addAction("E&xit")
    exit_action.triggered.connect(window.close)

    # View Menu
    view_menu = menubar.addMenu("&View")

    themes_menu = view_menu.addMenu("Theme")
    theme_group = QActionGroup(window)
    theme_group.setExclusive(True)

    available_themes = [
        'cyberpunk',
        'dark_mode',
        'light_mode',
        'retro_green',
        'retro_amber',
        'neon_blue'
    ]
    # Create theme actions
    for theme_name in available_themes:
        display_name = theme_name.replace('_', ' ').title()
        theme_action = QAction(display_name, window)
        theme_action.setCheckable(True)
        theme_action.setChecked(theme_name == window.theme)
        theme_action.triggered.connect(
            lambda checked, t=theme_name: window.switch_theme(t)
        )
        theme_group.addAction(theme_action)
        themes_menu.addAction(theme_action)

    credentials_action = view_menu.addAction("&Credentials")
    credentials_action.triggered.connect(lambda: show_credentials_dialog(window))

    telemetry_action = view_menu.addAction("&Telemetry")
    telemetry_action.triggered.connect(lambda: show_telemetry_dialog(window))

    # Tools Menu (new)
    tools_menu = menubar.addMenu("&Tools")

    netbox_action = tools_menu.addAction("&Netbox Import")
    netbox_action.triggered.connect(lambda: show_netbox_importer(window))
    manage_sessions_action = tools_menu.addAction('Manage Sessions')
    manage_sessions_action.triggered.connect(lambda: show_session_manager(window))

    # Help Menu
    help_menu = menubar.addMenu("&Help")

    about_action = help_menu.addAction("&About")
    about_action.triggered.connect(lambda: show_about_dialog(window))


def show_session_manager(window):
    """Launch the session manager dialog"""
    from termtel.widgets.session_editor import SessionEditorDialog

    dialog = SessionEditorDialog(window, session_file=window.session_file_with_path)
    if dialog.exec() == dialog.DialogCode.Accepted:
        # Reload the sessions after editing
        # window.load_sessions(window, window.session_file_with_path)
        try:
            with open(window.session_file_with_path) as f:
                sessions_data = yaml.safe_load(f)
                window.session_navigator.load_sessions(file_content_to_load=sessions_data)

        except Exception as e:
            logger.error(f"Failed to load sessions: {str(e)}")



def show_netbox_importer(window):
    """Show the Netbox to Session importer"""
    try:
        dialog = NetboxExporter(window)
        dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        dialog.show()
    except Exception as e:
        logger.error(f"Error showing Netbox importer: {e}")

def handle_open_sessions(window):
    """Handle opening a new sessions file"""
    try:
        file_name, _ = QFileDialog.getOpenFileName(
            window,
            "Open Sessions File",
            "",
            "YAML Files (*.yaml);;All Files (*)"
        )
        if file_name:
            logger.info(f"Opening sessions file: {file_name}")
            window.session_file = file_name
            window.load_sessions()
    except Exception as e:
        logger.error(f"Error opening sessions file: {e}")


def show_credentials_dialog(window):
    """Show the credentials management dialog"""
    try:
        dialog = CredentialManagerDialog(window)
        dialog.credentials_updated.connect(window.session_navigator.load_sessions)
        dialog.exec()
    except Exception as e:
        logger.error(f"Error showing credentials dialog: {e}")


def show_telemetry_dialog(window):
    """Show the telemetry settings dialog"""
    try:
        window.launch_telemetry()
    except Exception as e:
        logger.error(f"Error showing telemetry dialog: {e}")


def show_about_dialog(window):
    """Show the about dialog"""
    try:
        dialog = AboutDialog(window)
        dialog.exec()
    except Exception as e:
        logger.error(f"Error showing about dialog: {e}")