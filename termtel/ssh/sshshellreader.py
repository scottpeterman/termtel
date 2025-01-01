from PyQt6.QtCore import pyqtSignal, QThread
import os

class ShellReaderThread(QThread):
    data_ready = pyqtSignal(str)

    def __init__(self, channel, buffer, parent_widget):
        super().__init__()
        self.channel = channel
        self.intial_buffer = buffer
        self.parent_widget = parent_widget
        if parent_widget.log_filename is not None:
            self.log_filename = parent_widget.log_filename
        else:
            self.log_filename = "../logs/session.log"

        # Ensure log directory exists
        os.makedirs(os.path.dirname(self.log_filename), exist_ok=True)

    def log_data(self, data):
        # Make sure that a log filename was provided
        if self.log_filename is not None:
            try:
                # Attempt to encode and decode the data as UTF-8 to ensure it's valid
                data = data.encode('utf-8', 'ignore').decode('utf-8', 'ignore')
                data = data.replace('\r\n', '\n').replace('\r', '\n')
                with open(self.log_filename, 'a', encoding='utf-8') as log_file: # 'a' option will append data to the end of the file
                    # log_file.write(data + os.linesep)
                    log_file.write(data)
            except UnicodeError:
                print("Failed to encode data as UTF-8.")


    def run(self):
        while True:
            if not self.channel.closed:
                try:
                    data = self.channel.recv(1024)

                    if data:
                        data_decoded = data.decode()
                        # Log data that is being received
                        self.log_data(data_decoded)

                        # for debugging
                        if self.intial_buffer == "":
                            self.intial_buffer = bytes(data).decode('utf-8')
                            self.parent_widget.initial_buffer = bytes(data).decode('utf-8')

                        self.data_ready.emit(data_decoded)
                except Exception as e:
                    print(f"Error while reading from channel: {e}")
                    self.log_data(f"Error while reading from channel: {e}")
            else:
                print("Channel closed...")
                self.log_data("Channel closed...")
                break
