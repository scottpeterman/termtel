import json
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLineEdit, QPushButton,
                             QProgressBar, QLabel, QFileDialog)
import pynetbox
import yaml
import urllib3
from termtel.themes2 import LayeredHUDFrame

# Suppress only the single InsecureRequestWarning from urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class DownloadThread(QThread):
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)
    save_file_signal = pyqtSignal(object)

    def __init__(self, token, url):
        QThread.__init__(self)
        self.token = token
        self.url = url

    def run(self):
        try:
            self.status_signal.emit("Connecting to Netbox")
            netbox = pynetbox.api(self.url, token=self.token)
            netbox.http_session.verify = False  # This is insecure; use with caution

            self.status_signal.emit("Downloading Data")
            uglypty_list = []

            # First loop to count total sites
            site_list = []
            sites = netbox.dcim.sites.all()
            for temp_site in sites:
                print(f"Site Preloading: {temp_site.name}")
                site_list.append(temp_site)
            total_sites = len(site_list)

            # Reset progress bar
            counter = 0

            # Second loop to actually get the data
            for site in site_list:
                folder_dict = {}
                folder_dict['folder_name'] = site.slug
                folder_dict['sessions'] = []
                devices = netbox.dcim.devices.filter(site_id=site.id)

                for device in devices:
                    session = {}
                    try:
                        session['DeviceType'] = device.device_role.name if device.device_role else 'Unknown'
                        session['Model'] = device.device_type.model
                        session['SerialNumber'] = device.serial
                        session['SoftwareVersion'] = 'Unknown'
                        session[
                            'Vendor'] = device.device_type.manufacturer.name if device.device_type.manufacturer else 'Unknown'
                        session['credsid'] = '1'
                        session['display_name'] = device.name
                        session['host'] = str(device.primary_ip4.address).split("/")[
                            0] if device.primary_ip4 else 'Unknown'
                        session['port'] = '22'

                        folder_dict['sessions'].append(session)
                        print(f"Processed: {device.name}")
                    except Exception as e:
                        print(f"Error processing device: {device.name}")
                        print(e)

                uglypty_list.append(folder_dict)
                counter += 1
                print(f"Site Number: {counter} of {total_sites}")

                # Update the progress bar
                self.progress_signal.emit((counter * 100) // total_sites)

            # save successful settings
            settings = {
                "token": self.token,
                "url": self.url
            }
            try:
                with open("netbox_settings.json", "w") as f:
                    json.dump(settings, f)
            except Exception as e:
                print(f"failed to save netbox settings! {e}")

            self.save_file_signal.emit(uglypty_list)
            self.status_signal.emit("Download Complete")
            self.progress_signal.emit(100)

        except Exception as e:
            print("An error occurred:", e)
            self.status_signal.emit(f"Error: {str(e)}")


def create_default_settings():
    default_settings = {
        "token": "",
        "url": "http://netbox.yourcompany.com"
    }
    with open("netbox_settings.json", "w") as f:
        json.dump(default_settings, f)


class App(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.parent.nbimporter = self
        self.title = 'Netbox to Terminal YAML Exporter'

        # Load Netbox settings from JSON if exists, else create it
        try:
            with open("netbox_settings.json", "r") as f:
                settings = json.load(f)
            self.default_token = settings.get("token", "")
            self.default_url = settings.get("url", "http://netbox.yourcompany.com")
        except FileNotFoundError:
            create_default_settings()
            self.default_token = ""
            self.default_url = "http://netbox.yourcompany.com"

        # Create main frame using LayeredHUDFrame
        self.main_frame = LayeredHUDFrame(self,
                                          theme_manager=self.parent.theme_manager,
                                          theme_name=self.parent.theme)
        self.initUI()

    def initUI(self):
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.main_frame)

        # Content layout inside the frame
        layout = QVBoxLayout()
        self.main_frame.content_layout.addLayout(layout)

        # Title label
        title_label = QLabel("Netbox Session Import")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Token input
        self.tokenField = QLineEdit(self)
        self.tokenField.setPlaceholderText('Enter your Netbox Token')
        self.tokenField.setText(self.default_token)
        layout.addWidget(self.tokenField)

        # URL input
        self.urlField = QLineEdit(self)
        self.urlField.setPlaceholderText('Enter your Netbox URL')
        self.urlField.setText(self.default_url)
        layout.addWidget(self.urlField)

        # Download button
        self.downloadButton = QPushButton('Download', self)
        self.downloadButton.clicked.connect(self.startDownloadThread)
        layout.addWidget(self.downloadButton)

        # Progress bar
        self.progress = QProgressBar(self)
        layout.addWidget(self.progress)

        # Status label
        self.statusLabel = QLabel('Status: Waiting', self)
        self.statusLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.statusLabel)

        # Add some spacing at the bottom
        layout.addStretch()

        # Set minimum size
        self.setMinimumWidth(400)
        self.setMinimumHeight(200)

    def update_theme(self, theme_name: str):
        """Update the widget's theme."""
        if hasattr(self, 'main_frame'):
            self.main_frame.set_theme(theme_name)

        # Get theme colors
        colors = self.parent.theme_manager.get_colors(theme_name)

        # Update progress bar style
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {colors['border']};
                border-radius: 0px;
                background-color: {colors['darker_bg']};
                color: {colors['text']};
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {colors['primary']};
            }}
        """)

        # Update button style
        self.downloadButton.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['primary']};
                color: {colors['background']};
                border: none;
                padding: 8px;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: {colors['button_hover']};
            }}
            QPushButton:pressed {{
                background-color: {colors['button_pressed']};
            }}
            QLineEdit {{
                background-color: {colors.darker_bg};
                color: {colors.text};
                border: 1px solid {colors.border_light};
                border-radius: 0;
                padding: 5px;
                font-family: "Courier New";
                selection-background-color: {colors.selected_bg};
            }}

            QLineEdit::placeholder {{
                color: {colors.border_light};
            }}
        """)

    def startDownloadThread(self):
        self.downloadButton.setEnabled(False)
        self.downloadThread = DownloadThread(self.tokenField.text(), self.urlField.text())
        self.downloadThread.progress_signal.connect(self.updateProgressBar)
        self.downloadThread.status_signal.connect(self.updateStatusLabel)
        self.downloadThread.save_file_signal.connect(self.showSaveFileDialog)
        self.downloadThread.finished.connect(lambda: self.downloadButton.setEnabled(True))
        self.downloadThread.start()

    def showSaveFileDialog(self, uglypty_list):
        filePath, _ = QFileDialog.getSaveFileName(
            self, "Save File", "", "YAML Files (*.yaml);;All Files (*)")
        if filePath:
            if not filePath.endswith('.yaml'):
                filePath += '.yaml'
            with open(filePath, "w") as f:
                yaml.dump(uglypty_list, f, default_flow_style=False)
            self.statusLabel.setText(f"Saved to {filePath}")

    def updateProgressBar(self, value):
        self.progress.setValue(value)

    def updateStatusLabel(self, text):
        self.statusLabel.setText(f"Status: {text}")