from dataclasses import dataclass
from typing import Any, Dict

from PyQt6.QtCharts import QValueAxis
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QPen, QPalette, QLinearGradient
from PyQt6.QtWidgets import QApplication, QVBoxLayout, QTreeWidget, QFrame, QLabel, QGridLayout, QLineEdit, QTextEdit, \
    QHBoxLayout


@dataclass
class ThemeColors:

    # Core colors
    primary: str = "#0a8993"  # Brighter cyan
    secondary: str = "#065359"  # Mid cyan
    background: str = "#010203"  # Near black
    darker_bg: str = "#000000"  # Pure black
    text: str = "#0a8993"  # Bright cyan text
    grid: str = "#065d63"  # Visible grid
    line: str = "#ffff33"  # Bright yellow
    border: str = "#0a8993"  # Bright cyan border
    success: str = "#0a8993"  # Bright cyan status
    error: str = "#ff4c4c"  # Bright red

    # Effects
    border_light: str = "rgba(10, 137, 147, 0.5)"
    corner_gap: str = "#010203"
    corner_bright: str = "#0ff5ff"  # Ultra bright cyan corners

    # Transparencies
    panel_bg: str = "rgba(0, 0, 0, 0.95)"
    scrollbar_bg: str = "rgba(6, 20, 22, 0.6)"
    selected_bg: str = "rgba(10, 137, 147, 0.25)"

    # Buttons
    button_hover: str = "#08706e"
    button_pressed: str = "#064d4a"

    chart_bg: str = "rgba(6, 83, 89, 0.25)"

class ThemeLibrary:
    def __init__(self):
        self.themes = {
            "cyberpunk": self.apply_cyberpunk_palette,
            "retro_green": self.apply_retro_green_palette,
            "retro_amber": self.apply_retro_amber_palette,
            "neon_blue": self.apply_neon_blue_palette
        }


        # Theme colors with consistent darkness levels
        self.chart_colors = {
            "cyberpunk": ThemeColors(),  # Keep original cyberpunk
            "retro_green": ThemeColors(
                primary="#0d3b0d",  # Dark green primary
                secondary="#041504",  # Darker green secondary
                background="#010201",  # Almost black with slight green tint
                darker_bg="#000100",  # Pure black with slight green tint
                text="#00ff00",  # Bright green for text (keep this bright for contrast)
                grid="#0d3b0d",  # Dark green grid
                line="#00ff00",  # Bright green for lines
                button_hover="#0d4b0d",  # Slightly lighter hover
                button_pressed="#083008",  # Darker pressed state
                border="#0d3b0d",  # Dark green border
                success="#00ff00",  # Bright green for success
                error="#ff0000",  # Keep red for error
                border_light="rgba(13, 59, 13, 0.4)",  # Semi-transparent dark green
                corner_gap="#010201",  # Match background
                panel_bg="rgba(1, 2, 1, 0.98)",  # Almost opaque dark
                scrollbar_bg="rgba(0, 1, 0, 0.5)",  # Semi-transparent very dark
                selected_bg="rgba(13, 59, 13, 0.15)",  # Very subtle selection
                chart_bg="rgba(13, 59, 13, 0.15)",  # Subtle chart background
                corner_bright="#00ff00",  # Bright green corners

            ),
            "retro_amber": ThemeColors(
                primary="#3b2600",  # Dark amber primary
                secondary="#251700",  # Darker amber secondary
                background="#0c0700",  # Almost black with slight amber tint
                darker_bg="#080400",  # Pure black with slight amber tint
                text="#ffa500",  # Bright amber for text (keep this bright for contrast)
                grid="#3b2600",  # Dark amber grid
                line="#ffa500",  # Bright amber for lines
                button_hover="#4b3000",  # Slightly lighter hover
                button_pressed="#301e00",  # Darker pressed state
                border="#3b2600",  # Dark amber border
                success="#ffa500",  # Bright amber for success
                error="#ff4500",  # Keep orange-red for error
                border_light="rgba(59, 38, 0, 0.4)",  # Semi-transparent dark amber
                corner_gap="#0c0700",  # Match background
                panel_bg="rgba(12, 7, 0, 0.98)",  # Almost opaque dark
                scrollbar_bg="rgba(8, 4, 0, 0.5)",  # Semi-transparent very dark
                selected_bg="rgba(59, 38, 0, 0.15)",  # Very subtle selection
                chart_bg="rgba(59, 38, 0, 0.15)",  # Subtle chart background
                corner_bright="#ffa500",

            ),
            "neon_blue": ThemeColors(  # Keep original neon_blue as is
                primary="#00FFFF",
                secondary="#00004E",
                background="#00001E",
                darker_bg="#000018",
                text="#00FFFF",
                grid="#00004E",
                line="#FFFFFF",
                button_hover="#000064",
                button_pressed="#000080",
                border="#00FFFF",
                success="#00FFFF",
                error="#FF0000",
                border_light="rgba(0, 255, 255, 0.4)",
                corner_gap="#00001E",
                panel_bg="rgba(0, 0, 30, 0.98)",
                scrollbar_bg="rgba(0, 0, 24, 0.5)",
                selected_bg="rgba(0, 255, 255, 0.15)",
                chart_bg="rgba(0, 0, 78, 0.2)",
                corner_bright="#00ffff",
            )
        }

    def get_colors(self, theme_name: str) -> Dict[str, str]:
        """Return the color dictionary for the specified theme."""
        if theme_name in self.chart_colors:
            return self.chart_colors[theme_name].__dict__
        else:
            print(f"Colors for theme '{theme_name}' not found, returning default.")
            return self.chart_colors["cyberpunk"].__dict__

    def get_chart_colors(self, theme_name: str) -> Dict[str, str]:
        """Alias for get_colors() for backwards compatibility."""
        return self.get_colors(theme_name)

    def apply_theme(self, widget, theme_name):
        if theme_name in self.themes:
            self.themes[theme_name](widget)
        else:
            print(f"Theme '{theme_name}' not found.")

    def _generate_theme_stylesheet(self, theme):
        """Generate common stylesheet with theme-specific colors"""
        return f"""
            QMainWindow, QWidget {{
                background-color: {theme.background};
                color: {theme.text};
                font-family: "Courier New";
            }}

            QGroupBox {{
                background-color: {theme.panel_bg};
                border: 1px solid {theme.border_light};
                margin-top: 1.5em;
                padding: 15px;
                font-family: "Courier New";
            }}

            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: {theme.text};
                font-family: "Courier New";
                text-transform: uppercase;
                background: {theme.background};
            }}

            QLineEdit {{
                background-color: {theme.darker_bg};
                color: {theme.text};
                border: 1px solid {theme.border_light};
                border-radius: 0;
                padding: 5px;
                font-family: "Courier New";
                selection-background-color: {theme.selected_bg};
            }}

            QLineEdit::placeholder {{
                color: {theme.border_light};
            }}

            QComboBox {{
                background-color: {theme.darker_bg};
                color: {theme.text};
                border: 1px solid {theme.border_light};
                border-radius: 0;
                padding: 5px;
                font-family: "Courier New";
                min-width: 6em;
            }}

            QComboBox::drop-down {{
                border: none;
                background: {theme.darker_bg};
                width: 20px;
            }}

            QComboBox::down-arrow {{
                image: none;
                border: 2px solid {theme.text};
                width: 6px;
                height: 6px;
                border-top: none;
                border-right: none;
                transform: rotate(-45deg);
                margin-right: 5px;
            }}

            QPushButton {{
                background-color: {theme.darker_bg};
                color: {theme.text};
                border: 1px solid {theme.border_light};
                border-radius: 0;
                padding: 5px 15px;
                font-family: "Courier New";
                text-transform: uppercase;
            }}

            QPushButton:hover {{
                background-color: {theme.button_hover};
                border: 1px solid {theme.text};
            }}

            QPushButton:pressed {{
                background-color: {theme.button_pressed};
                border: 1px solid {theme.text};
            }}

            QTreeWidget {{
                background-color: {theme.darker_bg};
                color: {theme.text};
                border: 1px solid {theme.border_light};
                font-family: "Courier New";
                outline: none;
                alternate-background-color: {theme.panel_bg};
            }}

            QTreeWidget::item {{
                padding: 5px;
                border: none;
            }}

            QTreeWidget::item:selected {{
                background-color: {theme.selected_bg};
                color: {theme.text};
            }}

            QTreeWidget::item:hover {{
                background-color: {theme.button_hover};
            }}

            QHeaderView::section {{
                background-color: {theme.darker_bg};
                color: {theme.text};
                border: 1px solid {theme.border_light};
                padding: 5px;
                font-family: "Courier New";
                text-transform: uppercase;
            }}

            QTabWidget {{
                border: none;
            }}

            QTabWidget::pane {{
                border: 1px solid {theme.border_light};
                background: {theme.darker_bg};
            }}

            QTabBar::tab {{
                background-color: {theme.darker_bg};
                color: {theme.text};
                border: 1px solid {theme.border_light};
                border-bottom: none;
                padding: 8px 12px;
                font-family: "Courier New";
                text-transform: uppercase;
                min-width: 80px;
                margin-right: 2px;
            }}

            QTabBar::tab:selected {{
                background-color: {theme.primary};
                color: {theme.darker_bg};
            }}

            QTabBar::tab:hover {{
                background-color: {theme.button_hover};
            }}

            QScrollBar:vertical {{
                background-color: {theme.darker_bg};
                width: 8px;
                margin: 0;
            }}

            QScrollBar::handle:vertical {{
                background: {theme.border_light};
                min-height: 20px;
                border-radius: 4px;
            }}

            QScrollBar::add-line:vertical, 
            QScrollBar::sub-line:vertical {{
                height: 0;
                background: none;
            }}

            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {{
                background: {theme.darker_bg};
            }}

            QScrollBar:horizontal {{
                background-color: {theme.darker_bg};
                height: 8px;
                margin: 0;
            }}

            QScrollBar::handle:horizontal {{
                background: {theme.border_light};
                min-width: 20px;
                border-radius: 4px;
            }}

            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {{
                width: 0;
                background: none;
            }}

            QScrollBar::add-page:horizontal,
            QScrollBar::sub-page:horizontal {{
                background: {theme.darker_bg};
            }}

            QTextEdit {{
                background-color: {theme.darker_bg};
                color: {theme.text};
                border: 1px solid {theme.border_light};
                font-family: "Courier New";
                padding: 5px;
                selection-background-color: {theme.selected_bg};
            }}

            QLabel {{
                color: {theme.text};
                font-family: "Courier New";
            }}

            QChartView {{
                background: transparent;
                border: 1px solid {theme.border_light};
            }}

            /* Chart Title Styling */
            QChart {{
                title-color: {theme.text};
                title-font: bold 10pt "Courier New";
            }}
        """

    def _apply_theme_common(self, widget, theme_name):
        """Apply common theme elements with specific colors"""
        theme = self.chart_colors[theme_name]
        palette = QPalette()

        # Set palette colors
        palette.setColor(QPalette.ColorRole.Window, QColor(theme.background))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(theme.text))
        palette.setColor(QPalette.ColorRole.Base, QColor(theme.darker_bg))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(theme.secondary))
        palette.setColor(QPalette.ColorRole.Text, QColor(theme.text))
        palette.setColor(QPalette.ColorRole.Button, QColor(theme.darker_bg))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(theme.text))

        # Apply palette
        app = QApplication.instance()
        if app:
            app.setPalette(palette)

        # Apply stylesheet
        widget.setStyleSheet(self._generate_theme_stylesheet(theme))

    def apply_cyberpunk_palette(self, widget):
        self._apply_theme_common(widget, "cyberpunk")

    def apply_retro_green_palette(self, widget):
        self._apply_theme_common(widget, "retro_green")

    def apply_retro_amber_palette(self, widget):
        self._apply_theme_common(widget, "retro_amber")

    def apply_neon_blue_palette(self, widget):
        self._apply_theme_common(widget, "neon_blue")


def update_chart_style(self, chart, theme_name: str, axes=None):
    """Enhanced chart styling with HUD-like grid"""
    colors = self.get_colors(theme_name)

    # Configure chart
    chart.setBackgroundVisible(False)
    chart.setPlotAreaBackgroundVisible(True)
    chart.setBackgroundBrush(QColor(0, 0, 0, 0))
    chart.setPlotAreaBackgroundBrush(QColor(colors['darker_bg']))
    chart.legend().setVisible(False)

    if axes:
        for axis in axes:
            # Grid styling
            grid_pen = QPen(QColor(colors['grid']), 1, Qt.PenStyle.DotLine)
            grid_pen.setDashPattern([1, 4])
            axis.setGridLinePen(grid_pen)
            axis.setGridLineColor(QColor(colors['grid']))

            # Labels styling
            axis.setLabelsColor(QColor(colors['text']))
            font = QFont("Courier New", 8)
            axis.setLabelsFont(font)

            if isinstance(axis, QValueAxis):
                axis.setTickCount(6)
                axis.setMinorTickCount(0)
                title_font = QFont("Courier New", 9, QFont.Weight.Bold)
                axis.setTitleFont(title_font)
                axis.setTitleBrush(QColor(colors['text']))


class LayeredHUDFrame(QFrame):
    def __init__(self, parent=None, theme_manager=None, theme_name="cyberpunk"):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.theme_name = theme_name
        self.setup_ui()
        if theme_manager:
            self.update_theme_colors()

    def setup_ui(self):
        # Main content layout
        self.content_layout = QVBoxLayout(self)
        self.content_layout.setContentsMargins(25, 25, 25, 25)

        # Create corner lines (bright)
        self.corner_lines = []
        for i in range(8):
            line = QFrame(self)
            if i < 4:  # Horizontal corner pieces
                line.setFrameShape(QFrame.Shape.HLine)
                line.setFixedHeight(1)
            else:  # Vertical corner pieces
                line.setFrameShape(QFrame.Shape.VLine)
                line.setFixedWidth(1)
            self.corner_lines.append(line)

        # Create connecting lines (dim)
        self.connecting_lines = []
        for i in range(4):
            line = QFrame(self)
            if i < 2:  # Horizontal connectors
                line.setFrameShape(QFrame.Shape.HLine)
                line.setFixedHeight(1)
            else:  # Vertical connectors
                line.setFrameShape(QFrame.Shape.VLine)
                line.setFixedWidth(1)
            self.connecting_lines.append(line)

        self.setStyleSheet("background-color: transparent;")

        # Set initial colors (will be overridden if theme_manager is provided)
        self.update_line_colors("#0f969e", "rgba(15, 150, 158, 0.3)")

    def update_theme_colors(self):
        """Update colors based on current theme"""
        if self.theme_manager:
            colors = self.theme_manager.get_colors(self.theme_name)
            # Fall back to border color if corner_bright isn't defined
            bright_color = colors.get('corner_bright', colors['border'])
            dim_color = colors['border_light']
            self.update_line_colors(bright_color, dim_color)
            # Convert hex to rgba if needed
            if bright_color.startswith('#'):
                r = int(bright_color[1:3], 16)
                g = int(bright_color[3:5], 16)
                b = int(bright_color[5:7], 16)
                dim_color = f"rgba({r}, {g}, {b}, 0.4)"

            self.update_line_colors(bright_color, dim_color)
    def update_line_colors(self, bright_color, dim_color):
        """Update line colors with provided colors"""
        # Update corner lines (bright)
        for line in self.corner_lines:
            line.setStyleSheet(f"background-color: {bright_color};")

        # Update connecting lines (dim)
        for line in self.connecting_lines:
            line.setStyleSheet(f"background-color: {dim_color};")

    def set_theme(self, theme_name):
        """Change the theme of the frame"""
        self.theme_name = theme_name
        self.update_theme_colors()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w, h = self.width(), self.height()
        corner_length = 20  # Length of bright corner pieces

        # Top-left corner
        self.corner_lines[0].setGeometry(0, 0, corner_length, 1)  # Horizontal
        self.corner_lines[4].setGeometry(0, 0, 1, corner_length)  # Vertical

        # Top-right corner
        self.corner_lines[1].setGeometry(w - corner_length, 0, corner_length, 1)  # Horizontal
        self.corner_lines[5].setGeometry(w - 1, 0, 1, corner_length)  # Vertical

        # Bottom-left corner
        self.corner_lines[2].setGeometry(0, h - 1, corner_length, 1)  # Horizontal
        self.corner_lines[6].setGeometry(0, h - corner_length, 1, corner_length)  # Vertical

        # Bottom-right corner
        self.corner_lines[3].setGeometry(w - corner_length, h - 1, corner_length, 1)  # Horizontal
        self.corner_lines[7].setGeometry(w - 1, h - corner_length, 1, corner_length)  # Vertical

        # Connecting lines (dim)
        # Top
        self.connecting_lines[0].setGeometry(corner_length, 0, w - 2 * corner_length, 1)
        # Bottom
        self.connecting_lines[1].setGeometry(corner_length, h - 1, w - 2 * corner_length, 1)
        # Left
        self.connecting_lines[2].setGeometry(0, corner_length, 1, h - 2 * corner_length)
        # Right
        self.connecting_lines[3].setGeometry(w - 1, corner_length, 1, h - 2 * corner_length)

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QTreeWidget,
    QTreeWidgetItem,
    QPushButton,
    QComboBox,
    QWidget,
)


class ThemeShowcaseWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.theme_manager = ThemeLibrary()
        self.setup_window()
        self.create_frames()
        self.apply_initial_theme()

    def setup_window(self):
        self.setWindowTitle("Theme Showcase")
        self.resize(1000, 800)
        self.central_widget = QWidget()
        self.main_layout = QVBoxLayout(self.central_widget)
        self.setCentralWidget(self.central_widget)

    def create_frames(self):
        self.create_theme_selector()
        self.create_input_panel()
        self.create_control_panel()
        self.create_tree_panel()

    def create_theme_selector(self):
        self.selector_frame = LayeredHUDFrame(self, theme_manager=self.theme_manager)
        selector_layout = QVBoxLayout()
        self.selector_frame.content_layout.addLayout(selector_layout)

        selector_layout.addWidget(QLabel("Select Theme:"))
        self.theme_selector = QComboBox()
        self.theme_selector.addItems(self.theme_manager.chart_colors.keys())
        self.theme_selector.currentTextChanged.connect(self.change_theme)
        selector_layout.addWidget(self.theme_selector)

        self.main_layout.addWidget(self.selector_frame)

    def create_input_panel(self):
        self.input_frame = LayeredHUDFrame(self, theme_manager=self.theme_manager)
        input_layout = QGridLayout()
        self.input_frame.content_layout.addLayout(input_layout)

        # Input widgets
        inputs = [
            ("Text Input:", QLineEdit("Sample text")),
            ("Dropdown:", self.create_dropdown()),
            ("Text Area:", self.create_text_area())
        ]

        for row, (label, widget) in enumerate(inputs):
            input_layout.addWidget(QLabel(label), row, 0)
            input_layout.addWidget(widget, row, 1)

        self.main_layout.addWidget(self.input_frame)

    def create_control_panel(self):
        self.controls_frame = LayeredHUDFrame(self, theme_manager=self.theme_manager)
        controls_layout = QHBoxLayout()
        self.controls_frame.content_layout.addLayout(controls_layout)

        buttons = self.create_buttons()
        for btn in buttons:
            controls_layout.addWidget(btn)

        self.main_layout.addWidget(self.controls_frame)

    def create_tree_panel(self):
        self.tree_frame = LayeredHUDFrame(self, theme_manager=self.theme_manager)
        tree_layout = QVBoxLayout()
        self.tree_frame.content_layout.addLayout(tree_layout)

        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["Item", "Status", "Value"])
        # self.populate_tree()
        tree_layout.addWidget(self.tree_widget)

        self.main_layout.addWidget(self.tree_frame)

    @staticmethod
    def create_dropdown():
        dropdown = QComboBox()
        dropdown.addItems(["Option 1", "Option 2", "Option 3"])
        return dropdown

    @staticmethod
    def create_text_area():
        text_area = QTextEdit()
        text_area.setPlainText("Multi-line\ntext area\ncontent")
        text_area.setMaximumHeight(100)
        return text_area

    @staticmethod
    def create_buttons():
        buttons = []
        for text in ["Normal Button", "Toggle State", "Action Button"]:
            btn = QPushButton(text)
            btn.clicked.connect(lambda: None)
            buttons.append(btn)
        return buttons

    def apply_initial_theme(self):
        self.change_theme("cyberpunk")

    def change_theme(self, theme_name):
        self.theme_manager.apply_theme(self, theme_name)
        theme_colors = self.theme_manager.get_colors(theme_name)

        # Update all frames
        for frame in [self.selector_frame, self.input_frame,
                      self.controls_frame, self.tree_frame]:
            frame.set_theme(theme_name)

        self.update_tree_style(theme_colors)

    def update_tree_style(self, theme_colors):
        self.tree_widget.setStyleSheet(f"""
            QTreeWidget {{
                background-color: transparent;
                border: none;
                color: {theme_colors['text']};
                outline: none;
            }}
            QTreeWidget::item {{
                padding: 5px;
                border: none;
            }}
            QTreeWidget::item:selected {{
                background-color: {theme_colors['selected_bg']};
            }}
            QHeaderView::section {{
                background-color: transparent;
                color: {theme_colors['text']};
                border: none; 
                border-bottom: 1px solid {theme_colors['text']};
                padding: 5px;
                font-family: "Courier New";
                font-weight: bold;
            }}
        """)

def main():
    import sys

    # Initialize the application
    app = QApplication(sys.argv)

    # Initialize the theme manager


    # Create the main window

    # Instantiate and show the main window
    window = ThemeShowcaseWindow()
    window.show()

    # Start the application event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
