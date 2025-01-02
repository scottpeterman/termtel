from PyQt6.QtCore import QThread, pyqtSignal
import socket
from contextlib import closing
import logging

logger = logging.getLogger(__name__)


class ConnectionCheckerThread(QThread):
    connection_status = pyqtSignal(bool, str)

    def __init__(self, host, port, timeout=2):
        super().__init__()
        self.host = host
        self.port = int(port)
        self.timeout = timeout

    def run(self):
        try:
            with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
                sock.settimeout(self.timeout)
                logger.info(f"Checking connection to {self.host}:{self.port}")
                result = sock.connect_ex((self.host, self.port))
                if result == 0:
                    logger.info(f"Connection check successful for {self.host}:{self.port}")
                    self.connection_status.emit(True, "")
                else:
                    logger.warning(f"Port {self.port} is not reachable on {self.host}")
                    self.connection_status.emit(False, f"Port {self.port} is not reachable")
        except socket.gaierror:
            logger.error(f"Could not resolve hostname: {self.host}")
            self.connection_status.emit(False, "Could not resolve hostname")
        except Exception as e:
            logger.error(f"Connection check error for {self.host}:{self.port}: {e}")
            self.connection_status.emit(False, str(e))