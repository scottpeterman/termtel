from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QTabWidget, QWidget,
                             QComboBox, QFormLayout, QMessageBox)
from PyQt6.QtCore import Qt
import logging
from typing import Dict, Optional
from pathlib import Path
import uuid

from termtel.helpers.credslib import SecureCredentials
from termtel.themes2 import LayeredHUDFrame

logger = logging.getLogger(__name__)


class NewSessionDialog(QDialog):
    def __init__(self, cred_manager: SecureCredentials, parent=None):
        super().__init__(parent)
        self.cred_manager = cred_manager
        self.selected_credential = None

        # Get theme information from parent
        try:
            self.theme_manager = parent.parent.theme_manager if hasattr(parent, 'parent') else None
            self.current_theme = parent.parent.theme if hasattr(parent, 'parent') else parent.theme
        except:
            try:
                self.theme_manager = parent.theme_manager
                self.current_theme = parent.theme_name
            except:
                pass


        self.setup_ui()
        self.load_credentials()
        self.apply_theme()

    def setup_ui(self):
        """Initialize the UI components."""
        self.setWindowTitle("New Session")
        self.setModal(True)
        self.resize(400, 300)

        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)

        # Main HUD frame
        if self.theme_manager:
            self.main_frame = LayeredHUDFrame(self, theme_manager=self.theme_manager, theme_name=self.current_theme)
        else:
            self.main_frame = LayeredHUDFrame(self)

        frame_layout = QVBoxLayout()
        self.main_frame.content_layout.addLayout(frame_layout)

        # Credentials section
        creds_group = QWidget()
        creds_layout = QVBoxLayout(creds_group)

        # Saved credentials selector
        saved_creds_layout = QHBoxLayout()
        self.creds_label = QLabel("Saved Credentials:")
        saved_creds_layout.addWidget(self.creds_label)
        self.creds_combo = QComboBox()
        self.creds_combo.currentIndexChanged.connect(self.on_credential_selected)
        saved_creds_layout.addWidget(self.creds_combo)
        creds_layout.addLayout(saved_creds_layout)

        # Connection details
        details_form = QFormLayout()

        self.host_input = QLineEdit()
        self.port_input = QLineEdit("22")
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.display_name_input = QLineEdit()

        # Labels
        self.host_label = QLabel("Host:")
        self.port_label = QLabel("Port:")
        self.username_label = QLabel("Username:")
        self.password_label = QLabel("Password:")
        self.display_name_label = QLabel("Display Name:")

        details_form.addRow(self.host_label, self.host_input)
        details_form.addRow(self.port_label, self.port_input)
        details_form.addRow(self.username_label, self.username_input)
        details_form.addRow(self.password_label, self.password_input)
        details_form.addRow(self.display_name_label, self.display_name_input)

        creds_layout.addLayout(details_form)
        frame_layout.addWidget(creds_group)

        # Buttons
        button_layout = QHBoxLayout()
        self.connect_button = QPushButton("CONNECT")
        self.connect_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("CANCEL")
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(self.connect_button)
        button_layout.addWidget(self.cancel_button)

        frame_layout.addLayout(button_layout)
        layout.addWidget(self.main_frame)

    def get_connection_data(self) -> Dict:
        """Return the connection data."""
        host = self.host_input.text().strip()
        if not host:
            raise ValueError("Host is required")

        # Generate display name if not provided
        display_name = self.display_name_input.text().strip()
        if not display_name:
            display_name = f"{host}"

        connection_data = {
            'host': host,
            'port': int(self.port_input.text() or 22),
            'username': self.username_input.text(),
            'password': self.password_input.text(),
            'display_name': display_name,
            'uuid': str(uuid.uuid4())
        }

        return connection_data

    def load_credentials(self):
        """Load saved credentials into the combo box."""
        try:
            if not (self.cred_manager.is_initialized and self.cred_manager.is_unlocked()):
                logger.warning("Credential manager not initialized or unlocked")
                return

            creds_path = self.cred_manager.config_dir / "credentials.yaml"
            if not creds_path.exists():
                logger.warning("No credentials file found")
                return

            creds_list = self.cred_manager.load_credentials(creds_path)

            self.creds_combo.clear()
            self.creds_combo.addItem("Manual Entry", None)

            for cred in creds_list:
                display_name = cred.get('display_name', cred.get('username', 'Unknown'))
                self.creds_combo.addItem(display_name, cred)

        except Exception as e:
            logger.error(f"Failed to load credentials: {e}")
            self.creds_combo.setEnabled(False)

    @staticmethod
    def get_connection(cred_manager: SecureCredentials, parent=None) -> Optional[Dict]:
        """Static method to create and show the dialog."""
        dialog = NewSessionDialog(cred_manager, parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                return dialog.get_connection_data()
            except ValueError as e:
                QMessageBox.warning(parent, "Invalid Input", str(e))
                return None
        return None

    def apply_theme(self):
        """Apply current theme to all widgets."""
        if not self.theme_manager:
            return

        colors = self.theme_manager.get_colors(self.current_theme)

        # Dialog styling
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {colors['background']};
                color: {colors['text']};
            }}
        """)

        # Style labels
        label_style = f"""
            QLabel {{
                color: {colors['text']};
                font-family: "Courier New";
            }}
        """
        for label in [self.creds_label, self.host_label, self.port_label,
                      self.username_label, self.password_label, self.display_name_label]:
            label.setStyleSheet(label_style)

        # Style inputs
        input_style = f"""
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
        """
        for input_widget in [self.host_input, self.port_input, self.username_input,
                             self.password_input, self.display_name_input]:
            input_widget.setStyleSheet(input_style)

        # Style combo box
        self.creds_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {colors['darker_bg']};
                color: {colors['text']};
                border: 1px solid {colors['border_light']};
                border-radius: 0;
                padding: 5px;
                font-family: "Courier New";
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border: 2px solid {colors['text']};
                width: 6px;
                height: 6px;
                border-top: none;
                border-right: none;
                transform: rotate(-45deg);
            }}
            QComboBox QAbstractItemView {{
                background-color: {colors['darker_bg']};
                color: {colors['text']};
                selection-background-color: {colors['selected_bg']};
                selection-color: {colors['text']};
                border: 1px solid {colors['border_light']};
            }}
        """)

        # Style buttons
        button_style = f"""
            QPushButton {{
                background-color: {colors['darker_bg']};
                color: {colors['text']};
                border: 1px solid {colors['border_light']};
                padding: 8px 15px;
                font-family: "Courier New";
                text-transform: uppercase;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: {colors['button_hover']};
                border: 1px solid {colors['text']};
            }}
            QPushButton:pressed {{
                background-color: {colors['button_pressed']};
                border: 1px solid {colors['text']};
            }}
        """
        self.connect_button.setStyleSheet(button_style)
        self.cancel_button.setStyleSheet(button_style)

    def on_credential_selected(self, index):
        """Handle credential selection from combo box."""
        cred_data = self.creds_combo.itemData(index)
        if cred_data:
            # Fill in the form with saved credentials
            self.username_input.setText(cred_data['username'])
            self.password_input.setText(cred_data['password'])
            if 'display_name' in cred_data:
                self.display_name_input.setText(cred_data['display_name'])
        else:
            # Clear the form for manual entry
            self.username_input.clear()
            self.password_input.clear()
            self.display_name_input.clear()