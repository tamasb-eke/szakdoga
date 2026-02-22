from scripts.basic_tools import GMPL_PATH, VALID_WORDS_PATH
from model.schemas import ValidationStatus
from typing import List, Tuple
import re
import networkx as nx


class Validation:
    def __init__(self):
        self.statuses = ValidationStatus
        self.semantic = SemanticValidation()
        self.syntactic = SyntacticValidation()

    def validate_chain(self, data: str) -> ValidationStatus:
        """
        Main entry point for semantic validation.
        """
        words = [w.lower() for w in data.split('-')]

        if not self.syntactic.matches_pattern(data):
            return ValidationStatus.SYNTAXERROR
        
        if self.syntactic.too_short_chain_length(words):
            return ValidationStatus.TOO_SHORT

        if self.semantic.has_repeating_words(words):
            return ValidationStatus.REPEATING_WORDS

        if not self.semantic.check_neighbor_integrity(words):
            return ValidationStatus.NOT_NEIGHBORS

        if not self.semantic.all_correct_words(words):
            return ValidationStatus.INVALID_WORD

        return ValidationStatus.TRUE


class SyntacticValidation:
    def __init__(self):
        pass

    @staticmethod
    def matches_pattern(data: str) -> bool:
        """Check if string matches format 'abc-def-ghi'."""
        pattern = r'^[a-zA-Z]{3}(?:-[a-zA-Z]{3})*$'
        return bool(re.fullmatch(pattern, data))
    
    @staticmethod
    def too_short_chain_length(words: List[str]):
        """Checks if the solution (chainword) contains more than 2 words"""
        return True if len(words) <= 2 else False


class SemanticValidation:
    def __init__(self):
        self.gmlpath = GMPL_PATH
        self.grapcache = None
        self.wordcache = None
        self.validwordspath = VALID_WORDS_PATH

    def get_valid_words(self)-> set[str]:
        if not self.wordcache:
            try:
                with open(self.validwordspath, 'r') as file:
                    return {line.strip().lower() for line in file}
            except FileNotFoundError:
                print(f"Warning: Could not find word file at {self.validwordspath}")
                return set()
        return self.wordcache
    
    def get_graph(self) -> nx.Graph:
        """
        Loads the NetworkX graph from disk once and caches it.
        """
        if not self.grapcache:
            try:
                return nx.read_gml(GMPL_PATH)
            except Exception as e:
                print(f"Warning: Could not load graph from {GMPL_PATH}. Error: {e}")
                return nx.Graph()
        return self.grapcache
    

    def find_shortest_path(self, word1: str, word2: str) -> Tuple[List[str], int]:
        """
        Return's the shortest path between two nodes from the graph, and it's length
        """
        G = self.get_graph()
        w1, w2 = word1.lower(), word2.lower()

        if w1 not in G or w2 not in G:
            return [], 0
            
        try:
            path = nx.shortest_path(G, source=w1, target=w2)
            return path, len(path)
        except nx.NetworkXNoPath:
            return [], 0

    def all_correct_words(self, words: List[str]) -> bool:
        """
        Checks if all the words in the chain are in the accaptable list
        """
        valid_vocab = self.get_valid_words()
        if not all(word in valid_vocab for word in words):
            return False
        return True


    @staticmethod
    def has_repeating_words(words: List[str]) -> bool:
        """
        Checks for repeating words.
        """
        previous = ''
        for word in words:
            if word == previous:
                return True
            previous = word
        return False
    
    @staticmethod
    def are_words_adjacent(word1: str, word2: str) -> bool:
        """Checks if two words differ by exactly one letter."""
        if len(word1) != len(word2):
            return False
        
        diffs = sum(1 for a, b in zip(word1, word2) if a != b)
        return diffs == 1

    def check_neighbor_integrity(self, words: List[str]) -> bool:
        """Checks if all consecutive words in the list are neighbors."""
        for i in range(len(words) - 1):
            if not self.are_words_adjacent(words[i], words[i+1]):
                return False
        return True
 