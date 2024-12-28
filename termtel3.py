#!/usr/bin/env python3
"""
Termtel - A PyQt6 Terminal Emulator
"""
import sys
import socket
import logging
from pathlib import Path

import yaml

from napalm_dashboard import DeviceDashboardWidget
from themes2 import ThemeLibrary, LayeredHUDFrame

from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtWidgets import QApplication, QMainWindow, QSplitter, QWidget, QHBoxLayout, QVBoxLayout, QMessageBox, \
    QInputDialog, QLineEdit, QStyleFactory
from PyQt6.QtCore import QUrl, QThread, Qt, QCoreApplication
from contextlib import closing
from typing import Optional, cast
import click
from helpers.settings import SettingsManager
from helpers.credslib import SecureCredentials
from widgets.session_navigator import SessionNavigator
from widgets.setup import setup_menus
from widgets.terminal_tabs import TerminalTabWidget

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('termtel')


class FastAPIServer(QThread):
    def __init__(self, app, port: int):
        super().__init__()
        self.app = app
        self.port = port

    def run(self):
        import uvicorn
        uvicorn.run(self.app, host="127.0.0.1", port=self.port)


class TermtelWindow(QMainWindow):
    def __init__(self, theme: str = "cyberpunk", session_file: str = "sessions.yaml"):
        super().__init__()
        self.server_thread: Optional[FastAPIServer] = None
        self.port = self.find_free_port()
        self.theme = theme
        self.theme_manager = ThemeLibrary()
        self.session_file = session_file
        self.cred_manager = SecureCredentials()
        self.settings_manager = SettingsManager()

        # Override theme with saved preference if it exists
        self.theme = self.settings_manager.get_app_theme()

        # Initialize UI before applying theme
        setup_menus(self)
        self.init_ui()

        self.theme_manager.apply_theme(self, self.theme)
        self.initialize_credentials()

        self.start_server()
        self.session_navigator.connect_requested.connect(self.handle_session_connect)

    def launch_telemetry(self):
        self.telemetry = DeviceDashboardWidget(parent=self)
        self.telemetry.setup_ui()
        self.telemetry.show()

    def load_saved_settings(self):
        """Load and apply saved settings."""
        # Apply window geometry if saved
        nav_width = self.settings_manager.get('navigation', 'tree_width', 250)
        if nav_width != 250:  # Only update if different from default
            sizes = self.splitter.sizes()
            total_width = sum(sizes)
            term_width = total_width - nav_width
            self.splitter.setSizes([nav_width, term_width])

        # Apply terminal settings
        term_settings = self.settings_manager.get_section('terminal')
        if term_settings:
            self.terminal_tabs.apply_settings(term_settings)

    def apply_dark_palette(self):
        """Apply dark color palette to the application."""
        dark_palette = QPalette()

        # Base colors
        dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)

        app = cast(QApplication, QApplication.instance())
        if app is not None:
            app.setPalette(dark_palette)

    def apply_light_palette(self):
        """Apply an improved light color palette to the application."""
        light_palette = QPalette()

        # Define colors
        background = QColor(248, 248, 248)  # Soft white background
        panel_background = QColor(240, 240, 240)  # Slightly darker for panels
        text = QColor("#000000")  # Soft black for text
        highlight = QColor(0, 120, 215)  # Windows-style blue for selection
        inactive_text = QColor(119, 119, 119)  # Grey for disabled items

        # Base interface colors
        light_palette.setColor(QPalette.ColorRole.Window, background)
        light_palette.setColor(QPalette.ColorRole.WindowText, text)
        light_palette.setColor(QPalette.ColorRole.Base, Qt.GlobalColor.white)
        light_palette.setColor(QPalette.ColorRole.AlternateBase, panel_background)
        light_palette.setColor(QPalette.ColorRole.Text, text)
        light_palette.setColor(QPalette.ColorRole.Button, panel_background)
        light_palette.setColor(QPalette.ColorRole.ButtonText, text)

        # Selection and highlighting
        light_palette.setColor(QPalette.ColorRole.Highlight, highlight)
        light_palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)

        # Tooltips
        light_palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        light_palette.setColor(QPalette.ColorRole.ToolTipText, text)

        # Links
        light_palette.setColor(QPalette.ColorRole.Link, highlight)
        light_palette.setColor(QPalette.ColorRole.LinkVisited, QColor(0, 100, 200))

        # Disabled state colors
        light_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, inactive_text)
        light_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, inactive_text)
        light_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, inactive_text)

        app = cast(QApplication, QApplication.instance())
        if app is not None:
            app.setPalette(light_palette)

            # Apply additional styling for specific widgets
            app.setStyleSheet("""
                QTreeView {
                    background-color: white;
                    border: 1px solid #e0e0e0;
                    padding: 5px;
                    color: #333333;
                }
                QTreeView::item {
                    padding: 5px;
                    border-radius: 2px;
                }
                QTreeView::item:hover {
                    background-color: #f5f5f5;
                }
                QTreeView::item:selected {
                    background-color: #0078d7;
                    color: white;
                }
                QHeaderView::section {
                    background-color: #f8f8f8;
                    color: #333333;
                    padding: 5px;
                    border: none;
                    border-bottom: 1px solid #e0e0e0;
                }
                QLineEdit {
                    background-color: white;
                    border: 1px solid #e0e0e0;
                    border-radius: 2px;
                    padding: 5px;
                    color: #333333;
                }
                QLineEdit:focus {
                    border: 1px solid #0078d7;
                }
                QPushButton {
                    background-color: #f8f8f8;
                    border: 1px solid #e0e0e0;
                    border-radius: 2px;
                    padding: 5px 15px;
                    color: #333333;
                }
                QPushButton:hover {
                    background-color: #f0f0f0;
                    border: 1px solid #d0d0d0;
                }
                QPushButton:pressed {
                    background-color: #e0e0e0;
                }
                QSplitter::handle {
                    background-color: #e0e0e0;
                    width: 1px;
                }
                QTabWidget::pane {
                    border: 1px solid #e0e0e0;
                    border-top: none;
                }
                QTabBar::tab {
                    background-color: #f8f8f8;
                    color: #333333;
                    padding: 8px 12px;
                    border: 1px solid #e0e0e0;
                    border-bottom: none;
                    margin-right: 2px;
                }
                QTabBar::tab:hover {
                    background-color: #f0f0f0;
                }
                QTabBar::tab:selected {
                    background-color: white;
                    border-bottom: 1px solid white;
                }
                QMenuBar {
                    background-color: #f8f8f8;
                    color: #333333;
                    border-bottom: 1px solid #e0e0e0;
                }
                QMenuBar::item:selected {
                    background-color: #f0f0f0;
                }
                QMenu {
                    background-color: white;
                    color: #333333;
                    border: 1px solid #e0e0e0;
                }
                QMenu::item:selected {
                    background-color: #f0f0f0;
                }
                QScrollBar:vertical {
                    background: #f8f8f8;
                    width: 14px;
                    margin: 0px;
                }
                QScrollBar::handle:vertical {
                    background: #d0d0d0;
                    min-height: 20px;
                    border-radius: 7px;
                    margin: 2px;
                }
                QScrollBar::handle:vertical:hover {
                    background: #b0b0b0;
                }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                    height: 0px;
                }
            """)


    def init_ui(self):
        self.setWindowTitle('TerminalTelemetry')
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        width = int(screen_geometry.width() * 0.8)
        self.width = width
        height = int(screen_geometry.height() * 0.8)
        center_point = screen_geometry.center()
        self.setGeometry(center_point.x() - width // 2, center_point.y() - height // 2, width, height)

        self.main_frame = LayeredHUDFrame(self, theme_manager=self.theme_manager, theme_name=self.theme)
        self.setCentralWidget(self.main_frame)

        # Main horizontal splitter
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_frame.content_layout.addWidget(self.main_splitter)

        # Left side container
        left_container = QWidget()
        left_layout = QHBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # Terminal section splitter
        self.terminal_splitter = QSplitter(Qt.Orientation.Horizontal)
        left_layout.addWidget(self.terminal_splitter)

        # Session Navigator
        nav_frame = LayeredHUDFrame(self, theme_manager=self.theme_manager, theme_name=self.theme)
        self.session_navigator = SessionNavigator(parent=self, cred_manager=self.cred_manager)
        nav_layout = QVBoxLayout()
        nav_frame.content_layout.addLayout(nav_layout)
        nav_layout.addWidget(self.session_navigator)
        nav_frame.setMinimumWidth(250)
        nav_frame.setMaximumWidth(400)
        self.terminal_splitter.addWidget(nav_frame)

        # Terminal Tabs
        term_frame = LayeredHUDFrame(self, theme_manager=self.theme_manager, theme_name=self.theme)
        self.terminal_tabs = TerminalTabWidget(self.port, parent=self)
        term_layout = QVBoxLayout()
        term_frame.content_layout.addLayout(term_layout)
        term_layout.addWidget(self.terminal_tabs)
        self.terminal_splitter.addWidget(term_frame)

        # Add left container to main splitter
        self.main_splitter.addWidget(left_container)

        # Add telemetry panel
        telemetry_frame = LayeredHUDFrame(self, theme_manager=self.theme_manager, theme_name=self.theme)
        self.telemetry = DeviceDashboardWidget(parent=self)
        telemetry_layout = QVBoxLayout()
        telemetry_frame.content_layout.addLayout(telemetry_layout)
        telemetry_layout.addWidget(self.telemetry)
        self.main_splitter.addWidget(telemetry_frame)

        # Set proportions
        self.main_splitter.setSizes([int(width * 0.6), int(width * 0.4)])
        self.terminal_splitter.setSizes([250, width - 250])


    # def init_ui(self):
    #     self.setWindowTitle('TerminalTelemetry')
    #
    #     # Screen geometry setup remains the same
    #     screen = QApplication.primaryScreen()
    #     screen_geometry = screen.availableGeometry()
    #     width = int(screen_geometry.width() * 0.8)
    #     self.width = width
    #     height = int(screen_geometry.height() * 0.8)
    #     center_point = screen_geometry.center()
    #     x = center_point.x() - width // 2
    #     y = center_point.y() - height // 2
    #     self.setGeometry(x, y, width, height)
    #
    #     # Create main frame using LayeredHUDFrame
    #     self.main_frame = LayeredHUDFrame(self, theme_manager=self.theme_manager, theme_name=self.theme)
    #     self.setCentralWidget(self.main_frame)
    #
    #     # Main layout goes inside the frame's content layout
    #     main_layout = QHBoxLayout()
    #     self.main_frame.content_layout.addLayout(main_layout)
    #     main_layout.setContentsMargins(0, 0, 0, 0)
    #     main_layout.setSpacing(0)
    #
    #     # Create splitter
    #     self.splitter = QSplitter(Qt.Orientation.Horizontal)
    #     main_layout.addWidget(self.splitter)
    #
    #     # Session Navigator (also using LayeredHUDFrame)
    #     nav_frame = LayeredHUDFrame(self, theme_manager=self.theme_manager, theme_name=self.theme)
    #     self.session_navigator = SessionNavigator(parent=self, cred_manager=self.cred_manager)
    #     nav_layout = QVBoxLayout()
    #     nav_frame.content_layout.addLayout(nav_layout)
    #     nav_layout.addWidget(self.session_navigator)
    #     nav_frame.setMinimumWidth(250)
    #     nav_frame.setMaximumWidth(400)
    #     self.splitter.addWidget(nav_frame)
    #
    #     # Terminal Tabs (using LayeredHUDFrame)
    #     term_frame = LayeredHUDFrame(self, theme_manager=self.theme_manager, theme_name=self.theme)
    #     self.terminal_tabs = TerminalTabWidget(self.port, parent=self)
    #     term_layout = QVBoxLayout()
    #     term_frame.content_layout.addLayout(term_layout)
    #     term_layout.addWidget(self.terminal_tabs)
    #     self.splitter.addWidget(term_frame)
    #
    #     # Set splitter sizes
    #     nav_width = int(width * 0.20)
    #     term_width = width - nav_width
    #     self.splitter.setSizes([nav_width, term_width])
    #     self.switch_theme(self.theme)

    def switch_theme(self, theme_name: str):
        """Override switch_theme to save the preference."""
        self.theme = theme_name
        self.theme_manager.apply_theme(self, theme_name)

        # Save the theme preference
        self.settings_manager.set_app_theme(theme_name)

        # Update all frames
        self.main_frame.set_theme(theme_name)
        for frame in self.findChildren(LayeredHUDFrame):
            frame.set_theme(theme_name)

        # Update session navigator
        self.session_navigator.update_theme(theme_name)

        # Update terminal tabs
        self.terminal_tabs.update_theme(theme_name)

        # Update the application palette based on theme
        if theme_name in ['light_mode']:
            self.apply_light_palette()
        else:
            self.apply_dark_palette()

    def handle_session_connect(self, connection_data):
        """Handle connection request."""
        logger.info(f"Connecting to: {connection_data['host']}:{connection_data['port']}")
        self.terminal_tabs.create_terminal(connection_data)

    def find_free_port(self) -> int:
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
            s.bind(('', 0))
            s.listen(1)
            port = s.getsockname()[1]
            logger.info(f"Found available port: {port}")
            return port

    def initialize_credentials(self):
        """Initialize the credential system."""
        try:
            if not self.cred_manager.is_initialized:
                password, ok = QInputDialog.getText(
                    self,
                    "Set Master Password",
                    "No credential store found. Enter a master password to create one:",
                    QLineEdit.EchoMode.Password
                )
                if ok and password:
                    if not self.cred_manager.setup_new_credentials(password):
                        QMessageBox.warning(self, "Error", "Failed to initialize credentials")
                return

            if not self.cred_manager.is_unlocked():
                password, ok = QInputDialog.getText(
                    self,
                    "Unlock Credentials",
                    "Enter master password:",
                    QLineEdit.EchoMode.Password
                )
                if ok and password:
                    if not self.cred_manager.unlock(password):
                        QMessageBox.warning(self, "Error", "Invalid master password")

        except Exception as e:
            logger.error(f"Failed to initialize credentials: {e}")
            QMessageBox.critical(self, "Error", f"Failed to initialize credentials: {e}")

    def start_server(self):
        try:
            from main import app  # Import the FastAPI app
            # Update settings before starting server
            from main import settings
            settings['theme'] = self.theme
            settings['sessionfile'] = self.session_file

            self.server_thread = FastAPIServer(app, self.port)
            self.server_thread.start()

            # Load sessions after server starts
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(1000, self.load_sessions)
            logger.info(f"Server started on port {self.port}")

        except Exception as e:
            logger.error(f"Failed to start server: {str(e)}")
            self.close()

    def load_sessions(self):
        """Load sessions from the YAML file."""
        try:
            with open(self.session_file) as f:
                sessions_data = yaml.safe_load(f)
            self.session_navigator.load_sessions(sessions_data)
        except Exception as e:
            logger.error(f"Failed to load sessions: {str(e)}")

    def closeEvent(self, event):
        """Handle application closure."""
        # Clean up terminals
        if hasattr(self, 'terminal_tabs'):
            self.terminal_tabs.cleanup_all()

        # Shut down server
        if self.server_thread and self.server_thread.isRunning():
            logger.info("Shutting down server...")
            self.server_thread.terminate()
            self.server_thread.wait()
        event.accept()


@click.command()
@click.option('--theme', default='cyberpunk', help='Set the theme for the terminal.')
@click.option('--sessionfile', default='sessions.yaml',
              help='YAML file containing session configurations.')
def main(theme: str, sessionfile: str):
    """TerminalTelemetry - A modern terminal emulator."""
    # if debug:
    #     logger.setLevel(logging.DEBUG)
    #
    # # Insert WebEngine debugging arguments before creating QApplication
    # sys.argv.extend(['--webEngineArgs --remote-debugging-port=9222'])

    app = QApplication(sys.argv)
    app.setApplicationName("TerminalTelemetry")

    # Enable remote debugging
    # from PyQt6.QtCore import Qt
    # QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)

    # Create theme manager instance
    theme_manager = ThemeLibrary()

    # Validate theme
    if theme not in theme_manager.themes:
        logger.warning(f"Theme '{theme}' not found, using 'cyberpunk'")
        theme = 'cyberpunk'

    window = TermtelWindow(theme=theme, session_file=sessionfile)
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()