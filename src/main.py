from scripts.load.load_from_json import load_from_initial_json_to_database
from classes.db_manager import get_database

db = get_database()

load_from_initial_json_to_database()









