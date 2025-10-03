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

def assignment_selector() -> str:
    """
    A user can choose between different tasks. The function returns with the number of the selected item
    """

    choosable_tasks = {'1', '2', '3', '4','e'}

    while True:
        print("\nPlease choose from the tasks below:")
        print("1) Load human responses from study result .json to database")
        print("2) Load earlier played chatbot's conversation result to database")
        print("3) Load manually collected results from .json to database")
        print("4) Play with chatbot")
        print("5) Get results")
        print("e) Exit")
        task = input("Selected task: ")

        if task in choosable_tasks:
            return task
        else:
            print("\nThe given number was not recognisable. Please choose another one.\n")


def main():
    """Just the main function of the code that call's the assignment's function"""
    
    task_functions = {
        '1': study_results_to_db,
        '2': chatbor_results_to_db,
        '3': ...,
        '4': ...,
        '5': ...,
    }
    
    while True:
        task = assignment_selector()
        
        if task == 'e':
            break
        
        task_functions[task]()



if __name__ == '__main__':
    main()

