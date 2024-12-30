# custom_driver.py
import traceback
from pathlib import Path

from termtel.tfsm_fire import TextFSMAutoEngine


class CustomDriver:
    def __init__(self, device):
        self.device = device
        BASE_DIR = Path(__file__)
        db_path = str(BASE_DIR.parent) + "/templates.db"
        self.engine = TextFSMAutoEngine(db_path)

    def _parse_speed(self, speed_str, bandwidth_str):
        """
        Parse speed from SPEED or BANDWIDTH field.
        Returns speed in Mbps.
        """
        try:
            if "Gb/s" in speed_str:
                splitted = speed_str.split()
                if splitted and len(splitted) > 0:
                    return float(splitted[0]) * 1000.0  # Convert Gb/s to Mbps
            elif "Mb/s" in speed_str:
                splitted = speed_str.split()
                if splitted and len(splitted) > 0:
                    return float(splitted[0])  # Already in Mbps
            elif "Kbit" in bandwidth_str:
                splitted = bandwidth_str.split()
                if splitted and len(splitted) > 0:
                    return float(splitted[0]) / 1000.0  # Convert Kbps to Mbps
            elif "Mbit" in bandwidth_str:
                splitted = bandwidth_str.split()
                if splitted and len(splitted) > 0:
                    return float(splitted[0])  # Already in Mbps
        except:
            pass
        return 1000.0  # Default to 1 Gbps (1000 Mbps) instead of 10 Mbps

    def parse_interface_info(self, name, intf, device_type='ios'):
        common_data = {}
        common_data['is_up'] = False
        if 'up' in intf.get('PROTOCOL_STATUS', '').lower():
            common_data['is_up'] = True

        common_data['is_enabled'] = False
        if 'up' in intf.get('LINK_STATUS', '').lower():
            common_data['is_enabled'] = True

        common_data['description'] = intf.get('DESCRIPTION', '')
        common_data['mac_address'] = intf.get('MAC_ADDRESS', '')
        try:
            common_data['mtu'] = int(intf.get('MTU', 0))
        except:
            common_data['mtu'] = 0

        if device_type == 'ios':
            # Parse speed (BANDWIDTH typically in Kbit)
            speed_str = intf.get('BANDWIDTH', '0')
            speed_value = 10.0
            try:
                splitted = speed_str.split()
                if splitted and len(splitted) > 0:
                    # If it contains "Kbit", convert to Mbps
                    if "Kbit" in speed_str:
                        speed_value = float(splitted[0]) / 1000.0
                    else:
                        # If no unit given, assume it's Kbps
                        speed_value = float(splitted[0]) / 1000.0
            except:
                speed_value = 10.0

            try:
                input_rate = float(intf.get('INPUT_RATE', 0))
            except:
                input_rate = 0.0
            try:
                output_rate = float(intf.get('OUTPUT_RATE', 0))
            except:
                output_rate = 0.0

            input_packets = 0
            output_packets = 0
            try:
                input_packets = int(intf.get('INPUT_PACKETS', 0) or 0)
            except:
                input_packets = 0
            try:
                output_packets = int(intf.get('OUTPUT_PACKETS', 0) or 0)
            except:
                output_packets = 0

            common_data['speed'] = speed_value
            common_data['input_rate'] = input_rate
            common_data['output_rate'] = output_rate
            common_data['input_packets'] = input_packets
            common_data['output_packets'] = output_packets

        elif device_type == 'nxos':
            speed = self._parse_speed(intf.get('SPEED', ''), intf.get('BANDWIDTH', ''))

            try:
                input_rate = float(intf.get('INPUT_RATE', 0))
            except:
                input_rate = 0.0
            try:
                output_rate = float(intf.get('OUTPUT_RATE', 0))
            except:
                output_rate = 0.0

            input_packets = 0
            output_packets = 0
            try:
                input_packets = int(intf.get('INPUT_PACKETS', 0) or 0)
            except:
                input_packets = 0
            try:
                output_packets = int(intf.get('OUTPUT_PACKETS', 0) or 0)
            except:
                output_packets = 0

            common_data['speed'] = speed
            common_data['input_rate'] = input_rate
            common_data['output_rate'] = output_rate
            common_data['input_packets'] = input_packets
            common_data['output_packets'] = output_packets

        else:
            raise ValueError("Unsupported device type: " + device_type)

        return common_data

    def get_interfaces_custom(self):
        """Get interface details using TextFSM parsing, including rates and counters."""
        if self.device.platform == "nxos_ssh":
            interface_cmd = "show interface"
        else:
            interface_cmd = "show interfaces"

        output = self.device.cli([interface_cmd])

        if 'eos' in self.device.platform:
            hint = "arista_eos_show_interfaces"
        elif 'nxos' in self.device.platform:
            hint = "cisco_nxos_show_ip_interface"
        else:
            hint = "cisco_ios_show_interfaces"

        template, parsed, score = self.engine.find_best_template(output[interface_cmd], hint)
        print("Best template:", interface_cmd, "Score:", score)
        if score < 5:
            template, parsed, score = self.engine.find_best_template(output[interface_cmd], 'cisco_nxos_show_interface')

        if not parsed:
            return {}, {}

        interfaces = {}
        counters = {}
        print("Parsed show interfaces")
        print(parsed)
        print("Reading parsed data...")
        print("Detected driver for parsing:", self.device.platform)

        try:
            index = 0
            while index < len(parsed):
                intf = parsed[index]
                name = intf.get('INTERFACE', '')
                device_type = "ios"
                if "ios" in self.device.platform:
                    device_type = "ios"
                elif "nxos" in self.device.platform:
                    device_type = "nxos"
                else:
                    device_type = "ios"

                interfaces[name] = self.parse_interface_info(name, intf, device_type)

                def safe_int(value, default=0):
                    try:
                        if value:
                            return int(value)
                        return default
                    except:
                        return default

                tx_unicast_packets = safe_int(intf.get('OUTPUT_PACKETS'))
                rx_unicast_packets = safe_int(intf.get('INPUT_PACKETS'))
                tx_errors = safe_int(intf.get('OUTPUT_ERRORS'))
                rx_errors = safe_int(intf.get('INPUT_ERRORS'))
                tx_rate = 0.0
                rx_rate = 0.0
                try:
                    tx_rate = float(intf.get('OUTPUT_RATE', 0))
                except:
                    tx_rate = 0.0
                try:
                    rx_rate = float(intf.get('INPUT_RATE', 0))
                except:
                    rx_rate = 0.0

                c_dict = {}
                c_dict['tx_unicast_packets'] = tx_unicast_packets
                c_dict['rx_unicast_packets'] = rx_unicast_packets
                c_dict['tx_errors'] = tx_errors
                c_dict['rx_errors'] = rx_errors
                c_dict['tx_rate'] = tx_rate
                c_dict['rx_rate'] = rx_rate

                counters[name] = c_dict

                index = index + 1

        except Exception as e:
            print("Error reading parsed data:", e)
            traceback.print_exc()

        return interfaces, counters
