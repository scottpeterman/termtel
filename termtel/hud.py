from PyQt6.QtWidgets import QWidget, QGroupBox
from PyQt6.QtCore import Qt, QMargins
from PyQt6.QtGui import QPainter, QPen, QColor, QFont
from PyQt6.QtCharts import QChart, QValueAxis, QLineSeries


class CyberpunkStyle:
    # Color scheme
    CYAN = "#22D3EE"
    CYAN_DARK = "#0891B2"
    CYAN_DARKER = "#164E63"
    BG_BLACK = "#000000"

    @staticmethod
    def apply_theme(app):
        app.setStyle("Fusion")
        app.setStyleSheet("""
            QMainWindow {
                background-color: #000000;
            }

            QWidget {
                background-color: transparent;
                color: #22D3EE;
                font-family: 'Courier New', monospace;
            }

            QGroupBox {
                border: 1px solid rgba(34, 211, 238, 0.2);
                border-radius: 4px;
                margin-top: 8px;
                padding: 24px 16px 16px 16px;
                background-color: rgba(0, 0, 0, 0.8);
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
                color: #22D3EE;
                font-size: 14px;
                font-weight: bold;
            }

            QLineEdit, QComboBox {
                background-color: transparent;
                border: 1px solid rgba(34, 211, 238, 0.3);
                border-radius: 4px;
                padding: 8px;
                color: #22D3EE;
                selection-background-color: rgba(34, 211, 238, 0.2);
            }

            QPushButton {
                background-color: rgba(8, 145, 178, 0.5);
                border: 1px solid rgba(34, 211, 238, 0.3);
                border-radius: 4px;
                padding: 8px 24px;
                color: #22D3EE;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: rgba(14, 116, 144, 0.5);
            }

            QTreeWidget, QTreeView {
                background-color: transparent;
                border: 1px solid rgba(34, 211, 238, 0.1);
                border-radius: 4px;
                alternate-background-color: rgba(34, 211, 238, 0.05);
            }

            QTreeWidget::item, QTreeView::item {
                padding: 8px;
                border-bottom: 1px solid rgba(34, 211, 238, 0.05);
            }

            QTreeWidget::item:selected, QTreeView::item:selected {
                background-color: rgba(34, 211, 238, 0.1);
            }

            QHeaderView::section {
                background-color: transparent;
                color: #22D3EE;
                border: none;
                border-bottom: 1px solid rgba(34, 211, 238, 0.2);
                padding: 8px;
                font-weight: bold;
            }

            QTabWidget::pane {
                border: 1px solid rgba(34, 211, 238, 0.2);
                background-color: transparent;
                border-radius: 4px;
            }

            QTabBar::tab {
                background-color: transparent;
                color: #22D3EE;
                border: 1px solid rgba(34, 211, 238, 0.2);
                padding: 8px 16px;
                margin-right: 2px;
            }

            QTabBar::tab:selected {
                background-color: rgba(34, 211, 238, 0.1);
            }

            QScrollBar:vertical {
                border: none;
                background: rgba(0, 0, 0, 0.2);
                width: 8px;
                border-radius: 4px;
                margin: 0;
            }

            QScrollBar::handle:vertical {
                background: rgba(34, 211, 238, 0.3);
                border-radius: 4px;
                min-height: 20px;
            }

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }

            QLabel {
                color: #22D3EE;
            }

            QChart {
                background-color: transparent;
                border: none;
            }

            QChartView {
                background-color: transparent;
                border: 1px solid rgba(34, 211, 238, 0.1);
                border-radius: 4px;
            }
        """)


class FrameDecorator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        pen = QPen(QColor(34, 211, 238, 76))
        pen.setWidth(2)
        painter.setPen(pen)

        size = 24
        margin = 0

        def draw_corner(x, y, angle):
            painter.save()
            painter.translate(x, y)
            painter.rotate(angle)
            painter.drawLine(0, 0, size, 0)
            painter.drawLine(0, 0, 0, size)
            painter.restore()

        # Draw all corners
        draw_corner(margin, margin, 0)
        draw_corner(self.width() - margin, margin, 90)
        draw_corner(margin, self.height() - margin, -90)
        draw_corner(self.width() - margin, self.height() - margin, 180)


def setup_chart_style(chart_view):
    """Apply cyberpunk styling to a QChartView instance"""
    chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
    chart_view.setBackgroundBrush(QColor(0, 0, 0, 0))

    chart = chart_view.chart()
    chart.setBackgroundVisible(False)
    chart.setPlotAreaBackgroundVisible(True)
    chart.setBackgroundBrush(QColor(0, 0, 0, 0))
    chart.setPlotAreaBackgroundBrush(QColor(0, 0, 0, 40))
    chart.legend().setVisible(False)

    # Configure margins
    chart.setMargins(QMargins(20, 20, 20, 20))
    chart.layout().setContentsMargins(0, 0, 0, 0)

    # Style axes
    for axis in chart.axes():
        axis.setLabelsColor(QColor(CyberpunkStyle.CYAN))
        axis.setGridLineColor(QColor(CyberpunkStyle.CYAN_DARKER))
        axis.setLinePen(QPen(QColor(CyberpunkStyle.CYAN), 1))
        axis.setGridLinePen(QPen(QColor(CyberpunkStyle.CYAN_DARKER), 1, Qt.PenStyle.DotLine))

        # Configure labels
        font = QFont("Courier New", 8)
        axis.setLabelsFont(font)

        # Remove axis line
        axis.setLineVisible(False)

        # Configure tick marks
        axis.setTickCount(6)
        axis.setMinorTickCount(1)

        if isinstance(axis, QValueAxis):
            if axis.orientation() == Qt.Orientation.Vertical:
                axis.setTitleText("UTILIZATION %")
            else:
                axis.setTitleText("TIME (s)")
            axis.setTitleFont(QFont("Courier New", 9, QFont.Weight.Bold))
            axis.setTitleBrush(QColor(CyberpunkStyle.CYAN))


def apply_hud_styling(window):
    """Apply HUD styling to a window and all its widgets"""
    # Add frame decorators to all group boxes
    for group_box in window.findChildren(QGroupBox):
        decorator = FrameDecorator(group_box)
        decorator.setGeometry(group_box.rect())
        group_box.resizeEvent = lambda event, w=group_box, d=decorator: \
            d.setGeometry(w.rect())

    # Set base font
    window.setFont(QFont("Courier New", 10))

    # Set margins
    window.setContentsMargins(16, 16, 16, 16)

    # Set window title prefix
    if not window.windowTitle().startswith("NETWORK HUD"):
        window.setWindowTitle(f"NETWORK HUD :: {window.windowTitle()}")


def style_series(series):
    """Apply cyberpunk styling to a chart series"""
    pen = QPen(QColor(CyberpunkStyle.CYAN))
    pen.setWidth(2)
    series.setPen(pen)

    if isinstance(series, QLineSeries):
        glow_pen = QPen(QColor(CyberpunkStyle.CYAN))
        glow_pen.setWidth(4)
        glow_pen.setColor(QColor(CyberpunkStyle.CYAN).lighter(150))
        series.setPen(glow_pen)


def get_router_svg():
    return '''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 60 41">
  <defs>
    <filter id="glow">
      <feGaussianBlur stdDeviation="0.3" result="coloredBlur"/>
      <feMerge>
        <feMergeNode in="coloredBlur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>
  <g fill="none" stroke="#22D3EE" stroke-width="0.8" filter="url(#glow)">
    <!-- Base cylinder outlines -->
    <path d="M29.137 22.837c16.144 0 29.137-5.119 29.137-11.419S45.281 0 29.137 0 0 5.119 0 11.419s12.994 11.419 29.137 11.419z" opacity="0.4"/>
    <path d="M58.274 11.419c0 6.3-12.994 11.419-29.137 11.419S0 17.719 0 11.419v16.537c0 6.3 12.994 11.419 29.137 11.419s29.137-5.119 29.137-11.419z" opacity="0.4"/>

    <!-- Grid lines -->
    <path d="M14.5 11.419 h43.774" opacity="0.2"/>
    <path d="M29.137 5.419 v16.418" opacity="0.2"/>
    <path d="M43.774 11.419 h-43.774" opacity="0.2"/>

    <!-- Network connections -->
    <path d="M22.448 7.081l2.363 3.544-9.056 1.969 1.969-1.575L3.942 8.656 7.486 5.9l13.388 2.362 1.575-1.181z" stroke-width="1"/>
    <path d="M35.442 15.743L33.473 12.2l8.269-1.969-1.181 1.575 13.388 2.362-3.15 2.363-13.781-2.363-1.575 1.575z" stroke-width="1"/>
    <path d="M30.717 5.113l9.056-2.362.394 3.544-2.363-.394-4.331 3.938-4.331-.787 4.331-3.544-2.756-.394z" stroke-width="1"/>
    <path d="M26.78 19.288l-8.662 1.575-.394-4.331 2.756.787 4.725-4.331 4.331.787-5.119 4.725 2.362.788z" stroke-width="1"/>

    <!-- Corner brackets -->
    <path d="M2 2 h6 M2 2 v6" stroke-width="1"/>
    <path d="M58 2 h-6 M58 2 v6" stroke-width="1"/>
    <path d="M2 39 h6 M2 39 v-6" stroke-width="1"/>
    <path d="M58 39 h-6 M58 39 v-6" stroke-width="1"/>
  </g>
</svg>'''

def get_switch_svg():
    return '''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!-- Created with Inkscape (http://www.inkscape.org/) -->

<svg
   xmlns:dc="http://purl.org/dc/elements/1.1/"
   xmlns:cc="http://creativecommons.org/ns#"
   xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
   xmlns:svg="http://www.w3.org/2000/svg"
   xmlns="http://www.w3.org/2000/svg"
   xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
   xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
   width="100"
   height="100"
   viewBox="0 0 26.458333 26.458334"
   version="1.1"
   id="svg8"
   inkscape:version="0.92.3 (2405546, 2018-03-11)"
   sodipodi:docname="2.svg">
  <defs
     id="defs2" />
  <sodipodi:namedview
     id="base"
     pagecolor="#ffffff"
     bordercolor="#666666"
     borderopacity="1.0"
     inkscape:pageopacity="0.0"
     inkscape:pageshadow="2"
     inkscape:zoom="5.6568543"
     inkscape:cx="24.257017"
     inkscape:cy="60.812532"
     inkscape:document-units="mm"
     inkscape:current-layer="layer1"
     showgrid="false"
     units="px"
     showguides="false"
     inkscape:window-width="1920"
     inkscape:window-height="1001"
     inkscape:window-x="-9"
     inkscape:window-y="-9"
     inkscape:window-maximized="1" />
  <metadata
     id="metadata5">
    <rdf:RDF>
      <cc:Work
         rdf:about="">
        <dc:format>image/svg+xml</dc:format>
        <dc:type
           rdf:resource="http://purl.org/dc/dcmitype/StillImage" />
        <dc:title></dc:title>
      </cc:Work>
    </rdf:RDF>
  </metadata>
  <g
     inkscape:label="Layer 1"
     inkscape:groupmode="layer"
     id="layer1"
     transform="translate(0,-270.54165)">
    <path
       style="fill:#009bd8;"
       d="m 21.55977,279.14682 -0.03534,4.40877 -4.048041,4.15909 0.09435,-4.17461 z"
       id="path1413"
       inkscape:connector-curvature="0"
       sodipodi:nodetypes="ccccc" />
    <path
       style="fill:#009bd8;stroke-width:1"
       d="m 8.5588078,279.04894 13.0009622,0.0979 -4.080081,4.31046 -13.1331462,-0.006 z"
       id="path1413-0"
       inkscape:connector-curvature="0"
       sodipodi:nodetypes="ccccc" />
    <rect
       style="opacity:1;fill:#009bd8;fill-opacity:1;fill-rule:nonzero"
       id="rect1396"
       width="13.260025"
       height="4.1339302"
       x="4.31071"
       y="283.54007" />
    <path
       style="fill:none;stroke:#000000;stroke-width:0.2683014px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1"
       d="m 21.55977,279.14682 -4.074145,4.39977 v 0"
       id="path826"
       inkscape:connector-curvature="0"
       sodipodi:nodetypes="ccc" />
    <path
       style="fill:none;stroke:#000000;stroke-width:0.26458332px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1"
       d="m 8.5588078,279.04894 -4.2480979,4.49113"
       id="path826-1"
       inkscape:connector-curvature="0"
       sodipodi:nodetypes="cc" />
    <path
       style="fill:none;stroke:#000000;stroke-width:0.26458332px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1"
       d="m 21.566209,283.45802 -4.08982,4.25666"
       id="path826-1-1"
       inkscape:connector-curvature="0"
       sodipodi:nodetypes="cc" />
    <path
       style="fill:none;stroke:#000000;stroke-width:0.26458332px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1"
       d="m 4.3432664,287.7089 13.2274686,-0.0349"
       id="path858"
       inkscape:connector-curvature="0"
       sodipodi:nodetypes="cc" />
    <path
       style="fill:none;stroke:#000000;stroke-width:0.26458332px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1"
       d="m 4.3422328,287.84016 0.00431,-4.38868"
       id="path860"
       inkscape:connector-curvature="0"
       sodipodi:nodetypes="cc" />
    <path
       style="fill:none;stroke:#000000;stroke-width:0.26698065px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1"
       d="m 4.3106845,283.54007 13.2729955,0.006"
       id="path858-5"
       inkscape:connector-curvature="0"
       sodipodi:nodetypes="cc" />
    <path
       style="fill:none;stroke:#000000;stroke-width:0.26458332px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1"
       d="m 17.476389,287.71468 0.0033,-4.25742"
       id="path860-9"
       inkscape:connector-curvature="0"
       sodipodi:nodetypes="cc" />
    <path
       style="fill:none;stroke:#000000;stroke-width:0.26698065px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1"
       d="m 8.4614402,279.08914 13.1985818,-2e-4"
       id="path858-5-3"
       inkscape:connector-curvature="0"
       sodipodi:nodetypes="cc" />
    <path
       style="fill:none;stroke:#000000;stroke-width:0.27492884px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1"
       d="m 21.52443,283.55559 0.0033,-4.59687"
       id="path860-9-2"
       inkscape:connector-curvature="0"
       sodipodi:nodetypes="cc" />
    <g
       id="g1461"
       transform="translate(-0.51449383,-0.11693042)">
      <path
         sodipodi:nodetypes="cccccccc"
         inkscape:connector-curvature="0"
         id="path961"
         d="m 8.5018066,282.79217 -0.3369304,0.36173 -0.9591147,-0.51882 2.013314,-0.60565 -0.416297,0.44637 3.2864065,4e-5 -0.298922,0.31637 z"
         style="fill:#ffffff;fill-opacity:1" />
      <path
         sodipodi:nodetypes="cccccccc"
         inkscape:connector-curvature="0"
         id="path963"
         d="m 11.446545,280.38716 -0.416297,0.44637 3.286406,4e-5 -0.298905,0.31637 -3.288473,-4e-5 -0.33693,0.36173 -0.9587626,-0.52098 z"
         style="fill:#ffffff;fill-opacity:1" />
      <path
         sodipodi:nodetypes="cccccccc"
         inkscape:connector-curvature="0"
         id="path965"
         d="m 12.148121,281.9647 3.404962,4e-5 -0.276027,0.29847 1.873319,-0.45496 -0.81912,-0.66951 -0.479267,0.50963 -3.403545,0.006 z"
         style="fill:#ffffff;fill-opacity:1" />
      <path
         sodipodi:nodetypes="cccccccc"
         inkscape:connector-curvature="0"
         id="path967"
         d="m 13.968439,280.36547 0.294245,-0.31637 3.409622,4e-5 0.479267,-0.50963 0.815745,0.66673 -1.869944,0.45774 0.276027,-0.29847 z"
         style="fill:#ffffff;fill-opacity:1" />
    </g>
  </g>
</svg>
'''