from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QTextEdit, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QTextCharFormat, QFont


class DiscoveryOutput(QWidget):
    """Right panel showing device discovery results with styled output"""

    # Signal emitted when discover button is clicked
    discovery_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)

        # Header with discover button and status
        header = QHBoxLayout()

        # Discover button with icon
        self.discover_btn = QPushButton("🔍 Discover")
        self.discover_btn.setFixedWidth(120)
        self.discover_btn.clicked.connect(self.discovery_requested.emit)
        self.discover_btn.setStyleSheet("""
            QPushButton {
                background-color: #2D2D2D;
                border: none;
                border-radius: 4px;
                padding: 5px 10px;
                color: #FFFFFF;
            }
            QPushButton:hover {
                background-color: #3D3D3D;
            }
            QPushButton:pressed {
                background-color: #404040;
            }
            QPushButton:disabled {
                background-color: #1D1D1D;
                color: #666666;
            }
        """)

        # Status label
        self.status_label = QLabel()
        self.status_label.setStyleSheet("QLabel { color: #4EC9B0; }")  # Default to success color

        header.addWidget(self.discover_btn)
        header.addWidget(self.status_label)
        header.addStretch()

        # Text area for results
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)

        self.text_area.setFrameStyle(QFrame.Shape.NoFrame)
        self.text_area.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #D4D4D4;
                border: none;
                padding: 10px;
            }
        """)

        # Set fixed-width font
        font = QFont("Consolas", 10)
        self.text_area.setFont(font)

        # Configure text formats
        self.formats = {
            'header': self._create_format('#569CD6', 11, True),  # Bright blue, bold
            'value': self._create_format('#4EC9B0'),  # Bright teal
            'field': self._create_format('#9CDCFE'),  # Light blue
            'section': self._create_format('#CE9178', 10, True),  # Orange, bold
            'success': self._create_format('#4EC9B0'),  # Bright teal
            'error': self._create_format('#F14C4C')  # Bright red
        }

        layout.addLayout(header)
        layout.addWidget(self.text_area)

    def _create_format(self, color: str, size: int = 10, bold: bool = False) -> QTextCharFormat:
        """Create a text format with specified color, size, and weight"""
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        fmt.setFontFamily("Consolas")
        fmt.setFontPointSize(size)
        if bold:
            fmt.setFontWeight(QFont.Weight.Bold)
        return fmt

    def insert_field(self, name: str, value: str):
        """Insert a field-value pair with proper styling"""
        cursor = self.text_area.textCursor()

        # Insert field name
        cursor.insertText(f"{name}: ", self.formats['field'])

        # Insert value
        cursor.insertText(f"{value}\n", self.formats['value'])

    def update_content(self, content: dict):
        """Updates the text area with styled discovery results"""
        self.text_area.clear()
        cursor = self.text_area.textCursor()

        # Device info header
        cursor.insertText("Device Information\n", self.formats['header'])
        cursor.insertText("─" * 40 + "\n", self.formats['field'])

        # Basic device information
        self.insert_field("Device Type", content['device_type'])
        self.insert_field("Confidence", f"{content['confidence_score']:.1f}%")
        self.insert_field("Template", content['template'])
        self.insert_field("Processing Time", f"{content['processing_time']:.2f}s")

        # Parsed data section
        cursor.insertText("\nParsed Data\n", self.formats['section'])
        cursor.insertText("─" * 40 + "\n", self.formats['field'])

        # Device-specific data
        for key, value in content['parsed_data'].items():
            if value:  # Only show non-empty values
                self.insert_field(f"  {key}", str(value))

    def update_status(self, status: str, success: bool = True):
        """Updates the status label with colored text"""
        self.status_label.setText(status)
        color = '#4EC9B0' if success else '#F14C4C'
        self.status_label.setStyleSheet(f"QLabel {{ color: {color}; }}")

    def show_error(self, error_msg: str):
        """Display error message with styling"""
        self.text_area.clear()
        cursor = self.text_area.textCursor()

        cursor.insertText("Error During Discovery\n", self.formats['header'])
        cursor.insertText("─" * 40 + "\n", self.formats['field'])
        cursor.insertText(f"\n{error_msg}\n", self.formats['error'])

    def set_discovery_enabled(self, enabled: bool):
        """Enable or disable the discover button"""
        self.discover_btn.setEnabled(enabled)