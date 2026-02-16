import matplotlib.pyplot as plt
import numpy as np
import random
from matplotlib.lines import Line2D
from pathlib import Path
from scripts.basic_tools import SAVE_PICTURE_PATH
from model.schemas import ValidationStatus

COLOR_MAP = {
    ValidationStatus.VALID: '#2ecc71',         
    ValidationStatus.TOO_SHORT: '#e74c3c',  
    ValidationStatus.REPEATING_WORDS: '#f39c12',         
    ValidationStatus.NOT_NEIGHBORS: '#9b59b6',      
    ValidationStatus.INVALID_WORD: "#364cda",
    ValidationStatus.UNKNOWN: '#95a5a6'        
}


def vizualize_game_data(game_data:list[dict], filename:Path='szem_abra.png'):
    """
    Szem ábra kirajzolása és mentése.
    
    Paraméterek:
    game_data (list[dict]): A játékok listája.
    file_name (str): A kimeneti fájl neve (pl. 'eredmeny.png')
    """

    fig, ax = plt.subplots(figsize=(12, 7))
    x_start, x_end = 0, 10
    x = np.linspace(x_start, x_end, 200)
    present_types = set() 
    
    for game in game_data:
        steps = game.get('length', 5)
        val_type = game.get('validation', 'unknown')
        present_types.add(val_type)
        color = COLOR_MAP.get(val_type, COLOR_MAP['unknown'])
        
        base_height = steps * 0.4 
        jitter = random.uniform(-0.2, 0.2)
        h = base_height + jitter
        direction = 1 if random.random() > 0.5 else -1
        h = h * direction
        
        y = h * np.sin(np.pi * (x - x_start) / (x_end - x_start))
        ax.plot(x, y, color=color, alpha=0.5, linewidth=1.2)


    ax.scatter([x_start, x_end], [0, 0], color='#333333', s=150, zorder=10)
    ax.text(x_start - 0.5, 0, "START", fontsize=20, fontweight='bold', ha='right', va='center')
    ax.text(x_end + 0.5, 0, "CÉL", fontsize=20, fontweight='bold', ha='left', va='center')
    ax.axis('off')
    
    legend_elements = []
    for val_type in present_types:
        c = COLOR_MAP.get(val_type, COLOR_MAP['unknown'])
        legend_elements.append(Line2D([0], [0], color=c, lw=2, label=val_type))
    ax.legend(handles=legend_elements, loc='upper right', frameon=False)
    
    plt.title(f"Összesített Eredmények ({len(game_data)} játék)", fontsize=16)
    plt.tight_layout()
    plt.savefig(SAVE_PICTURE_PATH/filename, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"SIKER! Az ábra elmentve ide: {SAVE_PICTURE_PATH/filename}")
