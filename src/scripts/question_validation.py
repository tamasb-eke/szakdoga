import re
import networkx as nx
from pathlib import Path
from scripts.basic_tools import ROOT

cache = None
#----------------------------- SYNTACTIC VALIDATION FUNCTIONS ---------------------------------------

def pattern_matching(data:str) -> bool:
    """Check if the answer have the correct pattern"""
    pattern = r'^[a-zA-Z]{3}(?:-[a-zA-Z]{3})*$'
    return bool(re.fullmatch(pattern, data))

def lengh_mathing(word_chain:str):
    """Check if the given answer contains only 3 letter long words"""
    words = word_chain.split('-')

    for word in words:
        if len(word) != 3:
            return False
    
    return True

def syntactic_validation(data:str) -> bool:
    """Checks if in a sense of syntactic validation is correct"""
    if not pattern_matching(data):
        return False
    return True


#----------------------------- SEMANTIC VALIDATION FUNCTIONS ---------------------------------------
def repeting_words(word_chain:str) -> bool:
    """
    Checks if a hyphen-separated string contains at least two identical words.
    
    :pamar word_chain (str): A string with words separated by hyphens (e.g., "KIS-KAS-KAM-MAX")
    """
    
    seen = set()
    words = word_chain.split('-')
    
    for word in words:
        if word in seen:
            return True
        seen.add(word)
    return False


def in_3_letter_scrabble_words(word_chain:str, cache) -> bool:
    """Checks if the word is valid, meaning can be found in the valid 3 letter list from scrabble"""

    filename = Path(ROOT/'data/game_guides/valid_three_letter_words.txt')
    words = word_chain.split('-')

    if cache == None:
        with open(filename, 'r') as file:
            cache = [line.strip().lower() for line in file]

    for word in words:
        lower_word = word.lower()
        if not lower_word in cache:
            return False, cache
    return True, cache


def neighbour_words(word_chain:str) -> bool:
    """
    Checks if all consecutive words in a hyphen-separated string are adjacent.
    
    :param word_chain (str): A string with 3-letter words separated by hyphens (e.g., "SOX-SAX-SAY")
    """

    words = word_chain.split('-')
    
    for i in range(len(words) - 1):
        current_word = words[i]
        next_word = words[i + 1]
        
        if not is_adjacent(current_word, next_word):
            return False
    return True

def is_adjacent(word1: str, word2: str) -> bool:
    """
    Checks if two words are adjacent (differ by exactly one letter).
    
    :param word1 (str): First word
    :param word2 (str): Second word
    """

    if len(word1) != len(word2):
        return False
    
    differences = 0
    for i in range(len(word1)):
        if word1[i] != word2[i]:
            differences += 1
        
        if differences > 1:
            return False
    
    return differences == 1

def semantic_validation(data: str) -> str:

    global cache

    if repeting_words(data):
        return "Repeting words"
    
    if not neighbour_words(data):
        return "Not neighbours"
    
    valid, cache = in_3_letter_scrabble_words(data, cache)
    if not valid:
        return "Not in the acceptable .txt list"
    
    return "True"

#----------------------------- GRAPH SHORTEST PATH FUNCTIONS ---------------------------------------

def load_graph_from_gml(gml_path):
    """
    Load a graph from a GML file.
    """
    return nx.read_gml(gml_path, label="name")

def find_shortest_word_path(gml_path, word1, word2):
    """
    Find the shortest path between two 3-letter words in the GML graph.
    """
    G = load_graph_from_gml(gml_path)
    
    if word1 not in G:
        raise ValueError(f"Word '{word1}' not found in the graph.")
    if word2 not in G:
        raise ValueError(f"Word '{word2}' not found in the graph.")
    
    try:
        path = nx.shortest_path(G, source=word1, target=word2)
        return path, len(path)
    except nx.NetworkXNoPath:
        return None  # or raise an exception if you prefer