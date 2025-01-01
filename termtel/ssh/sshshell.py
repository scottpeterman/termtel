from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from .sshshellreader import ShellReaderThread
from PyQt6.QtWidgets import QMessageBox
import paramiko


class Backend(QObject):
    send_output = pyqtSignal(str)
    buffer = ""

    def __init__(self, host, username, password=None, port='22', key_path=None, parent_widget=None, parent=None):
        super().__init__(parent)
        self.parent_widget = parent_widget
        self.client = None
        self.channel = None
        self.reader_thread = None

        try:
            self.client = paramiko.SSHClient()
            self.client.load_system_host_keys()  # Load known host keys from the system
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # Automatically add unknown hosts
            host = str(host).strip()
            username = str(username).strip()

            if key_path:
                try:
                    private_key = paramiko.RSAKey(filename=key_path.strip())
                    self.client.connect(hostname=host, username=username, pkey=private_key)
                    transport = self.client.get_transport()
                    transport.set_keepalive(60)
                except paramiko.AuthenticationException as e:
                    self.notify("Login Failure", f"Authentication Failed: {host}")
                    return
                except paramiko.SSHException as e:
                    self.notify("Login Failure", f"Connection Failed: {host} Reason: {e}")
                    return
                except Exception as e:
                    self.notify("Error", str(e))
                    return
            else:
                password = str(password).strip()
                try:
                    self.client.connect(hostname=host, port=int(port), username=username, password=password, look_for_keys=False)
                    transport = self.client.get_transport()
                    transport.set_keepalive(60)
                except paramiko.AuthenticationException as e:
                    self.notify("Login Failure", f"Authentication Failed: {host}")
                    return
                except paramiko.SSHException as e:
                    self.notify("Login Failure", f"Connection Failed: {host} Reason: {e}")
                    return
                except Exception as e:
                    self.notify("Error", str(e))
                    return

            self.setup_shell()

        except Exception as e:
            self.notify("Connection Error", str(e))
            print(e)

    def setup_shell(self):
        try:
            self.channel = self.client.invoke_shell("xterm")
            self.channel.set_combine_stderr(True)
            print("Invoked Shell!")
        except Exception as e:
            print(f"Shell not supported, falling back to pty...")
            transport = self.client.get_transport()
            options = transport.get_security_options()
            print(options)

            self.channel = transport.open_session()
            self.channel.get_pty()  # Request a pseudo-terminal
            self.channel.set_combine_stderr(True)

        # Start reading the channel
        if self.channel is not None:
            self.reader_thread = ShellReaderThread(self.channel, self.buffer, parent_widget=self.parent_widget)
            self.reader_thread.data_ready.connect(self.send_output)
            self.reader_thread.start()

    def notify(self, message, info):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setText(info)
        msg.setWindowTitle(message)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        retval = msg.exec()

    @pyqtSlot(str)
    def write_data(self, data):

        if self.channel and self.channel.send_ready():
            try:
                self.channel.send(data)
            except paramiko.SSHException as e:
                print(f"Error while writing to channel: {e}")
            except Exception as e:
                print(f"Channel error {e}")
                self.notify("Closed", "Connection is closed.")

                pass
        else:
            print("Error: Channel is not ready or doesn't exist")
            self.notify("Error", "Channel is not ready or doesn't exist")

    @pyqtSlot(str)
    def set_pty_size(self, data):
        if self.channel and self.channel.send_ready():
            try:
                cols = data.split("::")[0]
                cols = int(cols.split(":")[1])
                rows = data.split("::")[1]
                rows = int(rows.split(":")[1])
                self.channel.resize_pty(width=cols, height=rows)
                print(f"backend pty resize -> cols:{cols} rows:{rows}")
            except paramiko.SSHException as e:
                print(f"Error setting backend pty term size: {e}")
        else:
            print("Error: Channel is not ready or doesn't exist")

    def __del__(self):
        if self.reader_thread and self.reader_thread.isRunning():
            self.reader_thread.terminate()

        if self.channel:
            self.channel.close()

        if self.client:
            self.client.close()
