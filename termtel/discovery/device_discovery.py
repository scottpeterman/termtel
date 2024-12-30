import time
import logging
import paramiko
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from termtel.tfsm_fire import TextFSMAutoEngine


@dataclass
class DeviceFingerprint:
    """Container for device discovery results"""
    device_type: str
    confidence_score: float
    template_name: str
    processing_time: float
    parsed_data: List[Dict]


class DeviceDiscovery:
    """Handles device fingerprinting and data extraction using TextFSM templates"""

    def __init__(self, template_db: str, verbose: bool = False):
        self.template_db = template_db
        self.verbose = verbose
        self.logger = self._setup_logger()
        self.engine = TextFSMAutoEngine(template_db, verbose)

    def _setup_logger(self) -> logging.Logger:
        """Configure logging"""
        logger = logging.getLogger('device_discovery')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.DEBUG if self.verbose else logging.INFO)
        return logger

    def process_device(self, host: str, username: str, password: str,
                       ssh_timeout: int = 60) -> Optional[DeviceFingerprint]:
        """
        Process a device to determine its type and extract relevant data

        Args:
            host: Device hostname/IP
            username: SSH username
            password: SSH password
            ssh_timeout: SSH connection timeout in seconds

        Returns:
            DeviceFingerprint object or None if discovery fails
        """
        start_time = time.time()
        client = None
        channel = None

        try:
            # Establish connection
            client, channel = self._establish_connection(host, username, password, ssh_timeout)

            # Get and process version info
            device_info = self._get_device_info(channel)

            # If we successfully identified the device, get neighbor data
            if device_info['confidence'] > 40:
                neighbor_data = self._get_neighbor_info(channel, device_info['device_type'])
                if neighbor_data and device_info['parsed_data']:
                    device_info['parsed_data'][0]['NEIGHBOR_DATA'] = neighbor_data

            processing_time = time.time() - start_time

            return DeviceFingerprint(
                device_type=device_info['device_type'],
                confidence_score=device_info['confidence'],
                template_name=device_info['template_name'],
                processing_time=processing_time,
                parsed_data=device_info['parsed_data']
            )

        except Exception as e:
            self.logger.error(f"Discovery failed for {host}: {str(e)}")
            return None

        finally:
            self._cleanup_connection(channel, client)

    def _establish_connection(self, host: str, username: str, password: str,
                              ssh_timeout: int) -> tuple[paramiko.SSHClient, paramiko.Channel]:
        """Establish SSH connection and get interactive shell"""
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                hostname=host,
                username=username,
                password=password,
                timeout=ssh_timeout,
                look_for_keys=False
            )

            channel = client.invoke_shell()
            channel.settimeout(ssh_timeout)

            # Disable pagination
            self._send_command(channel, "terminal length 0")

            self.logger.info(f"Successfully connected to {host}")
            return client, channel

        except Exception as e:
            if client:
                client.close()
            raise Exception(f"Connection failed: {str(e)}")

    def _get_device_info(self, channel: paramiko.Channel) -> dict:
        """Get and process device version information"""
        try:
            # Get version output
            version_output = self._send_command(channel, "show version")

            # Match template and parse output
            template_name, parsed_data, confidence = self.engine.find_best_template(
                version_output,
                filter_string="show_version"
            )

            # Extract device type from template name
            if template_name:
                device_type = "_".join(template_name.split("_")[:-2])
            else:
                device_type = "unknown"
                parsed_data = [{}]
                confidence = 0.0

            return {
                'device_type': device_type,
                'template_name': template_name or "unknown",
                'confidence': confidence,
                'parsed_data': parsed_data or [{}]
            }

        except Exception as e:
            self.logger.error(f"Failed to get device info: {str(e)}")
            raise

    def _get_neighbor_info(self, channel: paramiko.Channel, device_type: str) -> Optional[str]:
        """Get neighbor information based on device type"""
        try:
            if device_type.lower() == 'cisco_ios':
                return self._send_command(channel, "show cdp neighbors detail", wait_time=5)
            elif device_type.lower() == 'arista_eos':
                return self._send_command(channel, "show lldp neighbors detail", wait_time=5)
            return None
        except Exception as e:
            self.logger.warning(f"Failed to get neighbor data: {str(e)}")
            return None

    def _send_command(self, channel: paramiko.Channel, command: str,
                      wait_time: float = 2) -> str:
        """Send command and wait for output"""
        try:
            channel.send(command + "\n")
            time.sleep(wait_time)  # Wait for command completion

            output = ""
            while channel.recv_ready():
                output += channel.recv(4096).decode('utf-8')
            return output
        except Exception as e:
            raise Exception(f"Command '{command}' failed: {str(e)}")

    def _cleanup_connection(self, channel: Optional[paramiko.Channel],
                            client: Optional[paramiko.SSHClient]) -> None:
        """Clean up SSH connections"""
        if channel:
            try:
                channel.close()
            except:
                pass
        if client:
            try:
                client.close()
            except:
                pass

    def _get_neighbor_command(self, device_type: str) -> Optional[str]:
        """Get the appropriate neighbor discovery command for device type"""
        commands = {
            'cisco_ios': 'show cdp neighbors detail',
            'arista_eos': 'show lldp neighbors detail',
            'juniper_junos': 'show lldp neighbors detail',
        }
        return commands.get(device_type.lower())