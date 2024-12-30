import argparse
import json
import os
import re
import xml.sax.saxutils as saxutils

from N2G import drawio_diagram, yed_diagram
import networkx as nx
import matplotlib.pyplot as plt
from collections import deque
import logging

logger = logging.getLogger(__name__)

def create_standard_filename(map_name, start_node, max_hops, layout_type):
    """Create a standardized filename format for all map files."""
    sanitized_map = sanitize_filename(map_name)
    sanitized_node = sanitize_filename(start_node)
    return f"{sanitized_map}_focused_{sanitized_node}_{max_hops}hops_{layout_type}_nx.png"

def sanitize_topology_data(data):
    """Clean up topology data by removing ANSI sequences and fixing interface names."""
    cleaned_data = {}

    # Helper function to clean node names
    def clean_node_name(name):
        # Remove ANSI sequences
        clean = re.sub(r'\x1b[^m]*m', '', name)
        # Remove any leading/trailing whitespace
        clean = clean.strip()
        return clean

    # Helper function to clean interface names
    def clean_interface_name(name):
        return name.replace('Etherneternet', 'Ethernet')

    # Process each node
    for node, node_data in data.items():
        clean_node = clean_node_name(node)
        cleaned_data[clean_node] = {"peers": {}}

        # Process peers
        for peer, peer_data in node_data.get('peers', {}).items():
            clean_peer = clean_node_name(peer)
            cleaned_data[clean_node]['peers'][clean_peer] = {"connections": []}

            # Process connections
            for connection in peer_data.get('connections', []):
                if len(connection) == 2:
                    cleaned_connection = [
                        clean_interface_name(connection[0]),
                        clean_interface_name(connection[1])
                    ]
                    cleaned_data[clean_node]['peers'][clean_peer]['connections'].append(cleaned_connection)

    return cleaned_data

def get_nodes_within_hops(data, start_node, max_hops):
    """
    Get all nodes within specified number of hops from the start node.
    """
    if start_node not in data:
        raise ValueError(f"Start node '{start_node}' not found in network data")

    nodes_to_include = set()
    edges_to_include = set()
    distances = {start_node: 0}
    queue = deque([(start_node, 0)])

    while queue:
        current_node, current_distance = queue.popleft()

        if current_distance > max_hops:
            continue

        nodes_to_include.add(current_node)

        # Process peers of current node
        for peer_id, peer_info in data[current_node].get('peers', {}).items():
            # Add edge information
            for connection in peer_info.get('connections', []):
                local_port, remote_port = connection
                edge = (current_node, peer_id, local_port, remote_port)
                if peer_id in data:  # Only include edges to known nodes
                    edges_to_include.add(edge)

            # Process next hop if within limit
            if peer_id in data and peer_id not in distances:
                distances[peer_id] = current_distance + 1
                if current_distance + 1 <= max_hops:
                    queue.append((peer_id, current_distance + 1))

    return nodes_to_include, edges_to_include, distances


def create_networkx_graph(nodes_to_include, edges_to_include, distances, start_node):
    """Create a NetworkX graph from the filtered network data."""
    G = nx.Graph()

    # Add nodes with attributes
    for node in nodes_to_include:
        distance = distances.get(node, 0)
        G.add_node(node, distance=distance, is_start=(node == start_node))

    # Add edges with port information as attributes
    for source, target, local_port, remote_port in edges_to_include:
        if source in nodes_to_include and target in nodes_to_include:
            G.add_edge(source, target, local_port=local_port, remote_port=remote_port)

    return G


def sanitize_filename(input_string):
    """Strictly sanitize filename by removing all non-alphanumeric characters except underscore and hyphen."""
    # Remove ANSI escape sequences
    clean = re.sub(r'\x1b[^m]*m', '', input_string)
    # Keep only alphanumeric, underscore, and hyphen
    clean = re.sub(r'[^a-zA-Z0-9_-]', '', clean)
    return clean


def save_networkx_diagram(G, output_dir, map_name, start_node, max_hops, layout_type='circular'):
    """Create and save a NetworkX visualization optimized for dark mode."""
    # Sanitize filename components
    sanitized_map_name = sanitize_filename(map_name)
    sanitized_start_node = sanitize_filename(start_node)

    # Set dark background style
    plt.style.use('dark_background')
    plt.figure(figsize=(40, 40))

    # Get node positions based on layout type
    if layout_type == 'circular':
        pos = nx.circular_layout(G, scale=2.0)
    elif layout_type == 'shell':
        pos = create_shell_layout(G)
    else:
        pos = create_hierarchical_layout(G, start_node)

    # Define dark mode color scheme
    COLOR_SCHEME = {
        'start': '#00FF9F',  # Bright mint green for start node
        'hop1': '#4D4DFF',  # Bright blue for 1-hop nodes
        'hop2': '#FF4D4D',  # Bright red for 2-hop nodes
    }

    # Set dark background
    plt.gcf().set_facecolor('#1A1A1A')
    plt.gca().set_facecolor('#1A1A1A')

    # Draw edges with increased width
    nx.draw_networkx_edges(G, pos, width=2.0, edge_color='#FFFFFF', alpha=0.7)

    # Draw node rectangles
    draw_node_rectangles(G, pos, COLOR_SCHEME)

    # Add node and edge labels
    add_labels(G, pos)

    plt.axis('off')
    ax = plt.gca()
    ax.margins(0.2)

    # Generate a safe output filename
    output_file = os.path.join(output_dir, create_standard_filename(map_name, start_node, max_hops, layout_type))

    # Save with high quality settings
    plt.savefig(output_file, bbox_inches='tight', dpi=300, facecolor='#1A1A1A', pad_inches=0.2)
    plt.close()

    print(f"NetworkX diagram saved to: {output_file}")
    return output_file


def draw_node_rectangles(G, pos, COLOR_SCHEME):
    """Draw rectangular nodes with appropriate colors."""
    rect_width = 0.8  # Increased width
    rect_height = 0.2  # Increased height

    node_patches = []
    for node in G.nodes():
        x, y = pos[node]
        if G.nodes[node]['is_start']:
            color = COLOR_SCHEME['start']
        else:
            distance = G.nodes[node]['distance']
            color = COLOR_SCHEME['hop1'] if distance == 1 else COLOR_SCHEME['hop2']

        rect = plt.Rectangle(
            (x - rect_width / 2, y - rect_height / 2),
            rect_width, rect_height,
            facecolor=color,
            edgecolor='#FFFFFF',
            linewidth=3,  # Increased line width
            alpha=0.8,
            zorder=2
        )
        node_patches.append(rect)

    ax = plt.gca()
    for patch in node_patches:
        ax.add_patch(patch)


def add_labels(G, pos):
    """Add node and edge labels with improved visibility for dark mode."""
    # Add node labels with white text
    nx.draw_networkx_labels(
        G, pos,
        font_size=16,  # Increased font size
        font_weight='bold',
        font_color='#FFFFFF',
        bbox=dict(facecolor='none', edgecolor='none')
    )

    # Add edge labels for ports
    edge_labels = {
        (u, v): f"{d['local_port']}\n{d['remote_port']}"
        for u, v, d in G.edges(data=True)
    }
    nx.draw_networkx_edge_labels(
        G, pos,
        edge_labels,
        font_size=12,  # Increased font size
        font_color='#CCCCCC',
        bbox=dict(
            facecolor='#1A1A1A',
            edgecolor='none',
            alpha=0.7,
            pad=0.5
        ),
        label_pos=0.3
    )


def create_shell_layout(G):
    """Create a shell layout with nodes arranged in concentric circles."""
    shells = [[], [], []]  # [core, hop1, hop2]
    for node in G.nodes():
        if G.nodes[node]['is_start']:
            shells[0].append(node)
        else:
            distance = G.nodes[node]['distance']
            shells[distance].append(node)

    return nx.shell_layout(G, shells)


def create_hierarchical_layout(G, start_node):
    """Create a hierarchical layout with the start node at the top."""
    DG = nx.DiGraph(G)
    levels = {}
    for node in G.nodes():
        distance = G.nodes[node]['distance']
        if distance not in levels:
            levels[distance] = []
        levels[distance].append(node)

    pos = {}
    pos[start_node] = (0, 1.0)

    for level, nodes in levels.items():
        if level == 0:
            continue

        y = 1.0 - (level * 0.5)
        num_nodes = len(nodes)
        if num_nodes == 1:
            pos[nodes[0]] = (0, y)
        else:
            width = max(2.0, num_nodes * 0.5)
            start_x = -width / 2
            spacing = width / (num_nodes - 1)
            sorted_nodes = sorted(nodes, key=lambda n: sum(pos[neighbor][0]
                                                           for neighbor in DG.neighbors(n)
                                                           if neighbor in pos))
            for i, node in enumerate(sorted_nodes):
                x = start_x + (i * spacing)
                pos[node] = (x, y)

    return pos


def create_focused_network_diagram(json_file, output_dir, map_name, start_node, max_hops, layout_algo="circular"):
    """Generate focused network diagrams in multiple formats."""
    try:
        # Ensure the output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Load and sanitize JSON data
        with open(json_file, 'r') as file:
            raw_data = json.load(file)


        # Clean up the data
        data = sanitize_topology_data(raw_data)

        # Find the matching node in the cleaned data
        clean_start_node = None
        raw_start_node = re.sub(r'\x1b[^m]*m', '', start_node)

        # Try to find the node in the cleaned data
        for node in data.keys():
            if node.replace('narista-core-1', '') == raw_start_node.replace('narista-core-1', ''):
                clean_start_node = node
                break

        if not clean_start_node:
            print(f"Available nodes: {list(data.keys())}")
            raise ValueError(f"Start node '{start_node}' not found in network data")

        # Get filtered nodes and edges
        nodes_to_include, edges_to_include, distances = get_nodes_within_hops(data, clean_start_node, max_hops)

        # Create and save NetworkX diagram
        G = create_networkx_graph(nodes_to_include, edges_to_include, distances, clean_start_node)
        output_file = save_networkx_diagram(G, output_dir, map_name, clean_start_node, max_hops, layout_algo)

        # Create additional diagram formats
        drawio_filename = f"{sanitize_filename(map_name)}_focused_{sanitize_filename(clean_start_node)}_{max_hops}hops.drawio"
        graphml_filename = f"{sanitize_filename(map_name)}_focused_{sanitize_filename(clean_start_node)}_{max_hops}hops.graphml"

        # Rest of the function remains the same...

    except Exception as e:
        print(f"Error creating network map: {str(e)}")
        # Print debug information
        print(f"Raw start node: {start_node}")
        print(f"Cleaned start node: {clean_start_node if 'clean_start_node' in locals() else 'Not cleaned yet'}")
        if 'data' in locals():
            print(f"Available nodes in data: {list(data.keys())}")
        return None

def get_hop_color(distance, max_hops):
    """Generate a color based on hop distance."""
    ratio = distance / max_hops
    if ratio <= 0.5:
        # Green to Yellow
        r = int(255 * (2 * ratio))
        g = 255
        b = 0
    else:
        # Yellow to Red
        r = 255
        g = int(255 * (2 - 2 * ratio))
        b = 0
    return f'#{r:02x}{g:02x}{b:02x}'


def main():
    parser = argparse.ArgumentParser(description="Generate focused network diagrams from a JSON file.")
    parser.add_argument('-json', '--json-file', required=True, help='Path to the input JSON file')
    parser.add_argument('-o', '--output-dir', required=True, help='Directory to write output files')
    parser.add_argument('-n', '--map-name', required=True, help='Name for the generated map')
    parser.add_argument('-s', '--start-node', required=True, help='Starting node for focused diagram')
    parser.add_argument('-d', '--max-hops', type=int, required=True, help='Maximum number of hops from start node')
    parser.add_argument('-l', '--layout', default='circular', help='Layout algorithm to use (default: circular)')

    args = parser.parse_args()

    create_focused_network_diagram(
        json_file=args.json_file,
        output_dir=args.output_dir,
        map_name=args.map_name,
        start_node=args.start_node,
        max_hops=args.max_hops,
        layout_algo=args.layout
    )


if __name__ == "__main__":
    main()