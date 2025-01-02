# widgets/terminal_tabs.py
import socket

from PyQt6.QtWebEngineCore import QWebEngineProfile
from PyQt6.QtWidgets import (QTabWidget, QWidget, QVBoxLayout,
                             QMenu, QMessageBox, QSplitter)
from PyQt6.QtCore import QUrl, pyqtSignal, Qt, QTimer
import uuid
import logging
from typing import Dict, Optional, Tuple

from termtel.themes2 import terminal_themes
from termtel.widgets.qtssh_widget import Ui_Terminal

logger = logging.getLogger(__name__)
THEME_MAPPING = {
    "cyberpunk": "Cyberpunk",
    "dark_mode": "Dark",
    "light_mode": "Light",
    "retro_green": "Green",
    "retro_amber": "Amber",
    "neon_blue": "Neon"
}

class TerminalTabWidget(QTabWidget):
    """Widget managing multiple terminal tabs."""
    terminal_closed = pyqtSignal(str)  # Signal when a terminal is closed
    all_terminals_closed = pyqtSignal()  # Signal when all terminals are closed

    def __init__(self, server_port: int, parent=None):
        super().__init__(parent)
        self.server_port = server_port
        self.sessions: Dict[str, QWidget] = {}
        self.parent = parent
        self.current_term_theme = "Cyberpunk"  # Default
        if hasattr(self.parent, 'theme'):
            self.current_term_theme = self.parent.theme

        self.setup_ui()

    def get_mapped_terminal_theme(self, pyqt_theme: str) -> str:
        """Map PyQt theme names to terminal theme names."""
        theme_mapping = {
            "cyberpunk": "Cyberpunk",
            "dark_mode": "Dark",
            "light_mode": "Light",
            "retro_green": "Green",
            "retro_amber": "Amber",
            "neon_blue": "Neon"
        }
        return theme_mapping.get(pyqt_theme.lower(), "Cyberpunk")

    def setup_ui(self):
        """Initialize the tab widget UI."""
        self.setTabsClosable(True)
        self.setMovable(True)
        self.setDocumentMode(True)

        # Connect signals
        self.tabCloseRequested.connect(self.close_tab)

        # Set up context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def update_theme(self, theme_name: str):
        """Update terminal themes."""
        terminal_theme = self.get_mapped_terminal_theme(theme_name)
        self.current_term_theme = terminal_theme

        # Update all terminal instances
        for i in range(self.count()):
            tab = self.widget(i)
            if tab:
                terminal = tab.findChild(Ui_Terminal)
                if terminal:
                    self.apply_theme_to_terminal(terminal, theme_name)


    def test_socket_connection(self, host: str, port: str, timeout: int = 5) -> Tuple[bool, Optional[str]]:
        """Test if a socket connection can be established to the given host and port."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        try:
            sock.connect((host, int(port)))
            return True, None
        except socket.timeout:
            return False, "Connection timed out after 5 seconds"
        except ConnectionRefusedError:
            return False, "Connection refused - service may not be running on the specified port"
        except socket.gaierror:
            return False, "Could not resolve hostname"
        except ValueError:
            return False, "Invalid port number"
        except Exception as e:
            return False, str(e)
        finally:
            sock.close()

    def create_terminal(self, connection_data: Dict) -> str:
        """Create a new terminal tab."""
        session_id = connection_data.get('uuid', str(uuid.uuid4()))

        try:
            # Test socket connection first
            host = connection_data['host']
            port = connection_data.get('port', '22')

            success, error_message = self.test_socket_connection(host, port)
            if not success:
                QMessageBox.critical(
                    self,
                    "Connection Failed",
                    f"Failed to connect to {host}:{port}\nError: {error_message}"
                )
                return None

            # Create tab container
            tab_container = QWidget()
            layout = QVBoxLayout(tab_container)
            layout.setContentsMargins(0, 0, 0, 0)

            # Create Ui_Terminal instance
            hostinfo = {
                "host": connection_data['host'],
                "port": connection_data.get('port', '22'),
                "username": connection_data.get('username'),
                "password": connection_data.get('password'),
                "log_filename": f"./logs/session_{connection_data['host']}.log",
                "theme": self.get_mapped_terminal_theme(self.current_term_theme)
            }

            terminal = Ui_Terminal(hostinfo, parent=tab_container)
            layout.addWidget(terminal)

            # Theme will be applied when terminal is ready
            if hasattr(terminal, 'view'):
                self.apply_theme_to_terminal(terminal, self.current_term_theme)

            # Add to tab widget
            display_name = connection_data.get('display_name') or connection_data['host']
            index = self.addTab(tab_container, display_name)
            self.setCurrentIndex(index)

            # Store session
            self.sessions[session_id] = tab_container
            return session_id

        except Exception as e:
            logger.error(f"Failed to create terminal: {e}")
            raise

    def apply_theme_to_terminal(self, terminal, terminal_theme):
        """Apply theme to a specific terminal instance."""
        if hasattr(terminal, 'view'):
            theme_data = terminal_themes.get(THEME_MAPPING[terminal_theme], terminal_themes["Cyberpunk"])
            if theme_data and "js" in theme_data:
                # Check if terminal is ready before applying theme
                terminal.view.page().runJavaScript(
                    "typeof term !== 'undefined' && term !== null",
                    lambda result: self.handle_theme_check(result, terminal, theme_data["js"])
                )

    def handle_theme_check(self, is_ready: bool, terminal, theme_js: str):
        """Handle the terminal readiness check for theme application."""
        if is_ready:
            terminal.view.page().runJavaScript(
                theme_js,
                lambda result: print(f"Theme applied successfully")
            )
        else:
            # Retry after a short delay
            QTimer.singleShot(100, lambda: self.apply_theme_to_terminal(terminal, self.current_term_theme))
    def cleanup(self):
        """
        Cleanup method to properly close the terminal and free resources.
        """
        try:
            # Disconnect the backend if it exists
            if hasattr(self, 'backend'):
                self.backend.disconnect()

            # Clear the web channel
            if hasattr(self, 'channel'):
                self.channel.deregisterObject(self.backend)

            # Clean up the web view
            if hasattr(self, 'view'):
                self.view.setPage(None)
                self.view.deleteLater()

            # Clean up the URL scheme handler
            if hasattr(self, 'handler'):
                QWebEngineProfile.defaultProfile().removeUrlSchemeHandler(self.handler)
                self.handler.deleteLater()

        except Exception as e:
            print(f"Error during terminal cleanup: {e}")

    def close_tab(self, index: int):
        """Handle tab close request."""
        try:
            widget = self.widget(index)
            if widget:
                # Find session ID for this widget
                session_id = None
                for sid, w in self.sessions.items():
                    if w == widget:
                        session_id = sid
                        break

                # Clean up and remove the tab
                terminal = widget.findChild(Ui_Terminal)
                if terminal:
                    try:
                        terminal.cleanup()
                    except Exception as e:
                        logger.warning(f"Terminal cleanup failed: {e}")

                # Remove the tab first to prevent UI issues
                self.removeTab(index)

                # Delete the widget after cleanup
                widget.deleteLater()

                # Clean up session
                if session_id:
                    self.remove_session(session_id)

        except Exception as e:
            logger.error(f"Error closing tab: {e}")
    def remove_session(self, session_id: str):
        """Remove session from tracking."""
        if session_id in self.sessions:
            self.sessions.pop(session_id)
            self.terminal_closed.emit(session_id)
            if not self.sessions:
                self.all_terminals_closed.emit()

    def show_context_menu(self, position):
        index = self.tabBar().tabAt(position)
        if index >= 0:
            menu = QMenu(self)

            # Add theme submenu
            theme_menu = menu.addMenu("Terminal Theme")

            # Create theme actions
            for theme_name, theme_data in terminal_themes.items():
                action = theme_menu.addAction(theme_name)
                action.setCheckable(True)
                action.setChecked(theme_name == self.current_term_theme)
                action.triggered.connect(
                    lambda checked, tn=theme_name: self.change_terminal_theme(tn))

            menu.addSeparator()

            # Close action
            close_action = menu.addAction("Close")
            close_action.triggered.connect(lambda: self.close_tab(index))

            # Close others action
            close_others_action = menu.addAction("Close Others")
            close_others_action.triggered.connect(
                lambda: self.close_other_tabs(index)
            )

            # Close all action
            close_all_action = menu.addAction("Close All")
            close_all_action.triggered.connect(self.close_all_tabs)

            menu.exec(self.tabBar().mapToGlobal(position))

    def change_terminal_theme(self, theme_name: str):
        """Change theme for current terminal and save preference."""
        self.current_term_theme = theme_name
        if hasattr(self, 'view'):
            QTimer.singleShot(3000, lambda: self.view.page().runJavaScript(
                terminal_themes.get(THEME_MAPPING[self.current_term_theme], terminal_themes["Green"])["js"],
                lambda result: print(f"{self.current_term_theme} theme applied")
            ))

        self.update_theme(theme_name)

    def close_other_tabs(self, keep_index: int):
        """Close all tabs except the specified one."""
        for i in range(self.count() - 1, -1, -1):
            if i != keep_index:
                self.close_tab(i)

    def close_all_tabs(self):
        """Close all tabs."""
        for i in range(self.count() - 1, -1, -1):
            self.close_tab(i)

    def cleanup_all(self):
        """Clean up all terminals on application exit."""
        try:
            self.close_all_tabs()
            self.sessions.clear()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")