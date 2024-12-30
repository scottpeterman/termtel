#!/usr/bin/env python3
import json
from pathlib import Path
from time import sleep
import re
from typing import Dict, Optional, Tuple
from termtel.ssh.pysshpass import ssh_client
from termtel.tfsm_fire import TextFSMAutoEngine as TextFSMParser
import logging


class DeviceFingerprinter:
    INITIAL_PROMPT = "#|>|\\$"

    PAGING_COMMANDS = {
        'cisco': ['terminal length 0', 'terminal width 511'],
        'asa': ['terminal pager 0'],
        'arista': ['terminal length 0', 'terminal width 32767'],
        'juniper': ['set cli screen-length 0', 'set cli screen-width 511'],
        'huawei': ['screen-length 0 temporary'],
        'hp': ['screen-length disable'],
        'paloalto': ['set cli pager off'],
        'fortinet': ['config system console', 'set output standard', 'end'],
        'dell': ['terminal length 0']
    }

    ERROR_PATTERNS = [
        r'% ?error',
        r'% ?invalid',
        r'% ?bad',
        r'% ?unknown',
        r'% ?incomplete',
        r'% ?unrecognized'
    ]

    def __init__(self, verbose: bool = False):
        BASE_DIR = Path(__file__)
        db_path = str(BASE_DIR.parent) + "/templates.db"
        self.parser = TextFSMParser(db_path)
        self.prompt = None
        self.client = None
        self.channel = None
        self.verbose = verbose

        log_level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def debug_output(self, message: str, output: Optional[str] = None):
        if self.verbose:
            self.logger.debug(message)
            if output:
                self.logger.debug(f"Raw output:\n{output}")

    def read_channel_output(self, channel, timeout: int = 1) -> str:
        """Helper method to read channel output"""
        output = ""
        sleep(timeout)  # Wait for output to accumulate
        while channel.recv_ready():
            chunk = channel.recv(4096).decode('utf-8')
            output += chunk
        return output

    def phase1_detect_prompt(self, channel) -> Optional[str]:
        """Phase 1: Initial Prompt Detection"""
        self.logger.info("Phase 1: Detecting prompt...")

        try:
            self.debug_output("Sending newline to detect prompt")
            channel.send("\n")

            output = self.read_channel_output(channel)
            self.debug_output("Received output", output)

            lines = [l.strip() for l in output.split('\n') if l.strip()]
            for line in reversed(lines):
                if re.search(f".*({self.INITIAL_PROMPT})\\s*$", line):
                    detected_prompt = line.strip()
                    self.logger.info(f"Detected prompt: {detected_prompt}")
                    return detected_prompt

            self.logger.error("No prompt detected in output")
            return None

        except Exception as e:
            self.logger.error(f"Error in prompt detection: {str(e)}")
            raise

    def phase2_disable_paging(self, channel, prompt: str) -> Tuple[Optional[str], list]:
        """Phase 2: Paging Disable Loop with improved vendor detection"""
        self.logger.info("Phase 2: Disabling paging...")

        successful_vendors = {}  # Track all successful vendors

        try:
            for vendor, commands in self.PAGING_COMMANDS.items():
                self.logger.info(f"Trying {vendor} paging commands")
                vendor_success = True
                successful_commands = []

                for cmd in commands:
                    try:
                        self.debug_output(f"Sending command: {cmd}")
                        channel.send(cmd + "\n")
                        output = self.read_channel_output(channel)
                        self.debug_output(f"Command output for {cmd}", output)

                        if output and not any(re.search(pattern, output, re.IGNORECASE)
                                              for pattern in self.ERROR_PATTERNS):
                            self.logger.info(f"Successfully executed {vendor} command: {cmd}")
                            successful_commands.append((vendor, cmd))
                        else:
                            self.debug_output(f"Command failed or produced errors: {cmd}")
                            vendor_success = False
                            break

                    except Exception as e:
                        self.logger.error(f"Error with {vendor} command {cmd}: {str(e)}")
                        vendor_success = False
                        break

                if vendor_success and successful_commands:
                    successful_vendors[vendor] = successful_commands

            # If multiple vendors worked, use additional heuristics to determine the most likely one
            if successful_vendors:
                # Check prompt for vendor hints
                prompt_lower = prompt.lower()
                for vendor in successful_vendors.keys():
                    if vendor.lower() in prompt_lower:
                        self.logger.info(f"Selected {vendor} based on prompt match")
                        return vendor, successful_vendors[vendor]

                # If no prompt match, prefer more specific vendors over generic ones
                vendor_priority = ['arista', 'juniper', 'huawei', 'paloalto', 'fortinet', 'asa', 'cisco']
                for preferred_vendor in vendor_priority:
                    if preferred_vendor in successful_vendors:
                        self.logger.info(f"Selected {preferred_vendor} based on vendor priority")
                        return preferred_vendor, successful_vendors[preferred_vendor]

            self.logger.warning("No vendor paging commands were successful")
            return None, []

        except Exception as e:
            self.logger.error(f"Error in paging disable phase: {str(e)}")
            raise
    def phase3_get_version(self, channel, prompt: str) -> Dict:
        """Phase 3: Version Command Execution"""
        self.logger.info("Phase 3: Getting version information...")

        try:
            self.debug_output("Sending 'show version' command")
            channel.send("show version\n")

            output = self.read_channel_output(channel, timeout=2)
            self.debug_output("Show version output", output)

            if not output:
                self.logger.error("No output received from version command")
                return {"error": "Failed to get version information"}

            # Intelligent template selection based on output content
            template_hint = None
            if 'cisco' in output and 'IOS' in output:
                template_hint = 'cisco_ios_show_version'
                self.logger.info(f"Detected Cisco IOS device, using template: {template_hint}")
            if 'cisco' in output and 'Nexus' in output:
                template_hint = 'cisco_nxos_show_version'
                self.logger.info(f"Detected Cisco NXOS device, using template: {template_hint}")
            if 'arista' in output and 'EOS' in output:
                template_hint = 'arista_eos_show_version'
                self.logger.info(f"Detected Arista EOS device, using template: {template_hint}")
            if 'JUNOS' in output:
                template_hint = 'juniper_junos_show_version'
                self.logger.info(f"Detected Juniper Junos device, using template: {template_hint}")

            best_template, parsed_data, score = self.parser.find_best_template(output, filter_string=template_hint)

            if not best_template or not parsed_data:
                self.logger.error("Failed to find matching template or parse version information")
                return {"error": "Failed to parse version information"}

            self.debug_output(f"Best matching template: {best_template} with score {score}")
            self.debug_output("Parsed version data", str(parsed_data))

            return {
                "success": True,
                "parsed_data": parsed_data,
                "template": best_template,
                "score": score
            }

        except Exception as e:
            self.logger.error(f"Error in version detection: {str(e)}")
            return {"error": f"Error getting version info: {str(e)}"}

    def fingerprint_device(self, host: str, username: str, password: str, timeout: int = 30) -> Dict:
        """Main fingerprinting process"""
        self.logger.info(f"Starting device fingerprinting for host: {host}")
        channel = None

        try:
            self.debug_output(f"Establishing SSH connection to {host}")
            client = ssh_client(
                host=host,
                user=username,
                password=password,
                cmds="",
                invoke_shell=True,
                prompt=self.INITIAL_PROMPT,
                prompt_count=1,
                timeout=timeout,
                disable_auto_add_policy=False,
                look_for_keys=False,
                inter_command_time=1,
                connect_only=True
            )

            if not client:
                self.logger.error("Failed to establish SSH connection")
                return {"error": "Failed to establish SSH connection"}

            channel = client.invoke_shell()
            sleep(2)  # Wait for banner

            prompt = self.phase1_detect_prompt(channel)
            if not prompt:
                return {"error": "Failed to detect prompt"}

            vendor, paging_commands = self.phase2_disable_paging(channel, prompt)
            if not vendor:
                self.logger.warning("Could not identify vendor through paging commands")

            version_result = self.phase3_get_version(channel, prompt)
            if not version_result.get("success"):
                return {"error": version_result.get("error", "Unknown error in version detection")}

            # Structure the results consistently
            return {
                "success": True,
                "device_info": {
                    "vendor": vendor,
                    "paging_commands": paging_commands,
                    "detected_prompt": prompt,
                    "parsed_data": version_result["parsed_data"],
                    "template": version_result["template"],
                    "score": version_result["score"]
                }
            }

        except Exception as e:
            self.logger.error(f"Fingerprinting failed: {str(e)}")
            return {"error": f"Fingerprinting failed: {str(e)}"}

        finally:
            try:
                if channel:
                    channel.close()
                    self.debug_output("SSH channel closed")
                if client:
                    client.close()
                    self.debug_output("SSH client closed")
            except Exception as e:
                self.logger.error(f"Error closing SSH connections: {str(e)}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Network Device Fingerprinting Tool')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    parser.add_argument('--host', default="172.16.101.21", help='Target host')
    parser.add_argument('--username', default="cisco", help='SSH username')
    parser.add_argument('--password', default="cisco", help='SSH password')
    parser.add_argument('--timeout', type=int, default=30, help='Connection timeout in seconds')

    args = parser.parse_args()

    fingerprinter = DeviceFingerprinter(verbose=args.verbose)
    result = fingerprinter.fingerprint_device(
        host=args.host,
        username=args.username,
        password=args.password,
        timeout=args.timeout
    )
    if result.get("success"):
        print("\nDevice Fingerprinting Results:")
        print(f"Vendor: {result['device_info']['vendor']}")
        print(f"Prompt: {result['device_info']['detected_prompt']}")
        print(f"Paging Commands: {result['device_info']['paging_commands']}")
        print(f"Template Used: {result['device_info']['template']}")
        print(f"Template Score: {result['device_info']['score']:.2f}")
        print("\nParsed Version Data:")
        print(json.dumps(result['device_info']['parsed_data'], indent=2))
    else:
        print("\nError:", result.get("error"))

if __name__ == "__main__":
    main()