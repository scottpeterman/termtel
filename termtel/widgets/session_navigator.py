"""
Termtel - Session Navigator Widget
Updated to use NewSessionDialog for connections
"""
import uuid
import yaml
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QLabel, QCheckBox, QGroupBox, QMenu,
    QMessageBox, QFormLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
import logging
from typing import Optional

from termtel.themes2 import LayeredHUDFrame
from termtel.widgets.new_session_dialog import NewSessionDialog
from termtel.helpers.credslib import SecureCredentials

logger = logging.getLogger('termtel.session_navigator')

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QGroupBox
)
from PyQt6.QtCore import pyqtSignal
from typing import Optional
from termtel.helpers.credslib import SecureCredentials
from termtel.widgets.new_session_dialog import NewSessionDialog
from termtel.themes2 import LayeredHUDFrame


class QuickConnectWidget(LayeredHUDFrame):
    """Quick connect widget with HUD frame styling."""
    connect_requested = pyqtSignal(dict)

    def __init__(self, cred_manager: Optional[SecureCredentials] = None, parent=None, theme_manager=None,
                 theme_name="cyberpunk"):
        LayeredHUDFrame.__init__(self, parent, theme_manager=theme_manager, theme_name=theme_name)
        self.cred_manager = cred_manager
        self.setup_quick_connect()

    def setup_quick_connect(self):
        """Add Quick Connect UI elements to the frame."""
        main_layout = QVBoxLayout()

        # Add header
        self.header_label = QLabel("Quick Connect")
        self.header_label.setStyleSheet("""
            font-family: "Courier New";
            font-weight: bold;
        """)
        main_layout.addWidget(self.header_label)

        # Add connection button
        self.new_connection_btn = QPushButton("NEW CONNECTION")
        self.new_connection_btn.clicked.connect(self.handle_new_connection)
        main_layout.addWidget(self.new_connection_btn)

        # Add to content layout from parent
        self.content_layout.addLayout(main_layout)

    def handle_new_connection(self):
        """Handle new connection request."""
        if self.cred_manager:
            connection_data = NewSessionDialog.get_connection(self.cred_manager, self)
            if connection_data:
                self.connect_requested.emit(connection_data)

    def set_theme(self, theme_name: str):
        """Override set_theme to include our custom elements."""
        super().set_theme(theme_name)

        if self.theme_manager:
            colors = self.theme_manager.get_colors(theme_name)

            # Update header label color
            self.header_label.setStyleSheet(f"""
                font-family: "Courier New";
                font-weight: bold;
                color: {colors['text']};
            """)

            # Style the button based on theme
            if theme_name == "light_mode":
                self.new_connection_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {colors['primary']};
                        color: {colors['text']};
                        border: 1px solid {colors['border']};
                        padding: 8px 15px;
                        font-family: "Courier New";
                        text-transform: uppercase;
                        min-height: 30px;
                    }}
                    QPushButton:hover {{
                        background-color: {colors['button_hover']};
                        border: 1px solid {colors['border']};
                    }}
                    QPushButton:pressed {{
                        background-color: {colors['button_pressed']};
                        border: 1px solid {colors['border']};
                    }}
                """)
            else:
                self.new_connection_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {colors['darker_bg']};
                        color: {colors['text']};
                        border: 1px solid {colors['border_light']};
                        padding: 8px 15px;
                        font-family: "Courier New";
                        text-transform: uppercase;
                        min-height: 30px;
                    }}
                    QPushButton:hover {{
                        background-color: {colors['button_hover']};
                        border: 1px solid {colors['text']};
                    }}
                    QPushButton:pressed {{
                        background-color: {colors['button_pressed']};
                        border: 1px solid {colors['text']};
                    }}
                """)
class SessionNavigator(QWidget):
    connect_requested = pyqtSignal(dict)

    def __init__(self, parent=None, cred_manager: Optional[SecureCredentials] = None):
        super().__init__(parent)
        self.cred_manager = cred_manager
        self.sessions_file = Path('sessions/sessions.yaml')
        self.parent = parent
        self.setup_ui()
        self.current_theme = parent.theme
        if hasattr(parent, 'theme_manager'):
            self.update_theme(self.current_theme)
        self.load_sessions()

    def setup_ui(self):
        """Initialize UI with HUD frames."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        self.current_theme = self.parent.theme
        # Create main HUD frame
        if hasattr(self.parent, 'theme_manager'):
            self.main_frame = LayeredHUDFrame(self, theme_manager=self.parent.theme_manager,
                                              theme_name=self.current_theme)
        else:
            self.main_frame = LayeredHUDFrame(self)

        main_layout = QVBoxLayout()
        self.main_frame.content_layout.addLayout(main_layout)

        # Search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search sessions...")
        self.search_box.textChanged.connect(self.handle_search)
        main_layout.addWidget(self.search_box)

        # Session tree
        self.session_tree = QTreeWidget()
        self.session_tree.setHeaderLabel("SESSIONS")
        self.session_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.session_tree.customContextMenuRequested.connect(self.show_context_menu)
        self.session_tree.itemDoubleClicked.connect(self.handle_session_activation)
        main_layout.addWidget(self.session_tree)

        layout.addWidget(self.main_frame)

        # Quick Connect in its own HUD frame
        self.quick_connect = QuickConnectWidget(
            cred_manager=self.cred_manager,
            parent=self,
            theme_manager=self.parent.theme_manager if hasattr(self.parent, 'theme_manager') else None,
            theme_name=self.current_theme
        )
        self.quick_connect.connect_requested.connect(self.handle_quick_connect)
        layout.addWidget(self.quick_connect)

    def update_theme(self, theme_name: str):
        """Update theme-specific styling"""
        self.current_theme = theme_name
        if hasattr(self.parent, 'theme_manager'):
            colors = self.parent.theme_manager.get_colors(theme_name)

            # Update main frame theme
            if hasattr(self.main_frame, 'set_theme'):
                self.main_frame.set_theme(theme_name)

            # Style the search box
            self.search_box.setStyleSheet(f"""
                QLineEdit {{
                    background-color: {colors['darker_bg']};
                    color: {colors['text']};
                    border: 1px solid {colors['border_light']};
                    border-radius: 0;
                    padding: 5px;
                    font-family: "Courier New";
                }}
                QLineEdit:focus {{
                    border: 1px solid {colors['text']};
                }}
            """)

            # Style the session tree while preserving native arrows
            self.session_tree.setStyleSheet(f"""
                QTreeWidget {{
                    background-color: {colors['darker_bg']};
                    color: {colors['text']};
                    border: 1px solid {colors['border_light']};
                    font-family: "Courier New";
                    outline: none;
                    padding: 5px;
                }}
                QTreeWidget::item {{
                    padding: 2px;
                    color: {colors['text']};
                }}
                QTreeWidget::item:selected {{
                    background-color: {colors['selected_bg']};
                }}
                QTreeWidget::item:hover {{
                    background-color: {colors['selected_bg']};
                }}
                QTreeWidget::branch:selected {{
                    background-color: {colors['selected_bg']};
                }}
                QHeaderView::section {{
                    background-color: {colors['darker_bg']};
                    color: {colors['text']};
                    padding: 5px;
                    border: none;
                    font-family: "Courier New";
                }}
            """)

            # Update quick connect theme
            if hasattr(self.quick_connect, 'set_theme'):
                self.quick_connect.set_theme(theme_name)

    def load_sessions(self, file_content_to_load=None):
        """Load sessions from the YAML file."""
        try:
            if not self.sessions_file.exists():
                logger.warning(f"Sessions file not found: {self.sessions_file}")
                return

            if file_content_to_load is None:
                self.parent.session_file_with_path = self.sessions_file
                with open(self.sessions_file) as f:
                    sessions_data = yaml.safe_load(f)
            else:
                sessions_data = file_content_to_load

            self.session_tree.clear()

            for folder in sessions_data:
                folder_item = QTreeWidgetItem(self.session_tree)
                folder_item.setText(0, folder['folder_name'])
                folder_item.setData(0, Qt.ItemDataRole.UserRole, {'type': 'folder'})

                for session in folder.get('sessions', []):
                    session_item = QTreeWidgetItem(folder_item)
                    session_item.setText(0, session.get('display_name', session['host']))
                    session_item.setData(0, Qt.ItemDataRole.UserRole, {
                        'type': 'session',
                        'data': session
                    })

            # self.session_tree.expandAll()

            logger.info("Sessions loaded successfully")

        except Exception as e:
            logger.error(f"Error loading sessions: {str(e)}")
            QMessageBox.warning(self, "Error", f"Failed to load sessions: {str(e)}")

    def handle_search(self, text):
        """Filter the session tree based on search text."""
        def match_item(item, text):
            if not text:
                return True
            return text.lower() in item.text(0).lower()


            # Local search
        for folder_idx in range(self.session_tree.topLevelItemCount()):
            folder_item = self.session_tree.topLevelItem(folder_idx)
            folder_visible = False

            for session_idx in range(folder_item.childCount()):
                session_item = folder_item.child(session_idx)
                matches = match_item(session_item, text)
                session_item.setHidden(not matches)
                folder_visible = folder_visible or matches

            folder_item.setHidden(not folder_visible)

    def show_context_menu(self, position):
        """Show context menu for session items."""
        item = self.session_tree.itemAt(position)
        if not item:
            return

        item_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not item_data or item_data['type'] != 'session':
            return

        menu = QMenu(self)
        connect_action = menu.addAction("Connect")
        connect_action.triggered.connect(lambda: self.handle_session_activation(item))

        menu.exec(self.session_tree.viewport().mapToGlobal(position))

    def handle_session_activation(self, item, column=0):
        """Handle session activation (double-click or context menu)."""
        item_data = item.data(0, Qt.ItemDataRole.UserRole)
        if item_data and item_data['type'] == 'session':
            session_data = item_data['data']

            # Show the new session dialog with pre-filled data
            if self.cred_manager:
                dialog = NewSessionDialog(self.cred_manager, self)
                dialog.host_input.setText(session_data['host'])
                dialog.port_input.setText(str(session_data.get('port', 22)))
                dialog.username_input.setText(session_data.get('username', ''))
                dialog.password_input.setText(session_data.get('password', ''))

                if dialog.exec() == dialog.DialogCode.Accepted:
                    updated_connection = dialog.get_connection_data()
                    updated_connection['display_name'] = session_data.get('display_name', updated_connection.get('host','not set' ))
                    self.connect_requested.emit(updated_connection)

    def handle_quick_connect(self, connection_data):
        """Forward the quick connect signal."""
        self.connect_requested.emit(connection_data)