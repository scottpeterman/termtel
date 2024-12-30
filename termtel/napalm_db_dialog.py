from PyQt6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QHBoxLayout, QPushButton

from termtel.themes2 import LayeredHUDFrame


class NetworkDeviceDialog(QDialog):
    def __init__(self, selected_creds, parent=None):
        super().__init__(parent)
        # self.cred_manager = cred_manager

        # Get theme info from parent
        self.theme_manager = parent.theme_manager if hasattr(parent, 'theme_manager') else None
        self.current_theme = parent.theme if hasattr(parent, 'theme') else None
        self.selected_creds = selected_creds
        self.setup_ui()
        self.apply_theme()

    def setup_ui(self):
        """Initialize the UI components."""
        self.setWindowTitle("Network Device Connection")
        self.setModal(True)
        self.resize(400, 200)

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

        # Connection details form
        details_form = QFormLayout()

        self.host_input = QLineEdit()
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        if self.selected_creds:
            self.username_input.setText(self.selected_creds.get('username',''))
            self.password_input.setText(self.selected_creds.get('password',''))
        details_form.addRow("Host:", self.host_input)
        details_form.addRow("Username:", self.username_input)
        details_form.addRow("Password:", self.password_input)

        frame_layout.addLayout(details_form)

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

    def get_connection_data(self):
        """Return the connection data."""
        return {
            'host': self.host_input.text().strip(),
            'username': self.username_input.text(),
            'password': self.password_input.text()
        }

    def apply_theme(self):
        """Apply current theme styling."""
        if not self.theme_manager:
            return

        colors = self.theme_manager.get_colors(self.current_theme)

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
        for input_widget in [self.host_input, self.username_input, self.password_input]:
            input_widget.setStyleSheet(input_style)

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