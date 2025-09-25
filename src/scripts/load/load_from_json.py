import json
from pathlib import Path
from scripts.logger.logger import get_logger
from scripts.safe_operation import safe_operation
from scripts.basic_tools import get_enviromental_variable, ROOT

@safe_operation()
def load_from_initial_json_to_database():
    """
    This function is loading from the research result's 'word_navigation_game_export.json' file
    It is usefull if the database is corrupted or needs a reload
    """

    logger = get_logger(__name__)
    json_path = ROOT/'data/game_guides/word_navigation_game_export.json'
    db_path = get_enviromental_variable('DATABASE_PATH')
    
