# widgets/terminal_tabs.py
from time import sleep

from PyQt6.QtWidgets import (QTabWidget, QWidget, QVBoxLayout,
                             QMenu, QMessageBox)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl, pyqtSignal, Qt, QObject, QThread
import uuid
import logging
from typing import Dict, Optional

from discovery.device_discovery import DeviceDiscovery
from discovery.network_mapper import NetworkMapper
from themes2 import terminal_themes

logger = logging.getLogger(__name__)

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QMenu, QMessageBox, QSplitter)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl, pyqtSignal, Qt, QTimer
import uuid
import logging
from typing import Dict, Optional

from widgets.telemetry_widget import DiscoveryOutput
from widgets.map_preview import MapPreview

logger = logging.getLogger(__name__)


class TerminalTab(QWidget):
    """Individual terminal tab containing terminal, telemetry, and map preview."""

    closed = pyqtSignal(str)  # Signal emitted when tab is closed with session_id

    def __init__(self, session_id: str, connection_data: Dict, server_port: int, parent=None, parent_ref=None):
        super().__init__(parent)
        self.session_id = session_id
        self.connection_data = connection_data
        self.server_port = server_port
        self.web_view = None
        self.resizeTimer = None
        self.loaded = False

        self.parent_ref = parent_ref
        self.parent = parent
        self.setup_ui()

    def setup_ui(self):
        """Initialize the terminal tab UI with split layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create horizontal splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # Left side: Terminal container
        terminal_container = QWidget()
        terminal_layout = QVBoxLayout(terminal_container)
        terminal_layout.setContentsMargins(0, 0, 0, 0)

        # Create web view for terminal
        self.web_view = QWebEngineView()
        self.web_view.page().setBackgroundColor(Qt.GlobalColor.transparent)
        terminal_layout.addWidget(self.web_view)

        # Right side: Telemetry and map preview
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(2, 2, 2, 2)
        right_layout.setSpacing(2)

        # Add telemetry widget
        self.telemetry = DiscoveryOutput()

        right_layout.addWidget(self.telemetry)

        # Add map preview
        # self.map_preview = MapPreview()
        # right_layout.addWidget(self.map_preview)

        # Add both sides to splitter
        splitter.addWidget(terminal_container)
        splitter.addWidget(right_panel)

        # Set initial sizes (70% terminal, 30% right panel)
        total_width = self.width()
        splitter.setSizes([int(total_width * 0.8), int(total_width * 0.2)])

        # Set dark theme styles
        right_panel.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
            }
        """)
        # right_panel.setMaximumWidth(500)
        total_width = self.parent_ref.width
        max_width = int(total_width * 0.4)
        right_panel.setMaximumWidth(max_width)
        right_panel.setVisible(False)
        # Load terminal page
        base_url = QUrl(f"http://127.0.0.1:{self.server_port}/terminal")
        self.web_view.setUrl(base_url)
        self.web_view.loadFinished.connect(self.initialize_terminal)



        # Install event filter for resize handling
        self.installEventFilter(self)

    def eventFilter(self, obj, event):
        """Handle resize events with debouncing."""
        if obj == self and event.type() == event.Type.Resize:
            if self.resizeTimer is not None:
                self.resizeTimer.stop()

            self.resizeTimer = QTimer()
            self.resizeTimer.setSingleShot(True)
            self.resizeTimer.timeout.connect(self.handle_resize)
            self.resizeTimer.start(1500)

        return super().eventFilter(obj, event)

    def handle_resize(self):
        """Handle the actual resize after debouncing."""
        if self.web_view:
            js_code = """
            if (window.currentTerminal && window.currentWebSocket) {
                const fitAddon = new FitAddon.FitAddon();
                window.currentTerminal.loadAddon(fitAddon);
                fitAddon.fit();

                const cols = window.currentTerminal.cols;
                const rows = window.currentTerminal.rows;

                window.currentWebSocket.send(JSON.stringify({
                    type: 'resize',
                    cols: cols,
                    rows: rows
                }));
            }
            """
            self.web_view.page().runJavaScript(js_code)

    def initialize_terminal(self, success: bool):
        """Initialize the terminal connection after page load."""
        print(f"web content loaded!")
        if success:
            # Get the current terminal theme
            current_theme = "Cyberpunk"  # Default theme
            if hasattr(self.parent, 'current_term_theme'):
                current_theme = self.parent.current_term_theme

            # Get theme data
            theme_data = terminal_themes.get(current_theme, terminal_themes["Cyberpunk"])

            js_code = f"""
            const terminal = new Terminal({{
                cursorBlink: true,
                cursorStyle: 'block',
                fontFamily: 'monospace',
                fontSize: 14
            }});

            const fitAddon = new FitAddon.FitAddon();
            terminal.loadAddon(fitAddon);

            const container = document.getElementById('terminal-container');
            terminal.open(container);
            fitAddon.fit();

            window.currentTerminal = terminal;
            {theme_data["js"]}  // Apply the theme

            const ws = new WebSocket(`ws://{self.web_view.url().host()}:{self.web_view.url().port()}/ws/terminal/{self.session_id}`);
            window.currentWebSocket = ws;

            ws.onopen = () => {{
                terminal.writeln('Connecting to {self.connection_data["host"]}...');
                ws.send(JSON.stringify({{
                    type: 'connect',
                    hostname: '{self.connection_data["host"]}',
                    port: {self.connection_data["port"]},
                    username: '{self.connection_data["username"]}',
                    password: '{self.connection_data["password"]}'
                }}));
            }};

            ws.onmessage = (event) => {{
                const msg = JSON.parse(event.data);
                if (msg.type === 'ssh_output') {{
                    terminal.write(atob(msg.data));
                }} else if (msg.type === 'error') {{
                    terminal.writeln('\\x1b[31m' + msg.data + '\\x1b[0m');  // Red text for errors
                }}
            }};

            ws.onerror = (error) => {{
                terminal.writeln('\\x1b[31mWebSocket error occurred\\x1b[0m');
            }};

            ws.onclose = () => {{
                terminal.writeln('\\x1b[31mConnection closed\\x1b[0m');
            }};

            terminal.onData(data => {{
                if (ws.readyState === WebSocket.OPEN) {{
                    ws.send(JSON.stringify({{
                        type: 'input',
                        data: data
                    }}));
                }}
            }});

            const resizeObserver = new ResizeObserver(() => {{
                if (container.offsetWidth > 0 && container.offsetHeight > 0) {{
                    fitAddon.fit();
                    const cols = terminal.cols;
                    const rows = terminal.rows;
                    ws.send(JSON.stringify({{
                        type: 'resize',
                        cols: cols,
                        rows: rows
                    }}));
                }}
            }});
            resizeObserver.observe(container);
            """
            self.web_view.page().runJavaScript(js_code)
            self.parent.parent.theme
            self.theme_timer = QTimer(self)
            self.theme_timer.setSingleShot(True)
            self.theme_timer.timeout.connect(
                lambda: self.parent.update_theme(self.parent.parent.theme)
            )
            self.theme_timer.start(3000)

        else:
            logger.error(f"Failed to load terminal page for session {self.session_id}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to load terminal page for {self.connection_data['host']}"
            )

    def start_discovery(self):
        """Handle discovery request"""
        print(f"Starting discovery with connection data:")
        print(f"Host: {self.connection_data['host']}")
        print(f"Username: {self.connection_data['username']}")
        print(f"Password length: {len(self.connection_data['password'])}")

        self.telemetry.set_discovery_enabled(False)
        self.telemetry.update_status("Discovery in progress...")

        # Create discovery thread
        self.discovery_thread = QThread()
        self.discovery_worker = DeviceDiscoveryWorker(
            connection_data=self.connection_data,
            template_db='templates/tfsm_templates.db'
        )

        # Set up worker connections
        self.discovery_worker.moveToThread(self.discovery_thread)
        self.discovery_thread.started.connect(self.discovery_worker.run)
        self.discovery_worker.finished.connect(self.discovery_thread.quit)
        self.discovery_worker.finished.connect(self.discovery_worker.deleteLater)
        self.discovery_thread.finished.connect(self.discovery_thread.deleteLater)

        self.discovery_worker.result_ready.connect(self.handle_discovery_complete)
        self.discovery_worker.error.connect(self.handle_discovery_error)

        self.discovery_thread.start()

    def handle_discovery_complete(self, fingerprint):
        """Process discovery results"""
        if fingerprint:
            content = {
                'device_type': fingerprint.device_type,
                'confidence_score': fingerprint.confidence_score,
                'template': fingerprint.template_name,
                'processing_time': fingerprint.processing_time,
                'parsed_data': fingerprint.parsed_data[0] if fingerprint.parsed_data else {}
            }
            self.telemetry.update_content(content)
            self.telemetry.update_status(
                f"✓ {fingerprint.device_type} ({fingerprint.confidence_score:.0f}% match)",
                True
            )

            # Check for neighbor data and start mapping
            if (fingerprint.device_type.lower() != 'linux' and
                    fingerprint.parsed_data and
                    'NEIGHBOR_DATA' in fingerprint.parsed_data[0]):
                self.start_mapping(
                    fingerprint.parsed_data[0]['NEIGHBOR_DATA'],
                    self.connection_data['host']
                )
        else:
            self.telemetry.show_error("No device match found")
            self.telemetry.update_status("✗ No match found", False)

        self.telemetry.set_discovery_enabled(True)

    def start_mapping(self, neighbor_data: str, start_node: str):
        """Start the network mapping process"""
        try:
            self.mapper = NetworkMapper()
            self.mapper.map_ready.connect(self.handle_map_ready)
            self.mapper.error.connect(self.handle_map_error)
            self.mapper.create_map(neighbor_data, start_node)
        except Exception as e:
            self.handle_map_error(str(e))

    def handle_map_ready(self, map_file: str):
        """Handle completed map generation"""
        try:
            self.map_preview.update_map(map_file)
        except Exception as e:
            logger.error(f"Error displaying map: {str(e)}")
            self.handle_map_error(f"Error displaying map: {str(e)}")

    def handle_map_error(self, error_msg: str):
        """Handle mapping errors"""
        logger.error(f"Mapping error: {error_msg}")
        # Could add error indication to map preview area
    def handle_discovery_error(self, error_msg: str):
        """Handle discovery errors"""
        self.telemetry.show_error(error_msg)
        self.telemetry.update_status("✗ Discovery failed", False)
        self.telemetry.set_discovery_enabled(True)

    def cleanup(self):
        """Clean up resources when tab is closed."""
        if self.web_view:
            self.web_view.page().runJavaScript("""
                if (window.currentWebSocket) {
                    window.currentWebSocket.close();
                }
                if (window.currentTerminal) {
                    window.currentTerminal.dispose();
                }
            """)
            self.web_view.setUrl(QUrl("about:blank"))
            self.web_view.deleteLater()
        self.closed.emit(self.session_id)

class TerminalTabWidget(QTabWidget):
    """Widget managing multiple terminal tabs."""
    terminal_closed = pyqtSignal(str)  # Signal when a terminal is closed
    all_terminals_closed = pyqtSignal()  # Signal when all terminals are closed

    def __init__(self, server_port: int, parent=None):
        super().__init__(parent)
        self.server_port = server_port
        self.sessions: Dict[str, TerminalTab] = {}
        self.parent = parent
        self.current_term_theme = "Cyberpunk"  # Default
        if hasattr(self.parent, 'settings_manager'):
            self.current_term_theme = self.parent.settings_manager.get_term_theme()

        self.setup_ui()

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
        # if hasattr(self.parent(), 'theme_manager'):
        colors = self.parent.theme_manager.get_colors(theme_name)

            # Apply theme to tab widget
        tab_stylesheet = f"""
            QTabWidget::pane {{
                border: 1px solid {colors['border']};
                background: {colors['darker_bg']};
            }}
            QTabBar::tab {{
                background: {colors['darker_bg']};
                color: {colors['text']};
                padding: 8px 12px;
                border: 1px solid {colors['border']};
                min-width: 100px;
                font-family: "Courier New";
            }}
            QTabBar::tab:selected {{
                background: {colors['background']};
                border-bottom: 2px solid {colors['line']};
                color: {colors['text']};
                font-weight: bold;
            }}
            QTabBar::tab:hover:!selected {{
                background: {colors['button_hover']};
            }}
        """

        if theme_name == "light_mode":
            tab_stylesheet += """
                QTabBar::tab {
                    color: #000000;  /* Force black text for light mode */
                }
                QTabBar::tab:selected {
                    color: #000000;  /* Keep text black when selected */
                }
            """


        self.setStyleSheet(tab_stylesheet)

        # Update existing terminals
        for i in range(self.count()):
            terminal = self.widget(i)
            if hasattr(terminal, 'update_theme'):
                terminal.update_theme(theme_name)

    def create_terminal(self, connection_data: Dict) -> str:
        """Create a new terminal tab."""
        session_id = connection_data['uuid'] or str(uuid.uuid4())

        # Create new terminal tab
        try:
            terminal = TerminalTab(session_id, connection_data, self.server_port, parent=self, parent_ref=self.parent)
            self.update_theme(self.parent.theme)
            terminal.closed.connect(self.remove_session)
            # Apply saved terminal theme after a delay to ensure terminal is ready
            if terminal.web_view:
                theme_data = terminal_themes.get(self.current_term_theme)
                if theme_data:
                    QTimer.singleShot(3000, lambda: terminal.web_view.page().runJavaScript(
                        theme_data["js"],
                        lambda result: print(f"{self.current_term_theme} theme applied")
                    ))
        except Exception as e:
            print(e)


        # Add to tab widget
        display_name = connection_data.get('display_name') or connection_data['host']
        index = self.addTab(terminal, display_name)
        self.setCurrentIndex(index)

        # self.update_theme(self.parent.theme)
        # Store session
        self.sessions[session_id] = terminal
        logger.info(f"Created new terminal session {session_id} for {display_name}")
        return session_id

    def close_tab(self, index: int):
        """Handle tab close request."""
        widget = self.widget(index)
        if isinstance(widget, TerminalTab):
            widget.cleanup()
        self.removeTab(index)

    def remove_session(self, session_id: str):
        """Remove session from tracking."""
        self.sessions.pop(session_id, None)
        logger.info(f"Removed terminal session {session_id}")

    def show_context_menu(self, position):
        index = self.tabBar().tabAt(position)
        if index >= 0:
            terminal_tab = self.widget(index)
            menu = QMenu(self)

            # Add theme submenu
            theme_menu = menu.addMenu("Terminal Theme")

            def create_theme_action(theme_name: str, theme_data: dict, terminal_tab):
                def theme_handler():
                    if terminal_tab.web_view:
                        terminal_tab.web_view.page().runJavaScript(
                            theme_data["js"],
                            lambda result: print(f"{theme_name} theme applied")
                        )
                        # Save the theme preference if settings manager exists
                        self.current_term_theme = theme_name
                        if hasattr(self.parent, 'settings_manager'):
                            self.parent.settings_manager.set_term_theme(theme_name)

                theme_action = theme_menu.addAction(theme_name)
                theme_action.triggered.connect(theme_handler)
                # Add checkmark to current theme
                if theme_name == self.current_term_theme:
                    theme_action.setCheckable(True)
                    theme_action.setChecked(True)

            # Create theme actions
            for theme_name, theme_data in terminal_themes.items():
                create_theme_action(theme_name, theme_data, terminal_tab)

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
            for session_id, terminal in self.sessions.items():
                terminal.cleanup()
            self.sessions.clear()
        except:
            pass


# DeviceDiscoveryWorker class:
class DeviceDiscoveryWorker(QObject):
    result_ready = pyqtSignal(object)
    error = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, connection_data: Dict, template_db: str):
        super().__init__()
        self.connection_data = connection_data
        self.template_db = template_db

    def run(self):
        print(f"Worker starting discovery for {self.connection_data['host']}")
        print(f"Using username: {self.connection_data['username']}")
        try:
            discovery = DeviceDiscovery(self.template_db, verbose=True)
            result = discovery.process_device(
                host=self.connection_data['host'],
                username=self.connection_data['username'],
                password=self.connection_data['password'],
                ssh_timeout=60
            )
            if result:
                print(f"Discovery successful for {self.connection_data['host']}")
                self.result_ready.emit(result)
            else:
                error_msg = f"Discovery failed for {self.connection_data['host']} - no result returned"
                print(error_msg)
                self.error.emit(error_msg)
        except Exception as e:
            error_msg = f"Discovery error for {self.connection_data['host']}: {str(e)}"
            print(error_msg)
            self.error.emit(error_msg)
        finally:
            self.finished.emit()

