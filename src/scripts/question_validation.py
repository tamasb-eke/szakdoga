import re
import networkx as nx
from pathlib import Path
from scripts.basic_tools import GMPL_PATH, VALID_WORDS_PATH

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
    
    words = word_chain.split('-')
    previous = ''

    for word in words:
        if word == previous:
            return True
        previous = word
    return False


def in_3_letter_scrabble_words(word_chain:str, cache) -> bool:
    """Checks if the word is valid, meaning can be found in the valid 3 letter list from scrabble"""

    words = word_chain.split('-')

    if cache == None:
        with open(VALID_WORDS_PATH, 'r') as file:
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

    if len(data.split('-')) <= 2:
        return "Too short chain length"

    if repeting_words(data):
        return "Repeting words"
    
    if not neighbour_words(data):
        return "Not neighbours"
    
    valid, cache = in_3_letter_scrabble_words(data, cache)
    if not valid:
        return "Not in the acceptable .txt list"
    
    return "True"

#----------------------------- GRAPH SHORTEST PATH FUNCTIONS ---------------------------------------


def find_shortest_word_path(word1:str, word2:str) -> tuple[list, int] | tuple [None, None]:
    """
    Find the shortest path between two 3-letter words in the GML graph.
    """
    G = nx.read_gml(GMPL_PATH, label="name")
    
    if word1 not in G:
        raise ValueError(f"Word '{word1}' not found in the graph.")
    if word2 not in G:
        raise ValueError(f"Word '{word2}' not found in the graph.")
    
    try:
        path = nx.shortest_path(G, source=word1, target=word2)
        return path, len(path)
    except nx.NetworkXNoPath:
        return None, None