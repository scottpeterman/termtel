"""
Termtel - Dialog Widgets
Common dialog boxes used throughout the application.
"""
from PyQt6.QtWidgets import QDialog, QFormLayout, QLineEdit, QDialogButtonBox
from PyQt6.QtCore import Qt
import uuid


class SSHCredentialsDialog(QDialog):
    def __init__(self, parent=None, session_data=None):
        super().__init__(parent)
        self.session_data = session_data or {}
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("SSH Credentials")
        layout = QFormLayout(self)

        # Create input fields
        self.username = QLineEdit(self)
        self.username.setText(self.session_data.get('username', ''))

        self.password = QLineEdit(self)
        self.password.setEchoMode(QLineEdit.EchoMode.Password)

        # Add fields to layout
        layout.addRow("Username:", self.username)
        layout.addRow("Password:", self.password)

        # Add buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            Qt.Orientation.Horizontal,
            self
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_credentials(self):
        return {
            'username': self.username.text(),
            'password': self.password.text(),
            'host': self.session_data.get('host'),
            'port': self.session_data.get('port', 22),
            'display_name': self.session_data.get('display_name', self.session_data.get('host')),
            'uuid': str(uuid.uuid4())
        }