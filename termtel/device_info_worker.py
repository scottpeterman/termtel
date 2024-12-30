# device_info_worker.py

import json
import traceback
from pprint import pprint

from napalm import get_network_driver
from PyQt6.QtCore import QThread, pyqtSignal

from termtel.custom_driver import CustomDriver

class DeviceInfoWorker(QThread):
    """Worker thread to handle device operations without blocking the UI"""
    facts_ready = pyqtSignal(object)
    interfaces_ready = pyqtSignal(object)
    neighbors_ready = pyqtSignal(object)
    routes_ready = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, driver, hostname: str, username: str, password: str):
        super().__init__()
        self.driver = driver
        self.hostname = hostname
        self.username = username
        self.password = password

    def run(self):
        try:
            device_open = False

            # Initialize NAPALM driver
            self.driver = get_network_driver(self.driver)
            driver = self.driver

            # Handle NXOS - switch to SSH if detected
            if 'nxos' in str(driver):
                self.driver = 'nxos_ssh'
                optional_args = {
                    'transport': 'ssh',
                    'port': 22
                }
                driver = get_network_driver(self.driver)
                device = driver(
                    hostname=self.hostname,
                    username=self.username,
                    password=self.password,
                    optional_args=optional_args
                )

            # Handle EOS with proper scope for SSH connection
            elif 'eos' in str(self.driver):
                optional_args = {
                     'transport': 'ssh',
                'use_eapi': False
                }

                device = driver(
                    hostname=self.hostname,
                    username=self.username,
                    password=self.password,
                    optional_args=optional_args
                )

            # Handle all other device types
            else:
                device = driver(
                    hostname=self.hostname,
                    username=self.username,
                    password=self.password
                )

            device.open()
            device_open = True
            self.facts = device.get_facts()

            # If "Kernel" in hostname, it's possibly a Nexus device using ios driver
            if "Kernel" in self.facts['hostname']:
                device.close()
                driver = get_network_driver('nxos_ssh')
                optional_args = {
                    'transport': 'ssh',
                    'port': 22
                }
                device = driver(
                    hostname=self.hostname,
                    username=self.username,
                    password=self.password,
                    optional_args=optional_args
                )
                device.open()
                device_open = True

            spanning_tree_output = device.cli(['show spanning-tree'])
            if 'root' in str(spanning_tree_output).lower():
                is_switch = True
            else:
                is_switch = False

            self.facts = device.get_facts()
            self.facts['is_switch'] = is_switch
            self.facts_ready.emit(self.facts)

            # Get interface info using custom parser
            custom = CustomDriver(device)
            interfaces, counters = custom.get_interfaces_custom()
            self.interfaces_ready.emit({"interfaces": interfaces, "counters": counters})
            print("-------------- parsed data ------------------")
            pprint(interfaces)

            # Get neighbor info using NAPALM
            lldp = device.get_lldp_neighbors()


            try:
                arp = device.get_arp_table()
            except Exception as e:
                print(f"Error retrieving arp: {e}")
                arp = {}
            self.neighbors_ready.emit({"lldp": lldp, "arp": arp})

            # Get route information
            try:
                # Get raw CLI output for complete routing table
                all_routes_output = device.cli(["show ip route"])
                # Try to get structured route data for default route
                default_route = {}
                try:
                    default_route = device.get_route_to("0.0.0.0/0")
                except:
                    pass  # Some platforms might not support this

                route_info = {
                    "structured_routes": default_route,
                    "raw_output": all_routes_output.get("show ip route", "")
                }
                self.routes_ready.emit(route_info)

            except Exception as e:
                print("Error getting routes:", str(e))
                self.routes_ready.emit({})

            device.close()

        except Exception as e:
            traceback.print_exc()
            self.error.emit(str(e))    # def run(self):
    #     try:
    #         # Initialize NAPALM driver
    #         self.driver = get_network_driver(self.driver)
    #         driver = self.driver
    #
    #         optional_args = {}
    #
    #         # Handle NXOS - switch to SSH if detected
    #         if 'nxos' in str(driver):
    #             self.driver = 'nxos_ssh'
    #             optional_args = {
    #                 'transport': 'ssh',
    #                 'port': 22
    #             }
    #             driver = get_network_driver(self.driver)
    #
    #         # Handle EOS - force SSH instead of pyeapi
    #         elif self.driver == 'eos':
    #             optional_args = {
    #                 'transport': 'ssh',
    #                 'use_eapi': False
    #             }
    #
    #         # Initialize device with optional arguments
    #         device = driver(
    #             hostname=self.hostname,
    #             username=self.username,
    #             password=self.password,
    #             optional_args=optional_args
    #         )
    #
    #         device.open()
    #         self.facts = device.get_facts()
    #
    #         # If "Kernel" in hostname, it's possibly a Nexus device using ios driver
    #         if "Kernel" in self.facts['hostname']:
    #             device.close()
    #             driver = get_network_driver('nxos_ssh')
    #             optional_args = {
    #                 'transport': 'ssh',
    #                 'port': 22
    #             }
    #             device = driver(
    #                 hostname=self.hostname,
    #                 username=self.username,
    #                 password=self.password,
    #                 optional_args=optional_args
    #             )
    #             device.open()
    #
    #         spanning_tree_output = device.cli(['show spanning-tree'])
    #         if 'root' in str(spanning_tree_output).lower():
    #             is_switch = True
    #         else:
    #             is_switch = False
    #
    #         self.facts = device.get_facts()
    #         self.facts['is_switch'] = is_switch
    #         self.facts_ready.emit(self.facts)
    #
    #         # Get interface info using custom parser
    #         custom = CustomDriver(device)
    #         interfaces, counters = custom.get_interfaces_custom()
    #         self.interfaces_ready.emit({"interfaces""": interfaces, "counters": counters})
    #         print("-------------- parsed data ------------------")
    #         pprint(interfaces)
    #         # Get neighbor info using NAPALM
    #         lldp = device.get_lldp_neighbors()
    #         arp = device.get_arp_table()
    #         self.neighbors_ready.emit({"lldp": lldp, "arp": arp})
    #
    #         # Get route information
    #         try:
    #             # Get raw CLI output for complete routing table
    #             all_routes_output = device.cli(["show ip route"])
    #             # Try to get structured route data for default route
    #             default_route = {}
    #             try:
    #                 default_route = device.get_route_to("0.0.0.0/0")
    #             except:
    #                 pass  # Some platforms might not support this
    #
    #             route_info = {
    #                 "structured_routes": default_route,
    #                 "raw_output": all_routes_output.get("show ip route", "")
    #             }
    #             self.routes_ready.emit(route_info)
    #
    #         except Exception as e:
    #             print("Error getting routes:", str(e))
    #             self.routes_ready.emit({})
    #
    #         device.close()
    #
    #     except Exception as e:
    #         traceback.print_exc()
    #         self.error.emit(str(e))