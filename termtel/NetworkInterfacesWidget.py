from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QTreeWidget, QTreeWidgetItem, QFrame, QSplitter, QMenu)
from PyQt6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
import time
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional


@dataclass
class InterfaceData:
    name: str
    is_up: bool
    speed: int  # in Mbps
    utilization: float
    rx_rate: float  # in bps
    tx_rate: float  # in bps


class InterfaceGraphWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.setup_ui()
        self.interface_history = {}
        self.current_interface = None
        self.history_length = 30
        self.parent = parent

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.chart = QChart()
        self.chart.setTitle("Interface Utilization")
        self.chart_view = QChartView(self.chart)

        self.axis_x = QValueAxis()
        self.axis_x.setTitleText("Time (s)")
        self.axis_x.setRange(0, 300)

        self.axis_y = QValueAxis()
        self.axis_y.setTitleText("Utilization (%)")
        self.axis_y.setRange(0, 100)

        self.chart.addAxis(self.axis_x, Qt.AlignmentFlag.AlignBottom)
        self.chart.addAxis(self.axis_y, Qt.AlignmentFlag.AlignLeft)

        layout.addWidget(self.chart_view)

    def update_interface_data(self, interface: str, utilization: float):
        print(f"Graph received update for {interface}: {utilization:.2f}%")
        current_time = time.time()

        if interface not in self.interface_history:
            self.interface_history[interface] = []

        history = self.interface_history[interface]
        history.append((current_time, utilization))

        if len(history) > self.history_length:
            history.pop(0)

        if interface == self.current_interface:
            self.update_graph()

    def set_current_interface(self, interface: str):
        print(f"Setting current interface to: {interface}")
        self.current_interface = interface
        self.update_graph()

    def update_graph(self):
        if not self.current_interface:
            return

        print(f"Updating graph for {self.current_interface}")
        self.chart.removeAllSeries()
        series = QLineSeries()

        history = self.interface_history.get(self.current_interface, [])
        if not history:
            print(f"No history for {self.current_interface}")
            return

        print(f"History points: {len(history)}")
        start_time = history[0][0]
        for timestamp, utilization in history:
            print(f"Point: {timestamp - start_time:.1f}s, {utilization:.2f}%")
            series.append(timestamp - start_time, utilization)

        self.chart.addSeries(series)
        series.attachAxis(self.axis_x)
        series.attachAxis(self.axis_y)
        self.chart.setTitle(f"{self.current_interface} Utilization History")


class InterfaceTreeWidget(QTreeWidget):
    interface_selected = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setHeaderLabels(["Interface", "Status", "Utilization", "Speed"])
        self.setColumnWidth(0, 200)
        self.setColumnWidth(1, 100)
        self.setColumnWidth(2, 120)
        self.setSortingEnabled(True)
        self.itemSelectionChanged.connect(self.on_selection_changed)

    def on_selection_changed(self):
        items = self.selectedItems()
        if items:
            print(f"Selected interface: {items[0].text(0)}")
            self.interface_selected.emit(items[0].text(0))

    def update_interface(self, data: InterfaceData):
        items = self.findItems(data.name, Qt.MatchFlag.MatchExactly, 0)

        speed_bits = data.speed * 1_000_000  # Convert Mbps to bps
        utilization = ((data.rx_rate + data.tx_rate) / speed_bits * 100) if data.speed else 0
        print(f"Tree update for {data.name}: {utilization:.2f}% ({data.rx_rate:,} + {data.tx_rate:,}) / {speed_bits:,}")

        if not items:
            item = QTreeWidgetItem([
                data.name,
                'Up' if data.is_up else 'Down',
                f"{utilization:.1f}%",
                f"{data.speed} Mbps" if data.speed else 'N/A'
            ])
        else:
            item = items[0]
            item.setText(1, 'Up' if data.is_up else 'Down')
            item.setText(2, f"{utilization:.1f}%")
            item.setText(3, f"{data.speed} Mbps" if data.speed else 'N/A')

        item.setBackground(1, Qt.GlobalColor.green if data.is_up else Qt.GlobalColor.red)

        if not items:
            self.addTopLevelItem(item)


class NetworkInterfacesWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.tree = InterfaceTreeWidget()
        self.tree.interface_selected.connect(self.on_interface_selected)
        self.graph = InterfaceGraphWidget()
        splitter.addWidget(self.tree)
        splitter.addWidget(self.graph)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter)

    def update_interfaces(self, data: Dict):
        print("\nUpdating interfaces with new data:")
        interfaces = data['interfaces']
        counters = data['counters']

        for name, details in interfaces.items():
            if name in counters:
                counter = counters[name]
                in_rate = counter.get('rx_rate', 0)
                out_rate = counter.get('tx_rate', 0)
                speed = details.get('speed', 0)

                print(f"\nInterface {name}:")
                print(f"  in_rate: {in_rate:,} bps")
                print(f"  out_rate: {out_rate:,} bps")
                print(f"  speed: {speed:,} Mbps")

                speed_bits = speed * 1_000_000  # Convert Mbps to bps
                utilization = ((in_rate + out_rate) / speed_bits * 100) if speed else 0
                print(f"  calculated utilization: {utilization:.2f}%")

                interface_data = InterfaceData(
                    name=name,
                    is_up=details.get('is_up', False),
                    speed=speed,
                    utilization=utilization,
                    rx_rate=in_rate,
                    tx_rate=out_rate
                )

                self.update_interface(interface_data)

    def update_interface(self, data: InterfaceData):
        speed_bits = data.speed * 1_000_000
        utilization = ((data.rx_rate + data.tx_rate) / speed_bits * 100) if data.speed else 0
        print(f"Updating interface {data.name} with {utilization:.2f}%")
        self.tree.update_interface(data)
        self.graph.update_interface_data(data.name, utilization)

    def on_interface_selected(self, interface: str):
        print(f"Interface selected: {interface}")
        self.graph.set_current_interface(interface)

    def clear(self):
        self.tree.clear()
        self.graph.interface_history.clear()
        self.graph.current_interface = None
        self.graph.update_graph()