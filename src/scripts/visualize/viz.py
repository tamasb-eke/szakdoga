import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict
import numpy as np
import re # For GML parsing if needed
from scipy.spatial import distance
import math

# Assume parse_gml_simple and count_edge_frequencies functions are defined as before.
# If not, I can re-paste them.

def parse_gml_simple(gml_file_path):
    """Simplified GML parser for 'name' attribute in node blocks."""
    nodes = set()
    try:
        with open(gml_file_path, 'r') as f:
            content = f.read()
        node_names = re.findall(r'node\s*\[(?:.*?\s)*?name\s+"([a-zA-Z]{3})"', content, re.DOTALL)
        nodes = set(node_names)
    except Exception as e:
        print(f"Error parsing GML: {e}")
    if not nodes:
        print(f"Warning: No nodes extracted from GML file: {gml_file_path}")
    return nodes

def count_edge_frequencies(txt_file_path):
    """Counts frequencies of adjacent word pairs from a TXT file."""
    edge_counts = defaultdict(int)
    try:
        with open(txt_file_path, 'r') as f:
            for line in f:
                words = [word.lower() for word in line.strip().split('-') if word]
                if len(words) < 2:
                    continue
                for i in range(len(words) - 1):
                    pair = tuple(sorted((words[i], words[i+1])))
                    edge_counts[pair] += 1
    except Exception as e:
        print(f"Error processing TXT file: {e}")
    return edge_counts


def visualize_word_graph(gml_nodes, edge_frequencies, output_filename="word_graph.png", min_edge_frequency=0):
    """
    Visualizes the word graph with publication-quality readability.
    - Only nodes with edges are shown.
    - Node names are displayed with minimal overlaps.
    - Edges are clearly visible beneath the node labels.
    - Increased font sizes and DPI for clarity.
    - Advanced node positioning algorithm to prevent overlapping.
    - Added min_edge_frequency parameter to filter edges based on their frequency.
    
    Parameters:
    -----------
    gml_nodes : set
        Set of nodes extracted from the GML file
    edge_frequencies : dict
        Dictionary mapping edge tuples to their frequencies
    output_filename : str, optional
        Name of the output image file
    min_edge_frequency : int, optional
        Minimum frequency threshold for edges to be included in the visualization
        Default is 0 (include all edges)
    """

    G_full = nx.Graph()
    for node in gml_nodes:
        G_full.add_node(node)

    # Filter edges based on minimum frequency
    filtered_edges = {(u, v): weight for (u, v), weight in edge_frequencies.items() 
                     if weight >= min_edge_frequency}
    
    for (u, v), weight in filtered_edges.items():
        if G_full.has_node(u) and G_full.has_node(v):
            G_full.add_edge(u, v, weight=weight)
        else:
            print(f"Warning: Edge ({u},{v}) contains word(s) not found in GML node list. Skipping this edge.")

    nodes_with_edges = [node for node, degree in G_full.degree() if degree > 0]

    if not nodes_with_edges:
        print(f"No nodes have any edges based on the TXT file (with min_edge_frequency={min_edge_frequency}). Cannot generate visualization.")
        plt.figure(figsize=(12, 12))
        plt.text(0.5, 0.5, f"No data to visualize:\nNo edges with frequency ≥ {min_edge_frequency}.",
                 horizontalalignment='center', verticalalignment='center',
                 fontsize=18, color='red', multialignment='center')
        plt.axis('off')
        plt.tight_layout()
        try:
            plt.savefig(output_filename, dpi=300)
            print(f"Empty graph image saved to {output_filename}")
        except Exception as e:
            print(f"Error saving empty graph image: {e}")
        return

    G_display = G_full.subgraph(nodes_with_edges).copy()
    
    # --- Advanced Layout ---
    # Use a stronger repulsive force and many iterations for better node spacing
    pos_initial = nx.spring_layout(G_display, k=2.0, iterations=300, seed=42)
    
    # Rescale layout to a larger area to reduce overlaps
    pos_array = np.array(list(pos_initial.values()))
    pos_array_rescaled = nx.rescale_layout(pos_array, scale=2.0)
    pos = {node: pos_array_rescaled[i] for i, node in enumerate(pos_initial.keys())}
    
    # --- Apply force-directed adjustments to reduce overlaps ---
    node_radius = 0.065
    adjustment_iterations = 50
    
    # Adjust positions to reduce overlaps
    for _ in range(adjustment_iterations):
        adjustments = {node: np.array([0.0, 0.0]) for node in pos}
        
        # Calculate repulsive forces between nodes that are too close
        nodes = list(pos.keys())
        for i, node1 in enumerate(nodes):
            for node2 in nodes[i+1:]:
                dx = pos[node2][0] - pos[node1][0]
                dy = pos[node2][1] - pos[node1][1]
                dist = math.sqrt(dx*dx + dy*dy)
                
                # If nodes are too close, push them apart more aggressively
                min_dist = 2.5 * node_radius
                if dist < min_dist:
                    # Calculate stronger repulsion force
                    force = min((min_dist - dist) / min_dist * 0.15, 0.08)
                    
                    # Direction of force
                    if dist > 0:
                        fx = dx / dist * force
                        fy = dy / dist * force
                    else:  # Avoid division by zero
                        angle = np.random.uniform(0, 2*np.pi)
                        fx = np.cos(angle) * force
                        fy = np.sin(angle) * force
                    
                    # Apply force (repel both nodes in opposite directions)
                    adjustments[node2][0] += fx
                    adjustments[node2][1] += fy
                    adjustments[node1][0] -= fx
                    adjustments[node1][1] -= fy
        
        # Apply adjustments
        for node, adjustment in adjustments.items():
            pos[node] = pos[node] + adjustment
    
    # --- Node Styling ---
    node_sizes = [100 for _ in G_display.nodes()]
    
    # --- Edge Styling ---
    # Create list to store edge properties
    edge_properties = []
    
    for u, v, data in G_display.edges(data=True):
        weight = data.get('weight', 0)
        
        # Define edge properties based on weight
        if weight > 50: 
            color = 'red'
            width = 9.0
            alpha = 0.9
        elif weight > 30: 
            color = (1.0, 0.27, 0)
            width = 8.0
            alpha = 0.9
        elif weight > 10: 
            color = (1.0, 0.55, 0)
            width = 7.0
            alpha = 0.85
        elif weight > 7: 
            color = 'orange'
            width = 6.0
            alpha = 0.85
        elif weight > 4: 
            color = 'green'
            width = 5.0
            alpha = 0.8
        elif weight > 2: 
            color = 'blue'
            width = 4.0
            alpha = 0.8
        else:  # weight > 0
            color = 'lightblue'  # Changed to light-blue for 1-2 uses
            width = 3.0
            alpha = 0.8
        
        # Store the edge with its properties
        edge_properties.append({
            'nodes': (u, v),
            'color': color,
            'width': width,
            'alpha': alpha
        })

    # --- Drawing ---
    plt.figure(figsize=(30, 30))
    
    # 1. Draw Edges FIRST (under the nodes)
    for edge_prop in edge_properties:
        u, v = edge_prop['nodes']
        edge_line = plt.plot([pos[u][0], pos[v][0]], [pos[u][1], pos[v][1]], 
                 color=edge_prop['color'], linewidth=edge_prop['width'], 
                 alpha=edge_prop['alpha'], solid_capstyle='round')
        edge_line[0].set_zorder(1)
    
    # 2. Draw Nodes (small visible nodes)
    node_collection = nx.draw_networkx_nodes(G_display, pos, node_size=node_sizes, node_color='black', 
                          alpha=0.7)
    if node_collection is not None:
        node_collection.set_zorder(2)
    
    # 3. Draw semi-transparent node labels with smaller, translucent backgrounds
    for node, (x, y) in pos.items():
        plt.text(x, y, node, fontsize=18, ha='center', va='center', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.85, 
                         edgecolor='lightgray'), zorder=3)
    
    # --- Legend and Final Touches ---
    legend_elements = []
    
    # Only add legend entries for edge frequencies that are actually displayed
    if min_edge_frequency <= 50:
        legend_elements.append(plt.Line2D([0], [0], color='red', lw=9, label='> 50 uses'))
    if min_edge_frequency <= 30:
        legend_elements.append(plt.Line2D([0], [0], color=(1.0, 0.27, 0), lw=8, label='> 30 uses'))
    if min_edge_frequency <= 10:
        legend_elements.append(plt.Line2D([0], [0], color=(1.0, 0.55, 0), lw=7, label='> 10 uses'))
    if min_edge_frequency <= 7:
        legend_elements.append(plt.Line2D([0], [0], color='orange', lw=6, label='> 7 uses'))
    if min_edge_frequency <= 4:
        legend_elements.append(plt.Line2D([0], [0], color='green', lw=5, label='> 4 uses'))
    if min_edge_frequency <= 2:
        legend_elements.append(plt.Line2D([0], [0], color='blue', lw=4, label='> 2 uses'))
    if min_edge_frequency <= 1:
        legend_elements.append(plt.Line2D([0], [0], color='lightblue', lw=3, label='1-2 uses'))

    plt.legend(handles=legend_elements, loc='upper right',
               title="Élek gyakorisága", fontsize=30, title_fontsize=34, framealpha=0.95)

    threshold_info = f" (min. gyakoriság: {min_edge_frequency})" if min_edge_frequency > 0 else ""
    plt.title(f"Leggyakrabban használt útvonalak a Gráfban{threshold_info}", fontsize=50, fontweight='bold')
    plt.axis('off')
    plt.tight_layout()
    
    # Add a subtle grid to better distinguish node positions
    plt.grid(False)

    try:
        plt.savefig(output_filename, dpi=300, bbox_inches='tight')  # Higher DPI for even sharper text
        print(f"Graph saved to {output_filename} (Publication Quality, min_edge_frequency={min_edge_frequency})")
    except Exception as e:
        print(f"Error saving graph image: {e}")

# --- Main execution --- (Example, replace with your file paths)
if __name__ == "__main__":
    gml_filepath = "/home/beket/snap/word_morph_network.gml"      # <--- PUT YOUR GML FILE PATH HERE
    txt_filepath = "/home/beket/snap/valami.txt"  # <--- PUT YOUR TXT FILE PATH HERE
    min_frequency = 3       # <--- SET MINIMUM EDGE FREQUENCY (default: 0 = show all edges)
                            # Set to 3 to show only edges used 3 or more times
    
    output_image_file = f"/mnt/c/Users/beket/Documents/Egyetem/6.felev/onlab/python_chatgpt1000_min{min_frequency}.png"
    

    # 1. Parse GML
    nodes_from_gml = parse_gml_simple(gml_filepath)
    if not nodes_from_gml:
        print("Could not parse GML file. Exiting.")
    else:
        print(f"Successfully parsed {len(nodes_from_gml)} nodes from GML.")
        # 2. Process TXT
        frequencies = count_edge_frequencies(txt_filepath)
        if not frequencies:
            print("No edge frequencies were counted from TXT file or file was empty/invalid.")
        # Allow visualization even if frequencies are empty, visualize_word_graph handles it
        # 3. Visualize
        visualize_word_graph(nodes_from_gml, frequencies, output_image_file, min_frequency)

