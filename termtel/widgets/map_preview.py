from PyQt6.QtWidgets import (QWidget, QLabel, QVBoxLayout, QScrollArea,
                             QPushButton, QDialog, QHBoxLayout)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QImage, QPixmap
import os


class MapPreview(QScrollArea):
    """Preview widget for network topology map"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.map_path = None

        # Configure scroll area
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Create container widget and layout
        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)

        # Create image label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.image_label.mousePressEvent = self.on_click

        # Set dark background
        self.setStyleSheet("QScrollArea { background-color: #1A1A1A; border: none; }")
        self.container.setStyleSheet("QWidget { background-color: #1A1A1A; }")

        # Add placeholder text
        self.image_label.setText("Map will be displayed here after discovery.")
        self.image_label.setStyleSheet("QLabel { color: #CCCCCC; }")

        self.layout.addWidget(self.image_label)
        self.setWidget(self.container)

    def update_map(self, map_path):
        """Update the map preview with a new image"""
        if not os.path.exists(map_path):
            self.image_label.setText("Error: Map image not found")
            return

        self.map_path = map_path

        # Load and scale image
        image = QImage(map_path)
        if image.isNull():
            self.image_label.setText("Error: Failed to load map image")
            return

        # Calculate scaled size maintaining aspect ratio
        display_width = 300  # Preview width
        scaled_size = QSize(display_width,
                            int(display_width * image.height() / image.width()))

        # Create and set pixmap
        pixmap = QPixmap.fromImage(image)
        scaled_pixmap = pixmap.scaled(scaled_size,
                                      Qt.AspectRatioMode.KeepAspectRatio,
                                      Qt.TransformationMode.SmoothTransformation)

        self.image_label.setPixmap(scaled_pixmap)
        self.image_label.setMinimumSize(scaled_size)

    def on_click(self, event):
        """Open full-size map viewer when clicked"""
        if self.map_path and os.path.exists(self.map_path):
            viewer = MapViewer(self.map_path, parent=self.window())
            viewer.exec()


class MapViewer(QDialog):
    """Full-screen map viewer with zoom capabilities"""

    def __init__(self, map_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Network Map Viewer")
        self.setWindowState(Qt.WindowState.WindowMaximized)

        # Initialize zoom level
        self.zoom_level = 1.0
        self.map_path = map_path

        # Create layout
        layout = QVBoxLayout(self)

        # Create scroll area for map
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Create image label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Load initial image
        self.load_image()

        # Add image label to scroll area
        self.scroll_area.setWidget(self.image_label)

        # Create control buttons
        button_layout = QHBoxLayout()

        zoom_in_btn = QPushButton("Zoom In")
        zoom_out_btn = QPushButton("Zoom Out")
        reset_btn = QPushButton("Reset")
        exit_btn = QPushButton("Exit Fullscreen")

        zoom_in_btn.clicked.connect(lambda: self.zoom(1.2))
        zoom_out_btn.clicked.connect(lambda: self.zoom(0.8))
        reset_btn.clicked.connect(self.reset_zoom)
        exit_btn.clicked.connect(self.close)

        for btn in [zoom_in_btn, zoom_out_btn, reset_btn, exit_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    padding: 8px 16px;
                    background-color: #2D2D2D;
                    border: none;
                    border-radius: 4px;
                    color: #FFFFFF;
                }
                QPushButton:hover {
                    background-color: #3D3D3D;
                }
                QPushButton:pressed {
                    background-color: #404040;
                }
            """)
            button_layout.addWidget(btn)

        # Add widgets to layout
        layout.addWidget(self.scroll_area)
        layout.addLayout(button_layout)

        # Set dark theme
        self.setStyleSheet("""
            QDialog {
                background-color: #1A1A1A;
            }
            QScrollArea {
                background-color: #1A1A1A;
                border: none;
            }
        """)

        # Handle wheel events for zooming
        self.scroll_area.wheelEvent = self.wheel_zoom

    def load_image(self):
        """Load and display the image at current zoom level"""
        image = QImage(self.map_path)
        if image.isNull():
            return

        # Calculate new size based on zoom
        new_width = int(image.width() * self.zoom_level)
        new_height = int(image.height() * self.zoom_level)

        # Create scaled pixmap
        pixmap = QPixmap.fromImage(image)
        scaled_pixmap = pixmap.scaled(QSize(new_width, new_height),
                                      Qt.AspectRatioMode.KeepAspectRatio,
                                      Qt.TransformationMode.SmoothTransformation)

        self.image_label.setPixmap(scaled_pixmap)

    def zoom(self, factor):
        """Apply zoom factor and update image"""
        self.zoom_level *= factor
        self.load_image()

    def reset_zoom(self):
        """Reset to original zoom level"""
        self.zoom_level = 1.0
        self.load_image()

    def wheel_zoom(self, event):
        """Handle mouse wheel zoom with Ctrl key"""
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            factor = 1.1 if delta > 0 else 0.9
            self.zoom(factor)
        else:
            # Pass through normal wheel event for scrolling
            super().wheelEvent(event)