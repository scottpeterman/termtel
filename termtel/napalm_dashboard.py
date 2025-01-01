import ipaddress
import math
import sys
import traceback
from time import sleep

# PyQt imports
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLineEdit,
    QComboBox, QPushButton, QLabel, QTreeWidget, QTreeWidgetItem, QTabWidget,
    QMessageBox, QTextEdit, QSizePolicy, QApplication, QDialog
)
from PyQt6.QtCharts import QChartView, QValueAxis, QChart, QLineSeries
from PyQt6.QtCore import Qt, QTimer, QByteArray, QMargins, QThread, QObject, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPen, QPainter

from termtel.helpers.credslib import SecureCredentials
from termtel.napalm_db_dialog import NetworkDeviceDialog
# Importing from separate modules (after splitting code)
from termtel.themes2 import ThemeLibrary, LayeredHUDFrame, ThemeColors
# from hud import (apply_hud_styling, setup_chart_style, style_series, get_router_svg, get_switch_svg)
from termtel.hud_icons import get_switch_svg, get_discovering_svg, get_router_svg, get_unknown_svg

from termtel.device_info_worker import DeviceInfoWorker
from termtel.device_fingerprint import DeviceFingerprinter


class FingerprintWorker(QObject):
    """Worker class for device fingerprinting"""
    finished = pyqtSignal()
    error = pyqtSignal(str)
    driver_detected = pyqtSignal(str)

    def __init__(self, hostname, username, password):
        super().__init__()
        self.hostname = hostname
        self.username = username
        self.password = password

    def run(self):
        try:
            fingerprinter = DeviceFingerprinter(verbose=True)
            result = fingerprinter.fingerprint_device(
                host=self.hostname,
                username=self.username,
                password=self.password
            )

            if not result.get("success"):
                raise Exception(result.get("error", "Unknown error in device detection"))

            device_info = result["device_info"]
            vendor = device_info["vendor"]
            template = device_info["template"]

            # Map fingerprint results to NAPALM drivers
            if "arista" in vendor.lower() or "arista_eos" in template.lower():
                driver = "eos"
            elif "cisco_nxos" in template.lower():
                driver = "nxos"
            elif "cisco" in vendor.lower():
                driver = "ios"
            else:
                raise Exception(f"Unsupported device type detected: {vendor}")

            self.driver_detected.emit(driver)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()

class DeviceDashboardWidget(QMainWindow):
    def __init__(self, parent=None):
        super().__init__()
        self.is_connected = False
        # self.setModal(False)
        self.parent = parent
        self.refparent = parent
        try:
            self.theme_manager = parent.theme_manager
            self._current_theme = parent.theme
        except:
            self.theme_manager = ThemeLibrary()
            parent = self
            self.theme = "retro_amber"
            self.theme_manager.apply_theme(self, self.theme)
            self._current_theme = self.theme

        self.setWindowTitle("Network Device Dashboard")
        self.setGeometry(100, 100, 1400, 900)
        # Initialize history tracking
        self.interface_history = {}
        self.interface_speeds = {}
        self.history_length = 30
        self.theme = parent.theme

        self.cred_manager = self.refparent.cred_manager
        # parent no set yet
        # self.cred_manager.unlock(parent.master_password)

        self.current_credentials = None
        self.setup_ui()
        self.start_credential_loading()

        # self.load_credentials()
        self.custom_driver = None  # Initialize custom_driver
        self.device = None  # Initialize device
        self.worker = None
        self.worker_thread = None
        self.refresh_timer = QTimer()
        self.refresh_timer.setInterval(30000)
        self.refresh_timer.timeout.connect(self.refresh_data)

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        conn_group = self.create_connection_group()
        main_layout.addWidget(conn_group)

        dashboard_layout = QHBoxLayout()

        left_layout = QVBoxLayout()
        self.device_info_widget = self.create_device_info_widget()
        self.interfaces_widget = self.create_interfaces_widget()
        left_layout.addWidget(self.device_info_widget, stretch=2)
        left_layout.addWidget(self.interfaces_widget, stretch=3)

        right_layout = QVBoxLayout()
        self.neighbors_widget = self.create_neighbors_widget()
        self.route_widget = self.create_route_widget()
        right_layout.addWidget(self.neighbors_widget, stretch=1)
        right_layout.addWidget(self.route_widget, stretch=1)

        left_container = QWidget()
        left_container.setLayout(left_layout)
        right_container = QWidget()
        right_container.setLayout(right_layout)

        dashboard_layout.addWidget(left_container, stretch=3)
        dashboard_layout.addWidget(right_container, stretch=2)

        main_layout.addLayout(dashboard_layout)

    def on_credential_selected(self, index):
        """Handle credential selection from combo box."""
        cred_data = self.creds_combo.itemData(index)
        # Just store the selected credentials for when Connect is clicked
        self.current_credentials = cred_data

    def disconnect_device(self):
        self.cleanup_worker()
        self.refresh_timer.stop()
        self.is_connected = False
        self.connect_button.setText("Connect")

        # Clear data but preserve tabs
        self.device_info.clear()
        self.interfaces_tree.clear()
        self.lldp_tree.clear()
        self.arp_tree.clear()
        self.route_tree.clear()

    def handle_connect(self):
        """Handle the connect button click."""
        if self.is_connected:
            reply = QMessageBox.question(
                self,
                'Confirm Disconnect',
                'Disconnect from current device?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.disconnect_device()
            return
        # Get any selected credentials
        selected_cred = self.creds_combo.currentData()

        # Always show dialog, but populate it if we have credentials
        dialog = NetworkDeviceDialog(selected_cred, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            conn_data = dialog.get_connection_data()
            self.connect_device(
                hostname=conn_data['host'],
                username=conn_data['username'],
                password=conn_data['password']
            )
    def attempt_load_credentials(self):
        """Attempt to load credentials, schedule retry if not ready."""
        if not hasattr(self, 'cred_manager') or not self.cred_manager:
            print("No credential manager available")
            return

        if not (self.cred_manager.is_initialized and self.cred_manager.is_unlocked()):
            print("Credential manager not ready, scheduling retry...")
            # Schedule another attempt in 500ms
            QTimer.singleShot(5000, self.attempt_load_credentials)
            return

        try:
            creds_path = self.cred_manager.config_dir / "credentials.yaml"
            if not creds_path.exists():
                print("No credentials file found")
                return

            creds_list = self.cred_manager.load_credentials(creds_path)

            self.creds_combo.clear()
            self.creds_combo.addItem("Manual Entry", None)

            for cred in creds_list:
                display_name = cred.get('display_name', 'Unknown')
                self.creds_combo.addItem(display_name, cred)

        except Exception as e:
            print(f"Failed to load credentials: {e}")
            self.creds_combo.setEnabled(False)

    def start_credential_loading(self):
        """Initiate the credential loading process."""
        # Start the first attempt
        QTimer.singleShot(0, self.attempt_load_credentials)

    def create_connection_group(self):
        group = QGroupBox("Device Connection")
        layout = QHBoxLayout()

        # Create credentials combo box
        self.creds_combo = QComboBox()
        self.creds_combo.addItem("Manual Entry", None)  # Default option
        self.creds_combo.currentIndexChanged.connect(self.on_credential_selected)

        # Driver selection (keep this)
        self.driver_combo = QComboBox()


        self.driver_combo.addItems(['AUTO', 'ios', 'eos', 'nxos'])
        self.driver_combo.setCurrentText('AUTO')

        # Connect button
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.handle_connect)

        # Add widgets to layout
        layout.addWidget(QLabel("Credentials:"))
        layout.addWidget(self.creds_combo)
        layout.addWidget(QLabel("Driver:"))
        layout.addWidget(self.driver_combo)
        layout.addWidget(self.connect_button)

        group.setLayout(layout)
        return group


    def create_device_info_widget(self):
        """Create and configure the device info display widget."""
        # Create main container
        container = LayeredHUDFrame(
            parent=self,
            theme_manager=self.theme_manager,
            theme_name=self._current_theme
        )

        # Get theme colors
        theme_colors = self.theme_manager.get_colors(self._current_theme)

        # Create main layout
        main_layout = QHBoxLayout()
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(16, 16, 16, 16)

        # Create and configure SVG widget
        self.device_svg = QSvgWidget()
        self.device_svg.setFixedSize(74, 64)

        # Get theme colors and modify SVG content
        theme_colors = self.theme_manager.get_colors(self._current_theme)
        svg_content = get_unknown_svg().replace('#22D3EE', theme_colors['text'])
        self.device_svg.load(QByteArray(svg_content.encode()))

        # Create SVG container with centered alignment
        svg_container = QWidget()
        svg_layout = QVBoxLayout(svg_container)
        svg_layout.setContentsMargins(0, 0, 0, 0)
        svg_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        svg_layout.addWidget(self.device_svg)
        svg_container.setFixedWidth(90)  # Set fixed width for SVG container

        # Create and configure device info tree
        self.device_info = QTreeWidget()
        self.device_info.setHeaderLabels(["PROPERTY", "VALUE"])
        self.device_info.setColumnWidth(0, 150)
        self.device_info.setMinimumHeight(200)
        self.device_info.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum
        )
        self.device_info.setAlternatingRowColors(False)
        self.device_info.setIndentation(0)
        self.device_info.setRootIsDecorated(False)
        self.device_info.setUniformRowHeights(True)
        self.device_info.setItemsExpandable(False)

        # Style the tree widget
        self.device_info.setStyleSheet(f"""
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

        # Add widgets to main layout
        main_layout.addWidget(svg_container)
        main_layout.addWidget(self.device_info, 1)  # Give tree widget stretch factor of 1

        # Add main layout to container
        container.content_layout.addLayout(main_layout)

        # Set container properties
        container.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum
        )
        container.setMinimumWidth(400)

        return container
    def create_interfaces_widget(self):
        container = LayeredHUDFrame(
            parent=self,
            theme_manager=self.theme_manager,
            theme_name=self._current_theme
        )
        split_layout = QHBoxLayout()
        split_layout.setContentsMargins(8, 8, 8, 8)

        list_layout = QVBoxLayout()
        self.interfaces_tree = QTreeWidget()
        self.interfaces_tree.setHeaderLabels(["INTERFACE", "STATUS", "UTILIZATION"])
        self.interfaces_tree.setColumnWidth(0, 150)
        self.interfaces_tree.setColumnWidth(1, 80)
        self.interfaces_tree.setColumnWidth(2, 100)
        self.interfaces_tree.itemSelectionChanged.connect(self.update_interface_graph)
        list_layout.addWidget(self.interfaces_tree)

        self.chart = QChart()
        self.chart_view = QChartView(self.chart)
        self.chart_view.setMinimumHeight(200)
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)

        self.setup_chart()

        split_layout.addLayout(list_layout, 1)
        split_layout.addWidget(self.chart_view, 1)
        container.content_layout.addLayout(split_layout)
        return container

    def create_neighbors_widget(self):
        container = LayeredHUDFrame(
            parent=self,
            theme_manager=self.theme_manager,
            theme_name=self._current_theme
        )
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)

        self.neighbors_tabs = QTabWidget()
        self.lldp_tree = QTreeWidget()
        self.lldp_tree.setHeaderLabels(["Local Port", "Neighbor", "Remote Port"])
        self.neighbors_tabs.addTab(self.lldp_tree, "LLDP")

        self.arp_tree = QTreeWidget()
        self.arp_tree.setHeaderLabels(["IP Address", "MAC Address", "Interface"])
        self.neighbors_tabs.addTab(self.arp_tree, "ARP")

        layout.addWidget(self.neighbors_tabs)
        container.content_layout.addLayout(layout)
        return container

    def create_route_widget(self):
        container = LayeredHUDFrame(
            parent=self,
            theme_manager=self.theme_manager,
            theme_name=self._current_theme
        )
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)

        search_layout = QHBoxLayout()
        self.route_search = QLineEdit()
        self.route_search.setPlaceholderText("Enter IP address to find longest prefix match")
        search_button = QPushButton("Find Route")
        search_button.clicked.connect(self.find_longest_prefix_match)
        search_layout.addWidget(self.route_search)
        search_layout.addWidget(search_button)
        layout.addLayout(search_layout)

        self.route_tabs = QTabWidget()
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)

        self.route_tree = QTreeWidget()
        self.route_tree.setHeaderLabels(["Network", "Mask", "Next Hop", "Protocol", "Interface", "Metric"])
        self.route_tree.setColumnWidth(0, 150)
        table_layout.addWidget(self.route_tree)
        self.route_tabs.addTab(table_container, "Table View")

        raw_container = QWidget()
        raw_layout = QVBoxLayout(raw_container)
        raw_layout.setContentsMargins(0, 0, 0, 0)
        self.route_raw = QTextEdit()
        self.route_raw.setReadOnly(True)
        self.route_raw.setFont(QFont("Courier New", 10))
        raw_layout.addWidget(self.route_raw)
        self.route_tabs.addTab(raw_container, "Raw Output")

        layout.addWidget(self.route_tabs)
        container.content_layout.addLayout(layout)
        return container

    def cleanup_worker(self):
        """Clean up existing worker thread."""
        if self.worker_thread and self.worker_thread.isRunning():
            print("Cleaning up existing worker thread")
            self.worker_thread.quit()
            self.worker_thread.wait()
        self.worker = None
        self.worker_thread = None

    def detect_device_type(self, hostname, username, password):

        """Use DeviceFingerprinter to detect device type"""
        fingerprinter = DeviceFingerprinter(verbose=True)
        result = fingerprinter.fingerprint_device(
            host=hostname,
            username=username,
            password=password
        )

        if not result.get("success"):
            raise Exception(result.get("error", "Unknown error in device detection"))

        device_info = result["device_info"]
        vendor = device_info["vendor"]
        template = device_info["template"]

        # Map fingerprint results to NAPALM drivers
        if "arista" in vendor.lower() or "arista_eos" in template.lower():
            return "eos"
        elif "cisco_nxos" in template.lower():
            return "nxos_ssh"
        elif "cisco" in vendor.lower():
            return "ios"
        else:
            raise Exception(f"Unsupported device type detected: {vendor}")

    def connect_device(self, hostname, username, password):
        """Modified connect method with async auto-detection and discovery state"""
        # hostname = self.hostname_input.text()
        # username = self.username_input.text()
        # password = self.password_input.text()

        if not all([hostname, username, password]):
            QMessageBox.warning(self, "Missing Information", "Please fill in all connection details.")
            return

        self.cleanup_worker()
        self.connect_button.setEnabled(False)
        self.setCursor(Qt.CursorShape.WaitCursor)

        try:
            selected_driver = self.driver_combo.currentText()

            if selected_driver == 'AUTO':
                # Show discovery state
                self.set_discovery_state(True)
                self.is_connected = True
                self.connect_button.setText("Disconnect")

                # Start fingerprint worker
                self.fingerprint_thread = QThread()
                self.fingerprint_worker = FingerprintWorker(hostname, username, password)
                self.fingerprint_worker.moveToThread(self.fingerprint_thread)

                # Connect fingerprint worker signals
                self.fingerprint_thread.started.connect(self.fingerprint_worker.run)
                self.fingerprint_worker.finished.connect(self.fingerprint_thread.quit)
                self.fingerprint_worker.finished.connect(self.fingerprint_worker.deleteLater)
                self.fingerprint_thread.finished.connect(self.fingerprint_thread.deleteLater)
                self.fingerprint_worker.finished.connect(lambda: self.set_discovery_state(False))

                # Connect success/error handlers
                self.fingerprint_worker.driver_detected.connect(
                    lambda driver: self.start_device_worker(hostname, username, password, driver)
                )
                self.fingerprint_worker.error.connect(self.handle_fingerprint_error)

                print(f"Starting fingerprint detection for {hostname}")
                self.fingerprint_thread.start()
            else:
                # Direct connection with selected driver
                driver = 'nxos_ssh' if selected_driver == 'nxos' else selected_driver
                self.start_device_worker(hostname, username, password, driver)

        except Exception as e:
            self.set_discovery_state(False)  # Reset discovery state
            self.handle_error(str(e))
            print(f"Error in connect_device: {e}")
            traceback.print_exc()
            self.connect_button.setEnabled(True)
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def set_discovery_state(self, enabled=True):
        """Update UI to show discovery state"""
        if enabled:
            self.set_device_icon(device_type='discovering')

            # Clear and update device info
            self.device_info.clear()
            item = QTreeWidgetItem()
            item.setText(0, "Status")
            item.setText(1, "Discovering device type...")
            item.setForeground(0, QColor(self.theme_manager.get_colors(self._current_theme)['text']))
            item.setForeground(1, QColor(self.theme_manager.get_colors(self._current_theme)['text']))
            self.device_info.addTopLevelItem(item)
        else:
            # Reset to unknown state until facts are received
            self.set_device_icon()

    def start_device_worker(self, hostname, username, password, driver):
        """Start the main device worker with the detected/selected driver"""
        try:
            print(f"Starting connection to {hostname} with driver {driver}")

            # Store connection info for refresh
            self.current_connection = {
                'driver': driver,
                'hostname': hostname,
                'username': username,
                'password': password
            }

            # Create new thread and worker
            self.worker_thread = QThread()
            self.worker = DeviceInfoWorker(driver, hostname, username, password)
            self.worker.moveToThread(self.worker_thread)

            # Connect worker signals
            self.worker.facts_ready.connect(self.update_device_info)
            self.worker.interfaces_ready.connect(self.update_interfaces)
            self.worker.neighbors_ready.connect(self.update_neighbors)
            self.worker.routes_ready.connect(self.update_routes)
            self.worker.error.connect(self.handle_error)

            # Connect thread signals
            self.worker_thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.worker_thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.worker_thread.finished.connect(self.worker_thread.deleteLater)

            self.worker_thread.start()
            self.refresh_timer.start()

        finally:
            self.connect_button.setEnabled(True)
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def handle_fingerprint_error(self, error_msg):
        """Handle errors from the fingerprint worker"""
        self.set_discovery_state(False)  # Reset discovery state
        QMessageBox.warning(
            self,
            "Auto-Detection Failed",
            f"Could not auto-detect device type: {error_msg}\nPlease select a driver manually."
        )
        self.connect_button.setEnabled(True)
        self.setCursor(Qt.CursorShape.ArrowCursor)

    # Update the update_device_info method

    def update_device_info(self, facts):
        """Modified update_device_info to use theme colors"""
        try:
            self.device_info.clear()
            theme_colors = self.theme_manager.get_colors(self._current_theme)

            # Update device icon based on facts
            self.set_device_icon(facts=facts)
            # Store facts for theme changes
            self.current_facts = facts
            # Define key-value pairs to display
            key_facts = [
                ("Hostname", facts.get('hostname', 'N/A')),
                ("Model", facts.get('model', 'N/A')),
                ("is_switch", facts.get('is_switch', 'N/A')),
                ("Serial", facts.get('serial_number', 'N/A')),
                ("OS Version", facts.get('os_version', 'N/A')),
                ("Uptime", str(facts.get('uptime', 'N/A'))),
                ("Vendor", facts.get('vendor', 'N/A'))
            ]

            # Add each fact with theme-consistent colors
            for key, value in key_facts:
                item = QTreeWidgetItem()
                item.setText(0, key)
                item.setText(1, str(value))
                item.setForeground(0, QColor(theme_colors['text']))
                item.setForeground(1, QColor(theme_colors['text']))
                self.device_info.addTopLevelItem(item)

            self.device_info.resizeColumnToContents(0)
            self.device_info.resizeColumnToContents(1)

        except Exception as e:
            print("Error updating device info:", str(e))
            traceback.print_exc()

    def parse_speed(self, speed_str, bandwidth_str):
        # Try SPEED field first
        speed_str = speed_str.strip().lower()

        if "gb/s" in speed_str:
            parts = speed_str.split()
            for part in parts:
                try:
                    return float(part) * 1_000_000_000.0  # Convert Gb/s to bps
                except ValueError:
                    continue

        elif "mb/s" in speed_str:
            parts = speed_str.split()
            for part in parts:
                try:
                    return float(part) * 1_000_000.0  # Convert Mb/s to bps
                except ValueError:
                    continue

        # If SPEED is empty or unparseable, fall back to BANDWIDTH
        parts = bandwidth_str.split()
        bw_val = 10000.0  # Default fallback
        bw_unit = "kbit"

        if len(parts) > 1:
            try:
                bw_val = float(parts[0])
            except ValueError:
                bw_val = 10000.0  # Default fallback
            bw_unit = parts[1].lower()

        if "kbit" in bw_unit:
            return bw_val * 1000.0
        elif "mbit" in bw_unit:
            return bw_val * 1_000_000.0
        elif "gbit" in bw_unit:
            return bw_val * 1_000_000_000.0

        return bw_val * 1000.0  # Default to kbit

    def calculate_utilization(self, details):
        """
        Calculate interface utilization using INPUT_RATE, OUTPUT_RATE, and SPEED.
        All rates should be in the same unit (bps)
        """
        # Convert rates from bps to Mbps for calculation
        input_rate = float(details.get('INPUT_RATE', 0)) / 1_000_000  # Convert to Mbps
        output_rate = float(details.get('OUTPUT_RATE', 0)) / 1_000_000  # Convert to Mbps

        # Speed is already in Mbps from custom_driver
        speed_mbps = float(details.get('SPEED', 10.0))

        # Avoid division by zero
        if speed_mbps <= 0:
            return "0.0%"

        # Calculate utilization as a percentage
        utilization = ((input_rate + output_rate) / (speed_mbps)) * 100
        return f"{utilization:.1f}%"

    def update_interfaces(self, data):
        """Update interface display and store current rates"""
        self.interfaces_tree.clear()
        interfaces = data.get('interfaces', {})
        counters = data.get('counters', {})

        print("\nCurrent interface history sizes:")
        for name, history in self.interface_history.items():
            print(f"{name}: {len(history)} points")

        for name, details in interfaces.items():
            # Get raw rate data directly from the interface details
            rx_rate = float(details.get('input_rate', 0))  # These are in bps
            tx_rate = float(details.get('output_rate', 0))
            total_rate = rx_rate + tx_rate

            # Get speed from bandwidth (which comes in Kbit)
            bandwidth_str = details.get('BANDWIDTH', '10000 Kbit')  # Default to 10Mbit
            try:
                if 'Kbit' in bandwidth_str:
                    speed_mbps = float(bandwidth_str.split()[0]) / 1000  # Convert Kbit to Mbit
                elif 'Mbit' in bandwidth_str:
                    speed_mbps = float(bandwidth_str.split()[0])
                elif 'Gbit' in bandwidth_str:
                    speed_mbps = float(bandwidth_str.split()[0]) * 1000
                else:
                    speed_mbps = 10.0  # Default to 10Mbps if parsing fails
            except (ValueError, IndexError):
                speed_mbps = 10.0  # Default to 10Mbps if parsing fails

            self.interface_speeds[name] = speed_mbps

            # Initialize history if needed
            if name not in self.interface_history:
                print(f"Initializing history for {name}")
                self.interface_history[name] = []

            # Store current rate in history
            self.interface_history[name].append(total_rate)
            print(f"Added point to {name} - now has {len(self.interface_history[name])} points")

            # Trim history if needed
            while len(self.interface_history[name]) > self.history_length:
                self.interface_history[name].pop(0)

            # Calculate utilization based on total rate
            utilization = (total_rate / (speed_mbps * 1_000_000)) * 100

            # Update interface tree
            status = "UP" if details.get('is_up') else "DOWN"
            item = QTreeWidgetItem([
                name,
                status,
                f"{utilization:.1f}%"
            ])

            if status == "UP":
                item.setForeground(1, QColor("#22D3EE"))
            else:
                item.setForeground(1, QColor("#EF4444"))

            self.interfaces_tree.addTopLevelItem(item)

            print(
                f"{name} - Speed: {speed_mbps}Mbps, Total Rate: {total_rate / 1_000_000:.2f}Mbps, Utilization: {utilization:.2f}%")

        self.interfaces_tree.sortItems(0, Qt.SortOrder.AscendingOrder)
        print(f"\nUpdated {len(interfaces)} interfaces")

    def update_interface_graph(self):
        """Update the interface graph with historical data."""
        try:
            selected_items = self.interfaces_tree.selectedItems()
            if not selected_items:
                return

            interface_name = selected_items[0].text(0)
            if interface_name not in self.interface_history:
                print(f"No history data for interface {interface_name}")
                return

            # Get interface speed and history
            speed_mbps = self.interface_speeds.get(interface_name, 10.0)
            history = self.interface_history[interface_name]

            print(f"\nUpdating graph for {interface_name}")
            print(f"Interface speed: {speed_mbps} Mbps")
            print(f"History points: {len(history)}")

            # Create series
            series = QLineSeries()
            max_util = 0.0
            total_util = 0.0
            current_util = 0.0

            # Process each data point
            for i, rate_bps in enumerate(history):
                # Convert rate to utilization percentage
                utilization = (float(rate_bps) / (float(speed_mbps) * 1_000_000)) * 100.0

                # Store current utilization for display
                if i == len(history) - 1:
                    current_util = utilization

                # Add point to series
                series.append(float(i), float(utilization))
                max_util = max(max_util, utilization)
                total_util += utilization

                print(f"Point {i}: {utilization:.2f}% ({rate_bps / 1_000_000:.2f} Mbps)")

            # Calculate average
            avg_util = total_util / len(history) if history else 0

            # Clear and reconfigure chart
            self.chart.removeAllSeries()

            # Make sure axes are visible
            self.axis_x.setVisible(True)
            self.axis_y.setVisible(True)

            # Configure series appearance
            pen = QPen(QColor("#00FF00"))
            pen.setWidth(2)
            series.setPen(pen)

            # Add series to chart
            self.chart.addSeries(series)

            # Explicitly attach axes
            series.attachAxis(self.axis_x)
            series.attachAxis(self.axis_y)

            # Set up axis ranges
            self.axis_x.setRange(0, 30)  # Fixed 30-second window

            if max_util > 0:
                new_max = math.ceil(max_util / 5.0) * 5.0 + 5.0
                if new_max > 100:
                    new_max = 100
                elif new_max < 20:
                    new_max = 20
                self.axis_y.setRange(0, new_max)
                print(f"Y-axis range set to 0-{new_max}%")

            # Update chart title
            self.chart.setTitle(
                f"INTERFACE :: {interface_name} ({speed_mbps} Mbps)\n"
                f"Current: {current_util:.1f}% | Max: {max_util:.1f}% | Avg: {avg_util:.1f}%"
            )

            # Force update
            self.chart_view.update()
            self.chart.update()

        except Exception as e:
            print(f"Error updating graph: {str(e)}")
            traceback.print_exc()

    def set_device_icon(self, device_type=None, facts=None):

        """Update device icon based on type or facts"""
        try:
            theme_colors = self.theme_manager.get_colors(self._current_theme)

            if device_type == 'discovering':
                svg_content = get_discovering_svg()
            elif facts and facts.get('is_switch'):
                svg_content = get_switch_svg()
            elif facts and not facts.get('is_switch'):
                svg_content = get_router_svg()
            else:
                svg_content = get_unknown_svg()

            modified_svg = svg_content.replace('#22D3EE', theme_colors['text'])
            self.device_svg.load(QByteArray(modified_svg.encode()))
        except Exception as e:
            print(f"Error setting device icon: {e}")

    # Modify refresh_data method
    def refresh_data(self):
        """Refresh interface data and update history"""
        try:
            # Check if we have connection info
            if not hasattr(self, 'current_connection'):
                print("No connection information available")
                self.refresh_timer.stop()
                return

            # Clean up any existing worker thread
            self.cleanup_worker()

            # Create new thread and worker
            conn = self.current_connection
            print(f"Refreshing data for {conn['hostname']}")

            self.worker_thread = QThread()
            self.worker = DeviceInfoWorker(
                conn['driver'],
                conn['hostname'],
                conn['username'],
                conn['password']
            )
            self.worker.moveToThread(self.worker_thread)

            # Connect worker signals
            self.worker.facts_ready.connect(self.update_device_info)
            self.worker.interfaces_ready.connect(self.update_interfaces)
            self.worker.neighbors_ready.connect(self.update_neighbors)
            self.worker.routes_ready.connect(self.update_routes)
            self.worker.error.connect(self.handle_error)

            # Connect thread signals
            self.worker_thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.worker_thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.worker_thread.finished.connect(self.worker_thread.deleteLater)

            self.worker_thread.start()

        except Exception as e:
            print(f"Error in refresh_data: {str(e)}")
            import traceback
            traceback.print_exc()

    def setup_chart(self):
        """Modified setup_chart to ensure consistent theme colors"""
        theme_colors = self.theme_manager.get_colors(self._current_theme)

        # Clear and configure chart
        self.chart.removeAllSeries()
        self.chart.setBackgroundVisible(False)
        self.chart.setPlotAreaBackgroundVisible(True)
        self.chart.setBackgroundBrush(QColor(0, 0, 0, 0))
        self.chart.setPlotAreaBackgroundBrush(QColor(theme_colors['chart_bg']))
        self.chart.legend().setVisible(False)
        self.chart.setMargins(QMargins(20, 20, 20, 20))

        # Configure title
        title_font = QFont("Courier New", 10, QFont.Weight.Bold)
        self.chart.setTitleFont(title_font)
        self.chart.setTitleBrush(QColor(theme_colors['text']))

        # Remove existing axes
        for axis in self.chart.axes():
            self.chart.removeAxis(axis)

        # Create and configure axes
        self.axis_x = QValueAxis()
        self.axis_y = QValueAxis()

        # Configure both axes
        for axis in [self.axis_x, self.axis_y]:
            axis.setLabelsColor(QColor(theme_colors['text']))
            axis.setGridLineColor(QColor(theme_colors['grid']))
            axis.setLinePen(QPen(QColor(theme_colors['text'])))
            axis.setGridLinePen(QPen(QColor(theme_colors['grid']), 1, Qt.PenStyle.DotLine))
            axis.setTickCount(6)
            axis.setMinorTickCount(1)
            axis.setLabelsFont(QFont("Courier New", 8))
            title_font = QFont("Courier New", 9, QFont.Weight.Bold)
            axis.setTitleFont(title_font)
            axis.setTitleBrush(QColor(theme_colors['text']))

        # Configure ranges
        self.axis_x.setRange(0, 30)
        self.axis_y.setRange(0, 20)

        # Set titles
        self.axis_x.setTitleText("TIME (s)")
        self.axis_y.setTitleText("UTILIZATION %")

        # Add axes to chart
        self.chart.addAxis(self.axis_x, Qt.AlignmentFlag.AlignBottom)
        self.chart.addAxis(self.axis_y, Qt.AlignmentFlag.AlignLeft)

    def update_neighbors(self, data):
        self.lldp_tree.clear()
        lldp = data.get('lldp', {})
        for local_port in lldp:
            neighbors = lldp[local_port]
            j = 0
            while j < len(neighbors):
                neighbor = neighbors[j]
                item = QTreeWidgetItem([
                    local_port,
                    neighbor.get('hostname', 'N/A'),
                    neighbor.get('port', 'N/A')
                ])
                self.lldp_tree.addTopLevelItem(item)
                j = j + 1

        self.arp_tree.clear()
        arp = data.get('arp', [])
        i = 0
        while i < len(arp):
            entry = arp[i]
            item = QTreeWidgetItem([
                entry.get('ip', 'N/A'),
                entry.get('mac', 'N/A'),
                entry.get('interface', 'N/A')
            ])
            self.arp_tree.addTopLevelItem(item)
            i = i + 1

    def handle_error(self, error_msg):
        QMessageBox.critical(
            self,
            "Connection Error",
            "Error connecting to device:\n" + error_msg
        )
        self.refresh_timer.stop()

    def change_theme(self, theme_name):
        """Handle theme changes for the dashboard"""
        self._current_theme = theme_name
        theme_colors = self.theme_manager.get_colors(theme_name)

        # Update main theme
        self.theme_manager.apply_theme(self, theme_name)

        # Update all LayeredHUDFrame containers
        for frame in [self.device_info_widget, self.interfaces_widget,
                      self.neighbors_widget, self.route_widget]:
            frame.set_theme(theme_name)

        # Update chart and its components
        self.setup_chart()
        if hasattr(self, 'interface_history') and self.interfaces_tree.selectedItems():
            self.update_interface_graph()  # Refresh current graph with new colors

        # Refresh device info if we have facts
        if hasattr(self, 'current_facts'):
            self.update_device_info(self.current_facts)

        # Update device info tree styling
        tree_style = f"""
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
        """

        # Apply styling to all tree widgets
        for tree in [self.device_info, self.interfaces_tree,
                     self.lldp_tree, self.arp_tree, self.route_tree]:
            tree.setStyleSheet(tree_style)

            # Update text colors for all existing items
            self.update_tree_item_colors(tree, theme_colors['text'])

        # Update device icon
        self.set_device_icon()

        # Force visual update
        self.update()
    def update_tree_item_colors(self, tree, color):
        """Recursively update colors for all items in a tree widget"""
        root = tree.invisibleRootItem()
        self._update_tree_item_colors_recursive(root, color)

    def _update_tree_item_colors_recursive(self, item, color):
        """Helper method to recursively update tree item colors"""
        for i in range(item.columnCount()):
            item.setForeground(i, QColor(color))

        for i in range(item.childCount()):
            self._update_tree_item_colors_recursive(item.child(i), color)
        theme_colors = self.theme_manager.get_colors(self._current_theme)

        # Update route raw output styling
        # self.route_raw.setStyleSheet(f"""
        #     QTextEdit {{
        #         background-color: transparent;
        #         color: {self.theme_manager.themes['text']};
        #         border: none;
        #     }}
        # """)

        # Update tabs styling
        tab_style = f"""
            QTabWidget::pane {{
                border: none;
                background: transparent;
            }}
            QTabBar::tab {{
                background: transparent;
                border: 1px solid {theme_colors['text']};
                padding: 5px;
                color: {theme_colors['text']};
            }}
            QTabBar::tab:selected {{
                background: {theme_colors['selected_bg']};
            }}
        """
        self.neighbors_tabs.setStyleSheet(tab_style)
        self.route_tabs.setStyleSheet(tab_style)

        # Update device icon with new theme colors
        self.set_device_icon()

        # Refresh interface colors
        if self.is_connected:
            self.update_interface_colors()

        # Force visual update
        self.update()

    def update_interface_colors(self):
        """Update interface status colors based on current theme"""
        theme_colors = self.theme_manager.get_colors(self._current_theme)

        # Update all interface items
        root = self.interfaces_tree.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            status = item.text(1)
            if status == "UP":
                item.setForeground(1, QColor(theme_colors['success']))
            else:
                item.setForeground(1, QColor(theme_colors['error']))

    def find_longest_prefix_match(self):
        try:
            search_ip = ipaddress.ip_address(self.route_search.text().strip())
            best_match = None
            best_prefix_len = -1
            matching_item = None

            root = self.route_tree.invisibleRootItem()
            item_count = root.childCount()
            i = 0
            while i < item_count:
                item = root.child(i)
                network = item.text(0)
                mask = item.text(1)
                try:
                    network_obj = ipaddress.ip_network(network + "/" + mask)
                    if search_ip in network_obj:
                        prefix_len = network_obj.prefixlen
                        if prefix_len > best_prefix_len:
                            best_prefix_len = prefix_len
                            best_match = network_obj
                            matching_item = item
                except ValueError:
                    pass
                i = i + 1

            if matching_item:
                i = 0
                while i < item_count:
                    root.child(i).setBackground(0, QColor(0, 0, 0, 0))
                    i = i + 1
                matching_item.setBackground(0, QColor("#22D3EE", 40))
                self.route_tree.scrollToItem(matching_item)
                QMessageBox.information(
                    self,
                    "Route Found",
                    "Found matching route:\nNetwork: " + str(best_match) +
                    "\nNext Hop: " + matching_item.text(2) +
                    "\nInterface: " + matching_item.text(4)
                )
            else:
                QMessageBox.warning(
                    self,
                    "No Route Found",
                    "No matching route found for IP: " + str(search_ip)
                )

        except ValueError as e:
            QMessageBox.warning(
                self,
                "Invalid IP",
                "Please enter a valid IP address.\nError: " + str(e)
            )

    def update_routes(self, route_info):
        self.route_tree.clear()
        try:
            structured_routes = route_info.get("structured_routes", {})
            for prefix in structured_routes:
                routes = structured_routes[prefix]
                j = 0
                while j < len(routes):
                    route = routes[j]
                    network, mask = prefix.split('/')
                    item = QTreeWidgetItem([
                        network,
                        mask,
                        route.get('next_hop', ''),
                        route.get('protocol', ''),
                        route.get('outgoing_interface', ''),
                        str(route.get('preference', ''))
                    ])
                    self.route_tree.addTopLevelItem(item)
                    j = j + 1

            raw_output = route_info.get("raw_output", "")
            self.route_raw.setText(raw_output)

            lines = raw_output.split('\n')
            current_network = None
            current_mask = None
            idx = 0
            while idx < len(lines):
                line = lines[idx].strip()
                if line and not line.startswith('Codes:') and not line.startswith('Gateway of'):
                    if 'is subnetted' in line:
                        parts = line.split()
                        current_network = parts[0]
                    else:
                        if (line.startswith('C') or line.startswith('L') or
                            line.startswith('S') or line.startswith('D') or
                            line.startswith('O') or line.startswith('B') or
                            line.startswith('*')):
                            parts = line.split()
                            protocol = parts[0].replace('*', '')
                            if 'via' in line:
                                prefix = parts[1]
                                if '/' not in prefix and current_network:
                                    network = prefix
                                else:
                                    network, mask = prefix.split('/')
                                via_index = 0
                                v = 0
                                while v < len(parts):
                                    if parts[v] == 'via':
                                        via_index = v
                                    v = v + 1
                                next_hop = parts[via_index + 1].rstrip(',')
                                interface = ''
                                last_part = parts[len(parts)-1]
                                if 'Ethernet' in last_part or 'Loopback' in last_part:
                                    interface = last_part
                                metric = ''
                                if '[' in line and ']' in line:
                                    start_idx = line.index('[') + 1
                                    end_idx = line.index(']')
                                    metric = line[start_idx:end_idx]
                                item = QTreeWidgetItem([
                                    network,
                                    mask,
                                    next_hop,
                                    protocol,
                                    interface,
                                    metric
                                ])
                                if protocol in ['C', 'L']:
                                    item.setForeground(0, QColor("#22D3EE"))
                                elif protocol == 'S':
                                    item.setForeground(0, QColor("#10B981"))
                                elif protocol == 'D':
                                    item.setForeground(0, QColor("#3B82F6"))
                                elif protocol == 'O':
                                    item.setForeground(0, QColor("#F59E0B"))
                                self.route_tree.addTopLevelItem(item)
                            else:
                                if 'is directly connected' in line:
                                    network, mask = parts[1].split('/')
                                    next_hop = 'directly connected'
                                    interface = parts[len(parts)-1]
                                    metric = ''
                                    item = QTreeWidgetItem([
                                        network,
                                        mask,
                                        next_hop,
                                        protocol,
                                        interface,
                                        metric
                                    ])
                                    self.route_tree.addTopLevelItem(item)

                idx = idx + 1

            i = 0
            while i < self.route_tree.columnCount():
                self.route_tree.resizeColumnToContents(i)
                i = i + 1

        except Exception as e:
            print("Error updating routes:", e)
            QMessageBox.warning(
                self,
                "Route Update Error",
                "Error updating route information: " + str(e)
            )


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Create container window
    container = QWidget()
    layout = QVBoxLayout(container)

    # Create and add the dashboard widget
    dashboard = DeviceDashboardWidget()
    layout.addWidget(dashboard)

    # Set up window
    container.resize(1400, 900)
    container.show()

    sys.exit(app.exec())