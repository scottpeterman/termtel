from pathlib import Path
import json
import logging
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal

from termtel.discovery.focused_network_map import create_focused_network_diagram

logger = logging.getLogger(__name__)


class NetworkMapper(QObject):
    """Handles network topology mapping and visualization"""

    map_ready = pyqtSignal(str)  # Emits path to generated map
    error = pyqtSignal(str)  # Emits error message

    def __init__(self, output_dir: str = "network_maps"):
        super().__init__()
        self.output_dir = output_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    def create_map(self, neighbor_data: str, start_node: str) -> Optional[str]:
        """
        Create network map from neighbor data

        Args:
            neighbor_data: CDP/LLDP neighbor output
            start_node: Name of the starting device

        Returns:
            Path to generated map file or None if failed
        """
        try:
            # Create temporary JSON file for neighbor data
            temp_json = Path(self.output_dir) / "temp_topology.json"
            topology_data = self._parse_neighbor_data(neighbor_data)

            with open(temp_json, 'w') as f:
                json.dump(topology_data, f, indent=2)

            # Generate the map
            map_file = create_focused_network_diagram(
                json_file=str(temp_json),
                output_dir=self.output_dir,
                map_name="network_topology",
                start_node=start_node,
                max_hops=2,  # TODO: Make configurable
                layout_algo="circular"
            )

            if map_file and Path(map_file).exists():
                self.map_ready.emit(map_file)
                return map_file
            else:
                self.error.emit("Failed to generate map file")
                return None

        except Exception as e:
            error_msg = f"Error creating network map: {str(e)}"
            logger.error(error_msg)
            self.error.emit(error_msg)
            return None

    def _parse_neighbor_data(self, neighbor_output: str) -> dict:
        """
        Parse CDP/LLDP neighbor output into topology format

        TODO: Implement proper parsing based on device type and output format
        For now, returns mock topology data
        """
        # Mock topology data structure
        return {
            "device1": {
                "peers": {
                    "device2": {
                        "connections": [
                            ["GigabitEthernet0/1", "GigabitEthernet0/2"]
                        ]
                    }
                }
            }
        }