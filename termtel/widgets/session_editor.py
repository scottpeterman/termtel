import sys

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTreeWidget, QTreeWidgetItem, QMenu, QLineEdit, QFormLayout, QComboBox,
                             QWidget, QLabel, QMessageBox, QSpinBox, QFileDialog, QApplication)
from PyQt6.QtCore import Qt
import yaml
from pathlib import Path

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTreeWidget, QTreeWidgetItem, QMenu, QLineEdit, QFormLayout, QComboBox,
                             QWidget, QLabel, QMessageBox, QSpinBox)
from PyQt6.QtCore import Qt
import yaml
from pathlib import Path


class RestrictedTreeWidget(QTreeWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setDragDropMode(QTreeWidget.DragDropMode.InternalMove)
        print("Tree widget initialized")

    def dragMoveEvent(self, event):
        super().dragMoveEvent(event)

        drop_item = self.itemAt(event.position().toPoint())
        drag_item = self.currentItem()

        if not drag_item or not drop_item:
            event.ignore()
            return

        drag_data = drag_item.data(0, Qt.ItemDataRole.UserRole)
        drop_data = drop_item.data(0, Qt.ItemDataRole.UserRole)

        # If we're dropping ON an item...
        if self.dropIndicatorPosition() == self.DropIndicatorPosition.OnItem:
            # Only allow if we're dropping a session onto a folder
            if drag_data['type'] == 'session' and drop_data['type'] == 'folder':
                event.acceptProposedAction()
            else:
                event.ignore()
            return

        # For between-item drops, validate same-folder for sessions
        if drag_data['type'] == 'session':
            if drag_item.parent() != drop_item.parent():
                event.ignore()
                return

        event.acceptProposedAction()

    def dropEvent(self, event):
        drop_item = self.itemAt(event.position().toPoint())
        drag_item = self.currentItem()

        if not drag_item or not drop_item:
            event.ignore()
            return

        drag_data = drag_item.data(0, Qt.ItemDataRole.UserRole)
        drop_data = drop_item.data(0, Qt.ItemDataRole.UserRole)

        # If we're dropping ON an item...
        if self.dropIndicatorPosition() == self.DropIndicatorPosition.OnItem:
            # Only allow if we're dropping a session onto a folder
            if not (drag_data['type'] == 'session' and drop_data['type'] == 'folder'):
                event.ignore()
                return

        # For between-item drops, validate same-folder for sessions
        elif drag_data['type'] == 'session':
            if drag_item.parent() != drop_item.parent():
                event.ignore()
                return

        super().dropEvent(event)

class SessionPropertyDialog(QDialog):
    def __init__(self, session_data=None, parent=None):
        super().__init__(parent)
        self.session_data = session_data or {}
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        self.setWindowTitle("Edit Session Properties")
        layout = QFormLayout(self)

        # Create form fields
        self.fields = {
            'display_name': QLineEdit(),
            'host': QLineEdit(),
            'port': QSpinBox(),
            'DeviceType': QComboBox(),
            'Model': QLineEdit(),
            'SerialNumber': QLineEdit(),
            'SoftwareVersion': QLineEdit(),
            'Vendor': QLineEdit(),
            'credsid': QLineEdit()
        }

        # Configure widgets
        self.fields['port'].setRange(1, 65535)
        self.fields['DeviceType'].addItems(["Linux", "cisco_ios", "hp_procurve"])

        # Add fields to layout
        layout.addRow("Display Name:", self.fields['display_name'])
        layout.addRow("Host:", self.fields['host'])
        layout.addRow("Port:", self.fields['port'])
        layout.addRow("Device Type:", self.fields['DeviceType'])
        layout.addRow("Model:", self.fields['Model'])
        layout.addRow("Serial Number:", self.fields['SerialNumber'])
        layout.addRow("Software Version:", self.fields['SoftwareVersion'])
        layout.addRow("Vendor:", self.fields['Vendor'])
        layout.addRow("Credentials ID:", self.fields['credsid'])

        # Add buttons
        button_box = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_box.addWidget(save_btn)
        button_box.addWidget(cancel_btn)

        layout.addRow(button_box)

    def load_data(self):
        for key, widget in self.fields.items():
            value = self.session_data.get(key, '')
            if isinstance(widget, QLineEdit):
                widget.setText(str(value))
            elif isinstance(widget, QComboBox):
                index = widget.findText(value)
                if index >= 0:
                    widget.setCurrentIndex(index)
            elif isinstance(widget, QSpinBox):
                widget.setValue(int(value) if value else 22)

    def get_data(self):
        data = {}
        for key, widget in self.fields.items():
            if isinstance(widget, QLineEdit):
                data[key] = widget.text()
            elif isinstance(widget, QComboBox):
                data[key] = widget.currentText()
            elif isinstance(widget, QSpinBox):
                data[key] = str(widget.value())
        return data


class SessionEditorDialog(QDialog):
    def __init__(self, parent=None, session_file=None):
        super().__init__(parent)
        self.session_file = session_file
        self.sessions_data = []
        self.setup_ui()
        if session_file:
            self.load_sessions()

    def setup_ui(self):
        self.setWindowTitle("Edit Sessions")
        self.resize(800, 600)

        layout = QVBoxLayout(self)

        # Tree widget
        self.tree = RestrictedTreeWidget()
        self.tree.setHeaderLabel("Sessions")
        self.tree.setDragEnabled(True)
        self.tree.setAcceptDrops(True)
        self.tree.setDragDropMode(QTreeWidget.DragDropMode.InternalMove)
        self.tree.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        self.tree.itemDoubleClicked.connect(self.edit_item)
        layout.addWidget(self.tree)

        # Buttons
        button_layout = QHBoxLayout()
        add_folder_btn = QPushButton("Add Folder")
        add_folder_btn.clicked.connect(self.add_folder)
        add_session_btn = QPushButton("Add Session")
        add_session_btn.clicked.connect(self.add_session)
        close_btn = QPushButton("Save && Close")
        close_btn.clicked.connect(self.save_and_close)

        button_layout.addWidget(add_folder_btn)
        button_layout.addWidget(add_session_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)

    def edit_item(self, item):
        """Handle double-click editing of items"""
        item_data = item.data(0, Qt.ItemDataRole.UserRole)

        if item_data['type'] == 'folder':
            # Simple folder name edit
            name, ok = QLineEdit.getText(
                self, "Edit Folder", "Folder name:",
                QLineEdit.EchoMode.Normal, item.text(0)
            )
            if ok and name:
                item.setText(0, name)
        else:
            # Show session property dialog
            dialog = SessionPropertyDialog(item_data['data'], self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                new_data = dialog.get_data()
                item_data['data'] = new_data
                item.setData(0, Qt.ItemDataRole.UserRole, item_data)
                item.setText(0, new_data.get('display_name', new_data.get('host', 'New Session')))

    def load_sessions(self):
        try:
            with open(self.session_file) as f:
                self.sessions_data = yaml.safe_load(f)

            self.tree.clear()
            for folder in self.sessions_data:
                folder_item = QTreeWidgetItem(self.tree)
                folder_item.setText(0, folder['folder_name'])
                folder_item.setData(0, Qt.ItemDataRole.UserRole, {'type': 'folder'})

                for session in folder.get('sessions', []):
                    session_item = QTreeWidgetItem(folder_item)
                    session_item.setText(0, session.get('display_name', session['host']))
                    session_item.setData(0, Qt.ItemDataRole.UserRole, {
                        'type': 'session',
                        'data': session
                    })

            self.tree.expandAll()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load sessions: {str(e)}")

    def save_sessions(self):
        try:
            new_data = []
            for folder_idx in range(self.tree.topLevelItemCount()):
                folder_item = self.tree.topLevelItem(folder_idx)
                folder_data = {
                    'folder_name': folder_item.text(0),
                    'sessions': []
                }

                for session_idx in range(folder_item.childCount()):
                    session_item = folder_item.child(session_idx)
                    session_data = session_item.data(0, Qt.ItemDataRole.UserRole)['data']
                    folder_data['sessions'].append(session_data)

                new_data.append(folder_data)

            with open(self.session_file, 'w') as f:
                yaml.safe_dump(new_data, f, default_flow_style=False)

            return True

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save sessions: {str(e)}")
            return False

    def save_and_close(self):
        if self.save_sessions():
            self.accept()

    def show_context_menu(self, position):
        item = self.tree.itemAt(position)
        if not item:
            return

        menu = QMenu(self)
        menu.addAction("Edit", lambda: self.edit_item(item))
        if item.data(0, Qt.ItemDataRole.UserRole)['type'] == 'folder':
            menu.addAction("Add Session", lambda: self.add_session(item))
        menu.addAction("Delete", lambda: self.delete_item(item))
        menu.exec(self.tree.viewport().mapToGlobal(position))

    def add_folder(self):
        name, ok = QLineEdit.getText(self, "New Folder", "Folder name:")
        if ok and name:
            folder_item = QTreeWidgetItem(self.tree)
            folder_item.setText(0, name)
            folder_item.setData(0, Qt.ItemDataRole.UserRole, {'type': 'folder'})
            self.tree.setCurrentItem(folder_item)

    def add_session(self, parent_folder=None):
        if not parent_folder:
            selected = self.tree.selectedItems()
            parent_folder = selected[0] if selected and selected[0].data(0, Qt.ItemDataRole.UserRole)[
                'type'] == 'folder' else None

        if not parent_folder:
            QMessageBox.warning(self, "Warning", "Please select a folder first")
            return

        # Create new session with defaults
        session_data = {
            'display_name': 'New Session',
            'host': '',
            'port': '22',
            'DeviceType': 'Linux',
            'Model': '',
            'SerialNumber': '',
            'SoftwareVersion': '',
            'Vendor': '',
            'credsid': ''
        }

        # Show property dialog for new session
        dialog = SessionPropertyDialog(session_data, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            session_data = dialog.get_data()
            session_item = QTreeWidgetItem(parent_folder)
            session_item.setText(0, session_data.get('display_name', session_data.get('host', 'New Session')))
            session_item.setData(0, Qt.ItemDataRole.UserRole, {
                'type': 'session',
                'data': session_data
            })
            self.tree.setCurrentItem(session_item)

    def delete_item(self, item):
        if QMessageBox.question(
                self,
                "Confirm Delete",
                f"Are you sure you want to delete {item.text(0)}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            parent = item.parent()
            if parent:
                parent.removeChild(item)
            else:
                self.tree.takeTopLevelItem(self.tree.indexOfTopLevelItem(item))
def main():
    app = QApplication(sys.argv)

    # Prompt for file selection
    file_path, _ = QFileDialog.getOpenFileName(
        None,
        "Select Session File",
        str(Path.home()),
        "YAML Files (*.yaml *.yml);;All Files (*.*)"
    )

    if not file_path:
        sys.exit(0)

    try:
        editor = SessionEditorDialog(session_file=file_path)
        result = editor.exec()

        if result == editor.DialogCode.Accepted:
            QMessageBox.information(None, "Success", "Sessions file saved successfully!")

    except Exception as e:
        QMessageBox.critical(None, "Error", f"An error occurred: {str(e)}")

    sys.exit(0)


if __name__ == "__main__":
    main()