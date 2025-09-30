from scripts.load.load_from_json import study_results_to_db, chatbor_results_to_db
from src.scripts.load.load_from_llm_other import llm_messages_loader
from classes.db_manager import get_database
from scripts.load_enviroment import AUTHOR
from classes.api import Chatbot

db = get_database()
chatbot = Chatbot()

study_results_to_db()
chatbor_results_to_db()
llm_messages_loader()
