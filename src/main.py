from scripts.load.load_from_json import load_from_initial_json_to_database
from classes.db_manager import get_database
from scripts.load_enviroment import AUTHOR
from classes.api import Chatbot

db = get_database()
chatbot = Chatbot()

load_from_initial_json_to_database()









