import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict
import numpy as np
import re
from typing import Set, Dict, Any
from classes.db_manager import get_database
from scripts.safe_operation import safe_operation
from scripts.logger.logger import get_logger
from pathlib import Path
from scripts.basic_tools import (
    GMPL_PATH,
    SAVE_PICTURE_PATH
)

EDGE_STYLE_CONFIG = [
    {'threshold': 50, 'label': '> 50 használat', 'style': {'color': 'red', 'linewidth': 18.0, 'alpha': 0.9}},
    {'threshold': 30, 'label': '> 30 használat', 'style': {'color': (1.0, 0.27, 0), 'linewidth': 14.0, 'alpha': 0.9}},
    {'threshold': 10, 'label': '> 10 használat', 'style': {'color': (1.0, 0.55, 0), 'linewidth': 10.0, 'alpha': 0.85}},
    {'threshold': 7, 'label': '> 7 használat', 'style': {'color': 'orange', 'linewidth': 8.0, 'alpha': 0.85}},
    {'threshold': 4, 'label': '> 4 használat', 'style': {'color': 'green', 'linewidth': 5.0, 'alpha': 0.8}},
    {'threshold': 2, 'label': '> 2 használat', 'style': {'color': 'blue', 'linewidth': 3.0, 'alpha': 0.8}},
    {'threshold': 0, 'label': '1-2 használat', 'style': {'color': 'lightblue', 'linewidth': 1.0, 'alpha': 0.8}}
]

NODE_LABEL_STYLE = {
    'fontsize': 40,   # Legyen hatalmas!
    'fontweight': 'bold',
    'ha': 'center',
    'va': 'center',
    # Keret eltüntetése (edgecolor='none')
    'bbox': dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8, edgecolor='none'),
    'zorder': 3
}





@safe_operation()
def parse_gml_simple(gml_file_path):
    """Simplified GML parser for 'name' attribute in node blocks. That is just the nodes of the graph"""

    with open(gml_file_path, 'r') as f:
        content = f.read()
    node_names = re.findall(r'node\s*\[(?:.*?\s)*?name\s+"([a-zA-Z]{3})"', content, re.DOTALL)
    return set(node_names)

    
@safe_operation()
def count_edge_frequencies(run_id:int) -> defaultdict:
    """Counts frequencies of adjacent word pairs based on the answers from database"""
    
    db = get_database()
    edge_counts = defaultdict(int)
    answers = db.answer.get_all(run_id=run_id, only_correct=True)
    chains = [r["chain"] for r in answers]

    for line in chains:
        if run_id < 423:
            words = [word.lower() for word in line.strip().split(' ') if word]
        else:
            words = [word.lower() for word in line.strip().split('-') if word]
        if len(words) < 2:
            continue
        for i in range(len(words) - 1):
            pair = tuple(sorted((words[i], words[i+1])))
            edge_counts[pair] += 1

    return edge_counts


def get_edge_style(weight: int) -> Dict[str, Any]:
    """Retrieves the style dictionary for a given edge weight from the config."""

    for config in EDGE_STYLE_CONFIG:
        if weight > config['threshold']:
            return config['style']
    return EDGE_STYLE_CONFIG[-1]['style'] # Fallback for weights of 1-2


def build_display_graph(gml_nodes: Set, edge_frequencies: defaultdict, min_edge_frequency: int) -> nx.Graph | None:
    """Builds the graph from nodes and edges, filtering by frequency."""

    logger = get_logger()
    G_full = nx.Graph()
    G_full.add_nodes_from(gml_nodes)

    for (u, v), weight in edge_frequencies.items():
        if weight >= min_edge_frequency:

            if u in G_full and v in G_full:
                G_full.add_edge(u, v, weight=weight)
            else:
                logger.warning(f"Warning: Edge ({u},{v}) contains word(s) not found in GML node list. Skipping...")


    nodes_with_edges = [node for node, degree in G_full.degree() if degree > 0]    
    if not nodes_with_edges:
        logger.warning("No nodes found -> empty graph")
        return None
    return G_full.subgraph(nodes_with_edges).copy()


def calculate_optimized_layout(G: nx.Graph) -> Dict[str, np.ndarray]:
    """Calculates node positions intended for a very sparse layout with large labels."""

    node_count = len(G.nodes())
    if node_count == 0:
        return {}

    # 1. LÉPÉS: Alap rugós modell, de nagyon erős "rúgókkal" (k érték)
    # Minél több node van, annál nagyobb tér kell.
    # A k=35.0 egy nagyon nagy szám, ez tolja szét őket.
    k_val = 45.0 / np.sqrt(node_count)
    
    # Több iteráció (500) a stabilitásért
    pos = nx.spring_layout(G, k=k_val, iterations=500, seed=42, weight='weight')
    
    # 2. LÉPÉS: Skálázás (Rescaling)
    # Ez nyújtja ki a végleges koordinátákat a hatalmas 30x30-as vászonra.
    # scale=35.0 nagyon nagy szóródást jelent.
    pos_array = np.array(list(pos.values()))
    pos_array_rescaled = nx.rescale_layout(pos_array, scale=35.0)
    pos = {node: pos_array_rescaled[i] for i, node in enumerate(pos.keys())}

    # 3. LÉPÉS: Finomhangoló taszítás
    # Mivel a címkék most óriásiak, a minimális biztonsági távolságot (min_dist)
    # is nagyra kell venni.
    min_dist = 5.0 # Ha még mindig fedik egymást a nagy betűk, növeld ezt (pl. 6.0 vagy 7.0)
    nodes = list(pos.keys())

    for _ in range(50): # 50 iteráció elég finomhangolásra
        adjustments = {node: np.zeros(2) for node in nodes}
        for i, node1 in enumerate(nodes):
            for node2 in nodes[i+1:]:
                delta = pos[node2] - pos[node1]
                dist = np.linalg.norm(delta)
                
                if 0 < dist < min_dist:
                    # Finom taszító erő
                    force = (min_dist - dist) / min_dist * 0.2
                    direction = delta / dist
                    adjustments[node2] += direction * force
                    adjustments[node1] -= direction * force

        for node, adj in adjustments.items():
            pos[node] += adj
            
    return pos

def draw_graph_elements(ax: plt.Axes, G: nx.Graph, pos: Dict[str, np.ndarray]):
    """Draws graph with tiny nodes and huge labels exactly on node positions."""

    # 1. Élek rajzolása
    for u, v, data in G.edges(data=True):
        # Lekérjük a stílust és készítünk egy MÁSOLATOT
        style = get_edge_style(data.get('weight', 0)).copy()
        
        # Átlátszóság beállítása
        style['alpha'] = 0.6 
        
        ax.plot([pos[u][0], pos[v][0]], [pos[u][1], pos[v][1]], 
                solid_capstyle='round', zorder=1, **style)

    # 2. Node-ok rajzolása - JAVÍTVA
    # Kivettem a 'zorder=2' paramétert, mert a te verziód nem szereti.
    # Mivel node_size=1 (apró), nem baj, ha nincs explicit rétegrendje,
    # úgyis a hatalmas címkék (zorder=3) és az élek (zorder=1) dominálnak.
    nodes = nx.draw_networkx_nodes(G, pos, ax=ax, node_size=1, node_color='black', alpha=0.3)
    
    # Ha mindenképp biztosra akarunk menni a rétegrenddel, így állíthatjuk be utólag:
    if nodes:
        nodes.set_zorder(2)

    # 3. Címkék rajzolása
    for node, (x, y) in pos.items():
        ax.text(x, y, node, **NODE_LABEL_STYLE)

def setup_plot_aesthetics(ax: plt.Axes, min_edge_frequency: int):
    """Configures the plot's legend outside the graph area."""

    legend_elements = [
        plt.Line2D([0], [0], label=config['label'], **config['style'])
        for config in EDGE_STYLE_CONFIG if min_edge_frequency <= config['threshold']
    ]

    # bbox_to_anchor=(1, 1): A jobb felső sarok legyen a referencia, de a ploton KÍVÜL
    ax.legend(handles=legend_elements, 
              loc='upper left', 
              bbox_to_anchor=(1.0, 1.0), # Ez teszi ki a jobb szélre
              title="Élek gyakorisága", 
              fontsize=40, 
              title_fontsize=44, 
              framealpha=1.0) # Teljesen átlátszatlan háttér
    
    threshold_info = f" Minimum él gyakoriság: {min_edge_frequency}" if min_edge_frequency > 0 else ""
    ax.set_title(f"{threshold_info}", fontsize=50, fontweight='bold', y=1.02)
    #ax.set_title(f"Leggyakrabban használt útvonalak a Gráfban{threshold_info}", fontsize=50, fontweight='bold', y=1.02)
    ax.axis('off')

@safe_operation(default_return=None)
def save_empty_graph_image(output_path: Path, min_edge_frequency: int):
    """Creates and saves a placeholder image when there's no data to visualize."""
    
    fig, ax = plt.subplots(figsize=(12, 12))
    text = f"No data to visualize:\nNo edges with frequency ≥ {min_edge_frequency}."
    ax.text(0.5, 0.5, text, ha='center', va='center', fontsize=18, color='red')
    ax.axis('off')
    fig.tight_layout()
    
    try:
        fig.savefig(output_path, dpi=300)
        print(f"Empty graph image saved to {output_path}")
    except Exception as e:
        print(f"Error saving empty graph image: {e}")
    plt.close(fig)


@safe_operation(default_return=None)
def visualize_word_graph(gml_nodes: Set, edge_frequencies: defaultdict, output_path: Path = Path("word_graph.png"), min_edge_frequency: int = 0):
    """
    This function generates a word graph visualization with a non-overlapping layout.

    :param gml_nodes: Set of nodes for the graph.
    :param edge_frequencies: Dictionary mapping node pairs to their frequencies.
    :param output_path: Path to save the output PNG image.
    :param min_edge_frequency: The minimum frequency for an edge to be included.
    """


    G_display = build_display_graph(gml_nodes, edge_frequencies, min_edge_frequency)

    if not G_display:
        print(f"No nodes have any edges with min_edge_frequency={min_edge_frequency}. Cannot generate visualization.")
        save_empty_graph_image(output_path, min_edge_frequency)
        return


    pos = calculate_optimized_layout(G_display)
    fig, ax = plt.subplots(figsize=(30, 30))

    draw_graph_elements(ax, G_display, pos)
    setup_plot_aesthetics(ax, min_edge_frequency)
    fig.tight_layout()

    try:
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Graph saved to {output_path} (min_edge_frequency={min_edge_frequency})")
    except Exception as e:
        print(f"Error saving graph image: {e}")
    finally:
        plt.close(fig)


def visualizer(run_id:int):
    """The main part of the visualizer component"""
    from scripts.load.load_helper import get_minimal_frequences
    db = get_database()
    gml_filepath = GMPL_PATH 
    min_frequency = get_minimal_frequences()

    output_image_file = (
        f"{SAVE_PICTURE_PATH}/python_{db.llm.get_(db.run.get_(run_id=run_id, column='llm_id'), column='name')}{len(db.answer.get_all(run_id=run_id, only_correct=True))}_{run_id}_min{min_frequency}.png"
    )
    if Path(output_image_file).exists():
        print(f"The picture is already exists at: {output_image_file}")
        return
    
    nodes_from_gml = parse_gml_simple(gml_filepath)
    frequencies = count_edge_frequencies(run_id)
    if not frequencies:
        print(f"No edge frequencies were counted from {run_id}")

    visualize_word_graph(nodes_from_gml, frequencies, output_image_file, min_frequency)

